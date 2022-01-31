import random
import itertools
#Single HTTP Request


class HttpRequest:
    newid = itertools.count()

    def __init__(
        self, 
        requestOptions, 
        monitor=True,
        sessionID = None,
        sessionLastRequestTime = None,
        lastRequestID = None,
        lastRequestTypeID = None,
        thisRequestTypeID = None):
        # used to create a unique requestID
        self.reqid = next(HttpRequest.newid)
        self.monitor = monitor
        self.lastRequestID = lastRequestID
        self.sameRequest = False
        self.requestTypeID = self.determin_req_type(requestOptions, lastRequestTypeID, thisRequestTypeID)
        # If Request is not monitored
        checkIfMonitoringActive = [value for value in requestOptions if value.id == self.requestTypeID and value.monitorRequest]
        if len(checkIfMonitoringActive) == 0:
            self.monitor = False
        # Information regarding the path the the current Destination within the path of the request
        self.path = self.setPathForID(requestOptions)
        self.currentDestination = 0
        self.sessionID = sessionID
        self.sessionLastRequestTime = sessionLastRequestTime

    def setSessionLastRequestTime(self, time):
        self.sessionLastRequestTime = time

    def increaseCurrentDestination(self):
        self.currentDestination = self.currentDestination +1

    def determin_req_type(self, requestOptions, lastrequestTypeID, thisRequestTypeID):
        # if a RequestTypeID for this is given use it
        if not thisRequestTypeID is None:
            return thisRequestTypeID
        # Check if there was a last request
        if lastrequestTypeID is None:
            options, probabilities = self.settup_lists(requestOptions)
        else:
            # if so, check if the last request has values for the next request - if so use them
            nextRequestOptions = [value for value in requestOptions if value.id == lastrequestTypeID].pop()
            if len(nextRequestOptions.nextRequest) > 0:
                # If Parameter Same Request is set - calculate Average Response Time for both requests as the same
                if nextRequestOptions.sameRequest:
                    self.reqid = self.lastRequestID
                    self.sameRequest = True
                options, probabilities = self.settup_lists_next_Request_Options(nextRequestOptions.nextRequest)
            else: 
                options, probabilities = self.settup_lists(requestOptions)

        return next(iter(random.choices(
            population=options,
            weights=probabilities
        )), None)

    # used to create two lists - one containing all options and the opter containing their probabilities 
    def settup_lists(self,requestOptions):
        options = []
        probabilities = []
        for singleOption in requestOptions:
            options.append(singleOption.id)
            probabilities.append(singleOption.probability)
        return options, probabilities


    def settup_lists_next_Request_Options(self,requestOptions):
        options = []
        probabilities = []
        for singleOption in requestOptions:
            options.append(singleOption["id"])
            probabilities.append(singleOption["probability"])
        return options, probabilities

    def setPathForID(self, requestOptions):
        for single in requestOptions:
            if(single.id == self.requestTypeID):
                return single.path

    def getFirstComponentID(self):
        for key, value in self.path.items():
            # Check for next Step
            if(self.currentDestination == key):
                if(len(value) != 1):
                    raise AttributeError("First Component needs to be exactly one - not multiple")
                else: 
                    return next(iter(value[0]["componentIDs"]))


    def getNextComponentID(self):
        self.increaseCurrentDestination()
        for key, value in self.path.items():
            # Check for next Step
            if(self.currentDestination == key):
                return value


    def checkForNextComponent(self):
        for key, value in self.path.items():
            # Check if there is a next Component
            if(self.currentDestination +1 == key):
                return True
        return False

    
    def selectNextPath(self):   
        options = [value for key, value in self.path.items() if key == self.currentDestination].pop()

        option_ids = []
        option_propabilities = []
        for single in options:
            option_ids.append(single["componentIDs"])
            option_propabilities.append(single.probability)
        return next(iter(random.choices(
            population=option_ids,
            weights=option_propabilities
        )), None)