class SingleRequestMonitoring(object):

    def __init__(self, requestTypeID):
        self.requestTypeID = requestTypeID
        self.start = None
        self.end = None
        self.extraStart=None
        self.extraEnd=None
        self.responseTime = None
        self.rejected = False
        self.components = {}

    def addComponent(self, name):
        self.components[name] = []

    def setStartTime(self,time):
        self.start = time

    def setExtraStartTime(self, time):
        self.extraStart = time

    def setExtraCompleted(self, time):
        self.extraEnd = time
        self.responseTime = (time - self.extraStart) + self.responseTime

    def setRequestCompleted(self, time):
        self.end = time
        self.responseTime = time - self.start 

    def setRejected(self):
        self.rejected = True

class ComponentMonitoring(object):

    def __init__(self):
        self.start = None
        self.end = None
        self.responseTime = None
        self.rejectedRequest = None
        self.queuedRequest = None
        self.queuedRequestStart = None

    def setQueued(self, time):
        self.queuedRequest = True
        self.queuedRequestStart = time

    def setRejected(self):
        self.rejectedRequest = True

    def setStart(self, time):
        self.start = time

    def setCompleted(self, time):
        self.end = time
        self.responseTime = time - self.start