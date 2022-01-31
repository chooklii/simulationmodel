import itertools
import random

"""
User Session

status:
t -> thinking
w -> waiting
"""
class UserSession:
    newid = itertools.count()

    def __init__(self, env, mean_waiting_time, requestTypeID = None):
        self.env = env
        self.sessionID = next(UserSession.newid)
        self.status = "t"
        self.reqID = None
        self.requestTypeID = requestTypeID
        self.waitingTime = None
        self.lastRequestEnd = None
        self.meanWaitingTime = mean_waiting_time
        self.nextRequestTime = self.calculateNextRequestTime()

    def setStatus(self, status):
        self.status = status

    def setRequestTypeID(self, reqTypeID):
        self.requestTypeID = reqTypeID

    def setReqID(self, reqID):
        self.reqID = reqID

    def calculateNextRequestTime(self):
        self.waitingTime = random.expovariate(1/self.meanWaitingTime)
        return self.env.now + self.waitingTime
        
    def calculateWaitingTime(self):
        #if self.requestTypeID == 9:
        #    self.waitingTime = random.expovariate(1/7)
        #else:
        self.waitingTime = random.expovariate(1/self.meanWaitingTime)
        self.nextRequestTime = self.env.now + self.waitingTime
        self.lastRequestEnd = self.env.now


# Return all Sessions in thinking where there thinking time has expired
def getAllSessionsToRequest(sessions, env):
    return [session for session in sessions if session.status == "t" and session.nextRequestTime < env.now]

# Update Session after Request is completed
def updateCompletedSession(session, env):
    session.calculateWaitingTime()
    session.setStatus("t")

# Return single Session based on its ID
def getSessionByID(sessions, sessionID):
    return [session for session in sessions if session.sessionID == sessionID][0]