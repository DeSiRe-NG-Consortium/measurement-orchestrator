from flask import Flask, json, request
import requests
import os
from datetime import datetime
import socket
from Association import Association
from MeasurementPoint import MeasurementPoint


api = Flask(__name__)

assoc_list = []
measurementPointList = []
middleware_ip = ""
saveMeasurementsToFileAfter = 3 # if more than this number of measurement points are in the queue, save them to a file
resultCacheUsedFlag = False

# Find out own IP address
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.settimeout(0)
try:
  # random private IP address in next line does not have any deeper meaning
  s.connect(('10.254.254.254', 1))
  IP = s.getsockname()[0]
except Exception:
  IP = '127.0.0.1'
finally:
  s.close()
  myIp = IP



# Instruct the Measurement Client in association 'assoc' to start the measurements to Endpoint with ip endpointIp.
def startMeasurementsOnClient(assoc):
  global myIp
  print("startMeasurementsOnClient() for assoc: " + str(assoc))
  clientPath = "http://" + assoc.mcIp + ":5010/startMeasurements"
  res = requests.post(clientPath, json={"meIP" : assoc.meIp, "measurementNetworkNamespace" : "5gns", "udpSpeed" : str(assoc.targetDatarate), "mPay" : "no", "orchestratorIp": myIp, "technology" : assoc.technology, "mode": assoc.mode})
  return res.status_code


# Instruct the Measurement Client in association 'assoc' to stop the measurements.
def stopMeasurementsOnClient(assoc):
  print("stopMeasurementsOnClient() for assoc: " + str(assoc))
  clientPath = "http://" + assoc.mcIp + ":5010/stopMeasurements"
  res = requests.post(clientPath)
  return res.status_code

# Send data to the Middleware.
# If a connection is not possible (due to, e.g., a loss of the OOB connection or standalone operation), data is buffered in a local cache.
def sendDataToMiddleware():
  global resultCacheUsedFlag
  global measurementPointList
  json_data=[]
  recentlyImported = False
  for measurementResult in measurementPointList:
    json_data.append(measurementResult.to_dict())
  middlewarePath = "http://" + middleware_ip + ":5010/measurements"
  json_obj = json.dumps(json_data)
  try:
    res = requests.post(middlewarePath, json=json_obj)
    if res.status_code == 201:
      measurementPointList.clear()
      importCachedMeasurementPoints()
      recentlyImported = True
    else:
      print("Error sending data to middleware - middleware sent response code " + str(res.status_code))
  except:
    print("Error sending data to middleware - other exception")
  # Save data to file (local cache)
  if len(measurementPointList) > saveMeasurementsToFileAfter and not recentlyImported: # only export when not imported to prevent loop
    exportMeasurementPointsToCache()


def importCachedMeasurementPoints():
  global resultCacheUsedFlag
  global measurementPointList
  if resultCacheUsedFlag: # If there is cached data, send it now that the middleware is responsive again
    print("Reading cached data")
    text_file = open("cache.json", "r")
    fromCacheString = "[" + text_file.read()[:-1] + "]" # add list symbols at beginning and end
    fromCacheLoadedJson = json.loads(fromCacheString)
    for row in fromCacheLoadedJson:
      cachedMeasurementPoint = MeasurementPoint(mcId = row["mcId"],
                                                mcMac = row["mcMac"],
                                                meId = row["meId"],
                                                # timestamp = datetime.strptime(row["timestamp"][1:-1], '%Y-%m-%d %H:%M:%S.%f'),
                                                timestamp = row["timestamp"],

                                                datarate = float(row["datarate"]),
                                                latency = float(row["latency"]),
                                                technology = row["technology"],
                                                targetDatarate = float(row["targetDatarate"]),
                                                mode = row["mode"])
      measurementPointList.append(cachedMeasurementPoint)
    resultCacheUsedFlag = False
    os.remove("cache.json") # Remove cache file
    print("Imported " + str(len(fromCacheLoadedJson)) + " measurement points from cache.")
    return True
  return False



def exportMeasurementPointsToCache():
    global resultCacheUsedFlag
    global measurementPointList
    text_file = open("cache.json", "a")
    for measurementResult in measurementPointList:
      text_file.write(json.dumps(measurementResult.to_dict()) + ",")
    text_file.close()
    writtenMeasurementPoints = len(measurementPointList)
    measurementPointList.clear()
    resultCacheUsedFlag = True
    print("Wrote " + str(writtenMeasurementPoints) + " measurement points to cache.json")



def readConfigFile():
  configFile="./mo_config.json"
  jsonConfigFile=open(configFile)
  jsonConfigFileData=json.load(jsonConfigFile)

  for row in jsonConfigFileData["associations"]:
    mcId = row["mcId"]
    mcIp = row["mcIp"]
    mcMac = row["mcMac"]
    meId = row["meId"]
    meIp = row["meIp"]
    state = "DISABLED" # start with disabled measurements always
    try:
      technology = row["technology"]
    except:
      technology = "5G"
    try:
      targetDatarate = row["targetDatarate"]
    except:
      targetDatarate = 25
    try:
      mode = row["mode"]
    except:
      mode = "DEFAULT"

    curAssoc = Association(mcId, mcIp, mcMac, meId, meIp, state, technology, targetDatarate, mode)
    print("Association read from config file ./mo_config.json: " + str(curAssoc))
    assoc_list.append(curAssoc)


# Starts/ stops certain measurements, which need to be specified in the JSON in this call.
# Called by Middleware when starting/ stopping a measurement
@api.route('/setMeasurementStates', methods=['post'])
def setMeasurements():
  global middleware_ip
  content=json.loads(request.json)
  state = content["state"]
  try:
    middleware_ip = content["middlewareIp"]
  except:
    print("Info: No middleware IP specified")

  for config in content["configs"]:
    mcId = config['mcId']
    meId = config['meId']

    # find association
    assocFound = False
    targetAssoc = -1
    for assoc in assoc_list:
      if not assocFound and assoc.mcId == mcId and assoc.meId == meId:
        targetAssoc = assoc
        assocFound = True
    if not assocFound:
      print("ERROR: Could not find association with mcId = " + mcId + " and meId = " + meId + "!")
      return json.dumps({"success": False}), 404

    if state == targetAssoc.state:
      print("ERROR: Target state does not differ for MC with id = "
        + mcId + " (current state: " + targetAssoc.state + "; target state: " + state + ") - aborting...")
      return json.dumps({"success": False}), 400

    else:
      targetAssoc.state = state
      measurementClientState = 400 #default
      if state == "DISABLED":
        measurementClientState = stopMeasurementsOnClient(targetAssoc)
      elif state == "ENABLED":
        measurementClientState = startMeasurementsOnClient(targetAssoc)
      else:
        print("ERROR: Unknown target state: " + state)
        return json.dumps({"success": False}), 400
      if measurementClientState != 200:
        print("Error while setting association " + str(targetAssoc) + " to state " + state + ": Received response code " + str(measurementClientState))
        return json.dumps({"success": False}), measurementClientState
  return json.dumps({"success": True}), 200


# Get or post measurement results
# Called by MC periodically
@api.route('/measurements', methods=['get', 'post'])
def measurements():
  if request.method == 'GET':
    json_data=[]
    for measurementResult in measurementPointList:
      json_data.append(measurementResult.to_dict())
    measurementPointList.clear()
    return json.dumps(json_data)

  elif request.method == 'POST': # MC sends measurement data
    # find MC id from MAC
    content=request.json
    try:
      mcMac=content[0]["mcMac"]
    except:
      print("Error: Invalid JSON received: " + str(content))
      return json.dumps({"success": False}), 400

    assocFound = False
    for assoc in assoc_list:
      if assoc.mcMac == mcMac and assoc.state == "ENABLED":
        assocFound = True
        for row in content: # for every measurement, add a MeasurementPoint
          newMeasurementPoint = MeasurementPoint(assoc.mcId, assoc.mcMac, assoc.meId, row["timestamp"], row["datarate"], row["latency"], assoc.technology, assoc.targetDatarate, assoc.mode)
          measurementPointList.append(newMeasurementPoint)
          print("Added a row to the measurement point list: " + str(newMeasurementPoint) + ". Length of measurementPointList is " + str(len(measurementPointList)))

    if not assocFound:
      print("Error: No association found for MAC: " + mcMac)
      return json.dumps({"success": False}), 404
    sendDataToMiddleware() # send to middleware
    return json.dumps({"success": True}), 201


# Receive runtime information from entities
@api.route('/log', methods=['post'])
def log():
  content=json.loads(request.json)
  logSender = content["sender"]
  logType = content["type"]
  logMessage = content["message"]
  print(str(datetime.now().isoformat()) + " --- " + logSender + ": " + logType + " - " + logMessage)
  return json.dumps({"success": True}), 200

if __name__ == '__main__':
    # Initialize
    readConfigFile()
    api.run(host="0.0.0.0", port="5010")
