import itertools
import random

"""
User Request

status:
t -> thinking
w -> waiting
"""
class UserRequest:
    newid = itertools.count()

    def __init__(self, env, mean_waiting_time, min_number_of_requests, max_number_of_requests, multiple_requests_per_user):
        self.env = env
        self.sessionID = next(UserRequest.newid)
        self.status = "t"
        self.requestTypeID = None
        self.waitingTime = None
        self.requestID=None
        self.requestNumber = 0
        self.numberOfRequests = self.calculateNumberOfRequests(min_number_of_requests, max_number_of_requests, multiple_requests_per_user)
        self.lastRequestEnd = None
        self.meanWaitingTime = mean_waiting_time
        self.nextRequestTime = self.calculateNextRequestTime()

    def setStatus(self, status):
        self.status = status

    def setRequestID(self, reqID):
        self.requestID = reqID

    def setRequestTypeID(self, reqTypeID):
        self.requestTypeID = reqTypeID

    def calculateNextRequestTime(self):
        if self.meanWaitingTime > 0:
            self.waitingTime = random.expovariate(1/self.meanWaitingTime)
            return self.env.now + self.waitingTime
        else: 
            return self.env.now
        
    def calculateWaitingTime(self):
        self.waitingTime = self.calculateNextRequestTime()
        self.nextRequestTime = self.env.now + self.waitingTime

    def calculateNumberOfRequests(self, min_number_of_requests, max_number_of_requests, multiple_requests_per_user):
        # if one request sends multiple requests calculate a random number - if not just select 1
        # if the number of requests is reached a request is concluded (and does not return like a session)
        if multiple_requests_per_user:
            return random.randint(min_number_of_requests, max_number_of_requests)
        else: 
            return 1

    def addUpNumberOfRequest(self):
        self.requestNumber+=1
    
    def setLastRequestEndTime(self, time):
        self.lastRequestEnd = time

# Return all Sessions in thinking where there thinking time has expired and where next there is a followup Request
def getAllUserRequestsToRequest(sessions, env, requestOptions):
    return [session for session in sessions if session.status == "t" and session.nextRequestTime < env.now and checkForNextRequestID(session, requestOptions)]

def getAllUserRequestsToDelete(sessions, env, requestOptions):
    return [session for session in sessions if session.status == "t" and not checkForNextRequestID(session, requestOptions)]

def deleteCompletedRequests(allRequests, env, requestOptions):
    requestsToDelete = getAllUserRequestsToDelete(allRequests, env, requestOptions)
    return [item for item in allRequests if item not in requestsToDelete]

def checkForNextRequestID(session, requestOptions):
    if session.requestTypeID is None:
        # It is a new session
        return True
    nextRequestOptions = [value for value in requestOptions if value.id == session.requestTypeID].pop()
    if len(nextRequestOptions.nextRequest) > 0:
        # It has a followup Request
        return True
    else: 
        if session.numberOfRequests > session.requestNumber:
            # Total number of Requests per Request not reached - keep it
            return True
        else:
            # It has no followup Request - Can be deleted
            return False

# Update Session after Request is completed
def updateCompletedRequest(session, env):
    session.calculateWaitingTime()
    session.setStatus("t")

# Return single Session based on its ID
def getRequestByID(sessions, sessionID):
    return [session for session in sessions if session.sessionID == sessionID][0]