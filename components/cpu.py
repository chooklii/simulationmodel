import simpy

class CPU(object):

    def __init__(self, env, amount, noise, maxuser=0,multipleRequestsCPU=False, multithreading=False, multithreadingParallelism=0):
        self.env = env
        self.amount = amount
        self.noise = noise
        self.multithreading=multithreading
        self.multithreadingParallelism = multithreadingParallelism
        self.multipleRequestsCPU = multipleRequestsCPU
        if(multithreading):
            self.resource = simpy.Resource(env, capacity=1)
        elif(multipleRequestsCPU):
            self.resource = simpy.Resource(env, capacity=maxuser)
        else: 
            self.resource = simpy.Resource(env, capacity=amount)
        # Capture processingTime to insert noise
        # After every 1 - Noise processed Time the Noise is inserted
        self.processedTime = 0

    def processMultithreading(self, processingTime):
        speedup = 1 / (self.multithreadingParallelism+((1-self.multithreadingParallelism)/self.amount)) 
        yield self.env.timeout(processingTime/speedup)

    def processMultipleRequests(self, processingTime):
        requiredProcessingTime = processingTime * self.resource.count
        yield self.env.timeout(requiredProcessingTime)

    def process(self, processingTime):
        # CPU Noise
        if(self.processedTime >= 1 - self.noise):
            yield self.env.process(self.processNoise())
        self.processedTime += processingTime

        if self.multithreading:
            yield self.env.process(self.processMultithreading(processingTime))
        elif self.multipleRequestsCPU:
            yield self.env.process(self.processMultipleRequests(processingTime))
        else: 
            yield self.env.timeout(processingTime)

    def processNoise(self):
        self.processedTime = 0
        yield self.env.timeout(self.noise)