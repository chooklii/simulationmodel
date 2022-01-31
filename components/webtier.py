import simpy
import random

from components.cpu import CPU
from monitoring.monitor import monitorStart, monitorCompletion
from helper import checkQueueLength


class WebTier(object):

    def __init__(
            self,
            env,
            serverid,
            maxuser,
            processingTime,
            queueLength,
            cpus,
            weight,
            cpuNoise,
            sslTimeout,
            fullSSLConnectionTime,
            reuseSSLConnectionTime):
        self.env = env
        self.weight = weight,
        self.queueLength = queueLength
        self.serverid = serverid
        self.cpus = cpus
        self.cpuNoise = cpuNoise
        self.processingTime = processingTime
        self.resource = simpy.Resource(env, capacity=maxuser)
        self.cpu = CPU(env, amount=cpus, noise=cpuNoise)
        self.sslTimeout = sslTimeout
        self.fullSSLConnectionTime = fullSSLConnectionTime
        self.reuseSSLConnectionTime = reuseSSLConnectionTime

    def process(self, req, ssl=False):
        ownSteps = self.getOwnStepsID(req)
        if ssl:
            # if this is the first component and needs to process SSL stuff
            yield self.env.process(self.processSSL(req))
        if req.checkForNextComponent():
            yield self.env.process(self.requestNextComponent(req))
        monitorStart(self.env, req, self.serverid)
        for step in ownSteps:
            yield self.env.process(self.requestCPU(step))
        monitorCompletion(self.env, req, self.serverid)

    def getOwnStepsID(self, req):
        destinationID = req.currentDestination
        return req.path[destinationID]

    def requestCPU(self, step):
        with self.cpu.resource.request() as request:
            yield request
            yield self.env.process(self.cpu.process(self.processingTime[step["step-id"]]))

    def requestNextComponent(self, req):
        nextComponents = self.selectNextComponent(req)
        for nextComponent in nextComponents:
            if checkQueueLength(nextComponent, self.env, req):
                with nextComponent.resource.request() as request:
                    yield request
                    yield self.env.process(nextComponent.process(req))

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
                raise AttributeError("WebTier cannot Load Balance")
            else:
                listOfNextComponents.append(
                    allComponents.getComponentByID(next(iter(componentIDs))))
        return listOfNextComponents
