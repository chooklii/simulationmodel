import simpy
import random
from simulation.helper import checkQueueLength
from simulation.monitoring.monitor import monitorStart, monitorCompletion
from simulation.components.cpu import CPU

class LoadBalancer(object):

    def __init__(
        self,
        serverid,
        env,
        maxuser,
        processingTime,
        algoritm,
        sslTimeout,
        fullSSLConnectionTime,
        reuseSSLConnectionTime,
        cpus,
        useCPU,
        cpuNoise,
        multipleRequestsCPU,
        multithreading,
        multithreadingParallelism
    ):
        self.env = env
        self.serverid = serverid
        self.algoritm = algoritm
        self.processingTime = processingTime
        self.maxuser = maxuser
        self.useCPU = useCPU
        self.cpu = CPU(
            env=env, 
            amount=cpus, 
            noise=cpuNoise, 
            maxuser=maxuser,
            multipleRequestsCPU=multipleRequestsCPU,
            multithreading=multithreading, 
            multithreadingParallelism=multithreadingParallelism)

        # Used for RR and WRR
        # first value is last server and second is amount if redirects to this server
        # which is required for WRR
        self.lastRedirectServer = 0
        self.lastRedirectAmount = 0
        self.resource = simpy.Resource(env, maxuser)

        # SSL Stuff
        self.fullSSLConnectionTime = fullSSLConnectionTime
        self.reuseSSLConnectionTime = reuseSSLConnectionTime
        self.sslTimeout = sslTimeout

    def process(self, req, index=None, ssl=False):
        if ssl:
            # if this is the first component and needs to process SSL stuff
            yield self.env.process(self.processSSL(req))
        
        monitorStart(self.env, req, self.serverid)
        if self.useCPU:
            yield self.env.process(self.requestCPU(self.processingTime[req.requestTypeID]))
        else: 
            yield self.env.timeout(self.processingTime[req.requestTypeID])
        monitorCompletion(self.env, req, self.serverid)
        

        selectedServer = self.selectServer(req)
        if(checkQueueLength(selectedServer, self.env, req)):
            with selectedServer.resource.request() as request:
                yield request
                yield self.env.process(selectedServer.process(req))

    def requestCPU(self, time):
        with self.cpu.resource.request() as request:
            yield request
            yield self.env.process(self.cpu.process(time))

    def processSSL(self, req):
        lastRequestTime = req.sessionLastRequestTime
        if(lastRequestTime is None or self.env.now > lastRequestTime + self.sslTimeout):
            yield self.env.process(self.requestCPU(self.fullSSLConnectionTime))
        else:
            yield self.env.process(self.requestCPU(self.reuseSSLConnectionTime))

    def selectServer(self, req):
        nextComponentOptions = self.selectNextComponent(req)

        if(self.algoritm == "RR"):
            return self.roundRobin(nextComponentOptions)
        if(self.algoritm == "WRR"):
            return self.weightedRoundRobin(nextComponentOptions)
        if(self.algoritm == "LL"):
            return self.leastLoaded(nextComponentOptions)
        if(self.algoritm == "WLL"):
            return self.weightedLeastLoaded(nextComponentOptions)
        if(self.algoritm == "R"):
            return self.random(nextComponentOptions)

    def roundRobin(self, nextComponents):
        if(self.lastRedirectServer + 1 < len(nextComponents)):
            self.lastRedirectServer +=1
        else:
            self.lastRedirectServer = 0
        return nextComponents[self.lastRedirectServer]

    def weightedRoundRobin(self, nextComponents):
        nextComponentByID = nextComponents[self.lastRedirectServer]
        # check if weight is completed
        if(nextComponentByID.weight > self.lastRedirectAmount +1):
            # if not redirect to this server
            self.lastRedirectAmount +=1
            return nextComponentByID
        else:
            self.lastRedirectAmount = 0
        return self.roundRobin(nextComponents)
        

    def weightedLeastLoaded(self, nextComponents):
        # Requests are asigned to the server with the lowest requests / weight ratio
        serverWithLowestRequestWeightRatio = sorted(
            nextComponents, key=lambda d: d.resource.count / d.weight)
        lowestLoadedServer = next(iter(serverWithLowestRequestWeightRatio))
        lowestLoad = lowestLoadedServer.resource.count / lowestLoadedServer.weight
        # check if other components have equal load
        componentsWithThisLoad = [
            component for component in serverWithLowestRequestWeightRatio if component.resource.count / component.weight == lowestLoad]
        if len(componentsWithThisLoad) == 1:
            return lowestLoadedServer
        else:
            # if weight is equal select a server with smallest Queue
            return self.selectServerWithSmallestQueue(componentsWithThisLoad)

    def random(self, nextComponents):
        # Random Load Balancing
        randomPositionIndex = random.randrange(len(nextComponents))
        return nextComponents[randomPositionIndex]

    def leastLoaded(self, nextComponents):
        componentsOrderdByLoad = sorted(
            nextComponents, key=lambda d: d.resource.count)
        lowestLoad = next(iter(componentsOrderdByLoad)).resource.count
        componentsWithThisLoad = [
            component for component in componentsOrderdByLoad if component.resource.count == lowestLoad]
        # If only one component has this load return this
        if len(componentsWithThisLoad) == 1:
            return componentsWithThisLoad[0]
        else:
            return self.selectServerWithSmallestQueue(componentsWithThisLoad)

    def selectServerWithSmallestQueue(self, componentOptions):
        # return the server with the smallest Queue or if multiple are equal select a random one
        orderedComponentsWithEqualLoad = sorted(
            componentOptions, key=lambda d: len(d.resource.queue))
        smallestQueueLength = len(
            next(iter(orderedComponentsWithEqualLoad)).resource.queue)
        componentsWithEqualQueueLength = [component for component in orderedComponentsWithEqualLoad if len(
            component.resource.queue) == smallestQueueLength]
        # if there is only one component with the lowest queue Length
        if len(componentsWithEqualQueueLength) == 1:
            return componentsWithEqualQueueLength[0]
        else:
            # if the queue Length is equal as well select a random component
            randomPositionIndex = random.randrange(
                len(componentsWithEqualQueueLength))
            return componentsWithEqualQueueLength[randomPositionIndex]

    def getOwnStepsID(self, req):
        destinationID = req.currentDestination
        return req.path[destinationID]

    def selectNextComponent(self, req):
        from simulation.components.handler import allComponents
        nextComponent = req.getNextComponentID()
        listOfNextComponents = []

        # Create List of Next Components to Request
        for single in nextComponent:
            componentIDs = single["componentIDs"]
            for component in componentIDs:
                listOfNextComponents.append(
                    allComponents.getComponentByID(component))
        return listOfNextComponents
