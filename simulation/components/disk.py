import simpy

class Disk(object):

    def __init__(self, env):
        self.env = env
        self.resource = simpy.Resource(env, capacity=1)

    def process(self, processingtime):
        yield self.env.timeout(processingtime)
