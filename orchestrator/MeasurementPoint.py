# Stores one Measurement Point, which is a single measurement.
class MeasurementPoint:
  def __init__(self, mcId, mcMac, meId, timestamp, datarate, latency, technology="5G", targetDatarate=25, mode="DEFAULT"):
    self.mcId = mcId
    self.mcMac = mcMac
    self.meId = meId
    self.timestamp = timestamp
    self.datarate = datarate
    self.latency = latency
    self.technology = technology
    self.targetDatarate = targetDatarate
    self.mode = mode

  def __str__(self):
      return ("mcId: " + self.mcId
  + "; mcMac: " + self.mcMac
  + "; meId: " + self.meId
  + "; timestamp: " + str(self.timestamp)
  + "; datarate: " + str(self.datarate)
  + "; latency: " + str(self.latency)
  + "; technology: " + self.technology
  + "; targetDatarate: " + str(self.targetDatarate)
  + "; mode is " + self.mode)

  def to_dict(self):
      return dict(mcId = self.mcId,
                  mcMac = self.mcMac,
                  meId = self.meId,
                  timestamp = self.timestamp,
                  datarate = self.datarate,
                  latency = self.latency,
                  technology = self.technology,
                  targetDatarate = self.targetDatarate,
                  mode = self.mode)
