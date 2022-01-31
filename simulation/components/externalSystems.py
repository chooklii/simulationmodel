import random


class ExternalSystem(object):


    def __init__(
        self,
        env,
        serverid,
        writeFrequency,
        writeRequestID,
        readRequests):
        self.env = env
        self.serverid = serverid
        self.writeFrequency=writeFrequency
        self.writeRequestID = writeRequestID
        self.lastWrite=0
        self.readRequests=readRequests
        self.nextWrite=self.determinNextWrite()

    def determinNextWrite(self):
        delay = random.expovariate(1/self.writeFrequency)
        return self.env.now + delay

    def setNextWriteTime(self):
        self.nextWrite = self.determinNextWrite()

def getExternalSystemsToWrite(systems, env):
    return [system for system in systems if system.nextWrite < env.now]

def getStepIDs(req):
    stepsids = []
    for key, value in req.path.items():
        for single in value:
            stepsids.append(single["step-id"])
    return stepsids

def checkIfRequestIncludedAnyInitiator(systems, req):
    # check if the completed request contained a initiater 
    stepIds = getStepIDs(req)
    requestsToInitialize = []

    for single in systems:
        for singleInitiator in single.readRequests:
            if(singleInitiator["initiator"] in stepIds):
                requestsToInitialize.append(singleInitiator["readRequestID"])
    return requestsToInitialize