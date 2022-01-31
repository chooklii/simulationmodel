import simpy
import random
from monitoring.monitor import monitorStart, monitorCompletion

from components.cpu import CPU
from helper import checkQueueLength

#Single Instance of Application Server
class ApplicationServer(object):

    def __init__(
        self, 
        env, 
        serverid, 
        maxuser, 
        processingTime, 
        resourceSharing, 
        cpus,
        weight,
        multipleRequestsCPU,
        multithreading,
        multithreadingParallelism,
        cpuNoise,
        queueLength,
        sslTimeout,
        fullSSLConnectionTime,
        reuseSSLConnectionTime,
        ):
        self.env = env
        self.weight = weight
        self.serverid = serverid
        self.resource = simpy.Resource(env, capacity=maxuser)
        self.cpu = CPU(
            env=env, 
            amount=cpus, 
            noise=cpuNoise, 
            maxuser=maxuser,
            multipleRequestsCPU=multipleRequestsCPU,
            multithreading=multithreading, 
            multithreadingParallelism=multithreadingParallelism)
        self.cpus = cpus,
        self.cpuNoise = cpuNoise,
        # Number of current Requests on the application server
        self.currentRequests = 0
        self.queueLength = queueLength
        self.resourceSharing = resourceSharing
        self.processingTime = processingTime

        # SSL Stuff
        self.fullSSLConnectionTime = fullSSLConnectionTime
        self.reuseSSLConnectionTime = reuseSSLConnectionTime
        self.sslTimeout = sslTimeout

    def process(self, req, index=None, ssl=False):
        self.currentRequests += 1
        if ssl:
            # if this is the first component and needs to process SSL stuff
            yield self.env.process(self.processSSL(req))
        ownSteps = self.getOwnStepsID(req)
        if req.checkForNextComponent():
            yield self.env.process(self.requestNextComponent(req))
        monitorStart(self.env, req, self.serverid)
        for step in ownSteps:
            time = self.processingTime[step["step-id"]]
            yield self.env.process(self.requestCPU(time))
        self.currentRequests -= 1
        monitorCompletion(self.env, req, self.serverid)

    def requestCPU(self, time):
        with self.cpu.resource.request() as request:
            yield request
            yield self.env.process(self.cpu.process(time))

    def requestNextComponent(self, req):
        nextComponents = self.selectNextComponent(req)
        for index in range(len(nextComponents)):
            nextComponent=nextComponents[index]
            if checkQueueLength(nextComponent, self.env,req):
                with nextComponent.resource.request() as request:
                    yield request
                    yield self.env.process(nextComponent.process(req, index))

    def getOwnStepsID(self, req):
        destinationID = req.currentDestination
        return req.path[destinationID]

    def processSSL(self, req):
        lastRequestTime = req.sessionLastRequestTime
        if(lastRequestTime is None or self.env.now > lastRequestTime + self.sslTimeout):
            yield self.env.process(self.requestCPU(self.fullSSLConnectionTime))
        else:
            yield self.env.process(self.requestCPU(self.reuseSSLConnectionTime))


    def selectNextComponent(self, req):
        from components.handler import allComponents
        nextComponent = req.getNextComponentID()
        listOfNextComponents = []

        # Create List of Next Components to Request
        for single in nextComponent:
            componentIDs = single["componentIDs"]
            if(len(componentIDs) > 1):
                raise AttributeError("Application Server cannot Load Balance")
            else:
                listOfNextComponents.append(
                    allComponents.getComponentByID(next(iter(componentIDs))))
        return listOfNextComponents
