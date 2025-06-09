# Stores an association of a Measurement Client to a Measurement Endpoint.
class Association:
  def __init__(self, mcId, mcIp, mcMac, meId, meIp, state="DISABLED", technology="5G", targetDatarate=25, mode="DEFAULT"):
    self.mcId = mcId
    self.mcIp = mcIp
    self.mcMac = mcMac
    self.meId = meId
    self.meIp = meIp
    self.state = state
    self.technology = technology
    self.targetDatarate = targetDatarate
    self.mode = mode
  def __str__(self):
      return ("mcId: " + self.mcId
  + "; mcIp: " + self.mcIp
  + "; mcMac: " + self.mcMac
  + "; meId: " + self.meId
  + "; meIp:" + self.meIp
  + "; technology: " + self.technology
  + "; targetDatarate: " + str(self.targetDatarate)
  + "; state is " + self.state
  + "; mode is " + self.mode)
