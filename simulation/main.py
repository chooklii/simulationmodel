import simpy
import random

from simulation.clients.usersession import (
    UserSession,
    getAllSessionsToRequest,
    updateCompletedSession,
    getSessionByID,
)
from simulation.clients.request import HttpRequest
from simulation.clients.userrequest import (
    UserRequest,
    getAllUserRequestsToRequest,
    deleteCompletedRequests,
    getRequestByID,
    updateCompletedRequest,
)
from simulation.monitoring.monitor import (
    monitor_request,
    monitor_response,
    display_averages,
    add_to_datastore,
    plotGraph,
    writeDataToFile,
)
from simulation.helper import checkQueueLength

from simulation.components.handler import (
    allComponents,
    initExternalSystemsMW,
    initExternalSystemsMQ,
)
from simulation.components.externalSystems import (
    getExternalSystemsToWrite,
    checkIfRequestIncludedAnyInitiator,
)

from simulation.validation import validateConfigData

RANDOM_SEED = 42
allSessions = []
externalSystemSessions = []
random.seed(RANDOM_SEED)

# Create Requests for Requests per Secomd
def request_creator(
    env,
    users_per_second,
    thinktime,
    requestOptions,
    externalSystemsMQ,
    externalSystemsMW,
    externalSystemsRQ,
    min_number_of_requests,
    max_number_of_requests,
    multiple_requests_per_user,
    timeoutIntervall,
    databaseReplication,
    ssl
):
    global allSessions
    intervall = 1 / users_per_second
    allSessions = []
    nextRequestTime = 0

    initExternalSystemsRQ(externalSystemsRQ, env, requestOptions)

    while True:
        randomTimeIntervall = random.expovariate(1 / intervall)
        if nextRequestTime < env.now:
            # CREATE REQUEST
            allSessions.append(
                UserRequest(
                    env=env,
                    mean_waiting_time=thinktime,
                    min_number_of_requests=min_number_of_requests,
                    max_number_of_requests=max_number_of_requests,
                    multiple_requests_per_user=multiple_requests_per_user,
                ))
            nextRequestTime = env.now + randomTimeIntervall
        requestsToSend = getAllUserRequestsToRequest(
            sessions=allSessions, env=env, requestOptions=requestOptions)
        allSessions = deleteCompletedRequests(allRequests=allSessions,
                                              env=env,
                                              requestOptions=requestOptions)
        
        # Process External Systems
        processExternalSystems(
            externalSystemsMQ, externalSystemsMW, env, requestOptions)
        processExternalSystemsRQ(externalSystemsRQ, env, requestOptions, databaseReplication)
        if len(requestsToSend) != 0:
            for single in requestsToSend:
                req = HttpRequest(
                    requestOptions=requestOptions,
                    sessionID=single.sessionID,
                    lastRequestTypeID=single.requestTypeID,
                    lastRequestID=single.requestID,
                    sessionLastRequestTime=single.lastRequestEnd,
                )
                single.setRequestID(req.reqid)
                single.setRequestTypeID(req.requestTypeID)
                single.setStatus("w")
                single.addUpNumberOfRequest()
                monitor_request(env, req)

                # Search for the first Component and request it
                firstComponentID = req.getFirstComponentID()
                firstComponent = allComponents.getComponentByID(
                    firstComponentID)
                if checkQueueLength(firstComponent, env, req):
                    env.process(
                        request_requests(
                            env,
                            req,
                            firstComponent,
                            externalSystemsMW,
                            requestOptions,
                            databaseReplication,
                            ssl
                        ))

        else:
            yield env.timeout(timeoutIntervall)


def request_requests(env, req, destination, externalSystemsMW, requestOptions, databaseReplication,ssl):
    global allSessions
    with destination.resource.request() as request:
        yield request
        yield env.process(destination.process(req, ssl=ssl))
        monitor_response(env, req)
        session = getSessionByID(allSessions, req.sessionID)
        updateCompletedSession(session, env)
        session.setLastRequestEndTime(env.now)

    # If Request included any async Write send Write Request to all other databases
    processAsyncDatabaseReplication(env, req, databaseReplication)
    # If Request included any initiator from MW send DB request
    processMiddleware(externalSystemsMW, env, req, requestOptions)


def processAsyncDatabaseReplication(env, req, databaseReplication):
    # check if completed Request has any Replication Logic
    if(req.requestTypeID in databaseReplication.keys()):
        # check if it is async
        if(databaseReplication[req.requestTypeID].asyncReplication):
            # request every component
            for component in databaseReplication[req.requestTypeID].dbs:
                nextComponent = allComponents.getComponentByID(component)
                # If RequestID is within components completedRequest the DB has already written the change
                if not req.reqid in nextComponent.completedRequestIDs:
                    env.process(requestReplicatedComponent(
                        env, nextComponent, req.requestTypeID))


def requestReplicatedComponent(env, component, reqTypeID):
    with component.resource.request(priority=-1) as request:
        yield request
        yield env.process(component.processReplication(reqTypeID))


def request_creator_sessions(env, sessions, thinktime, requestOptions,
                             externalSystemsMQ, externalSystemsMW, externalSystemsRQ, ssl, timeoutIntervall, databaseReplication):
    global allSessions
    allSessions = create_sessions(sessions, env, thinktime)
    initExternalSystemsRQ(externalSystemsRQ, env, requestOptions)
    while True:
        # Check for Sessions to Request
        sessionsToRequest = getAllSessionsToRequest(allSessions, env)
        # Process External Systems
        processExternalSystems(externalSystemsMQ, externalSystemsMW, env,
                               requestOptions)
        # external Systems with own Requests and ThinkTime
        processExternalSystemsRQ(externalSystemsRQ, env, requestOptions, databaseReplication)
        if len(sessionsToRequest) != 0:
            # Go through all Sessions to Request, create a new Request and set them to waiting
            for session in sessionsToRequest:
                req = HttpRequest(
                    requestOptions=requestOptions,
                    sessionID=session.sessionID,
                    lastRequestTypeID=session.requestTypeID,
                )
                session.setReqID(req.reqid)
                session.setRequestTypeID(req.requestTypeID)
                session.setStatus("w")
                monitor_request(env, req)

                # Search for the first Component and request it
                firstComponentID = req.getFirstComponentID()
                firstComponent = allComponents.getComponentByID(
                    firstComponentID)
                if checkQueueLength(firstComponent, env, req):
                    env.process(
                        request_session(
                            env,
                            req,
                            firstComponent,
                            externalSystemsMW,
                            requestOptions,
                            ssl,
                            allSessions,
                            databaseReplication
                        ))
        else:
            yield env.timeout(timeoutIntervall)


def initExternalSystemsRQ(externalSystemsRQ, env, requestOptions):
    global externalSystemSessions
    for externalSystem in externalSystemsRQ:
        newSessions = create_sessions(number=externalSystem.numberclients, env=env,
                                      thinktime=externalSystem.thinktime, requestTypeID=externalSystem.writeRequestID)
        externalSystemSessions += newSessions


def processExternalSystemsRQ(externalSystemsRQ, env, requestOptions, databaseReplication):
    global externalSystemSessions
    sessionsToRequest = getAllSessionsToRequest(externalSystemSessions, env)

    if len(sessionsToRequest) != 0:
        for session in sessionsToRequest:
            req = HttpRequest(
                requestOptions=requestOptions,
                sessionID=session.sessionID,
                lastRequestTypeID=session.requestTypeID,
            )
            session.setReqID(req.reqid)
            session.setRequestTypeID(req.requestTypeID)
            session.setStatus("w")
            monitor_request(env, req)

            # Search for the first Component and request it
            firstComponentID = req.getFirstComponentID()
            firstComponent = allComponents.getComponentByID(
                firstComponentID)
            if checkQueueLength(firstComponent, env, req):
                env.process(
                    request_session(
                        env,
                        req,
                        firstComponent,
                        externalSystemsMW,
                        requestOptions,
                        ssl,
                        externalSystemSessions,
                        databaseReplication
                    ))


def processExternalSystems(externalSystemsMQ, externalSystemsMW, env,
                           requestOptions):
    global monitorExternalSystem
    # Request for both systems
    systemsToRequest = getExternalSystemsToWrite(
        externalSystemsMQ + externalSystemsMW, env)
    if len(systemsToRequest) != 0:
        for system in systemsToRequest:
            system.setNextWriteTime()
            req = HttpRequest(
                requestOptions,
                thisRequestTypeID=system.writeRequestID,
                monitor=monitorExternalSystem,
            )
            # Search for the first Component and request it
            firstComponentID = req.getFirstComponentID()
            firstComponent = allComponents.getComponentByID(firstComponentID)
            if checkQueueLength(firstComponent, env, req):
                monitor_request(env, req)
                env.process(requestExternalSystem(env, req, firstComponent))


def processMiddleware(externalSystemsMW, env, req, requestOptions):
    global monitorExternalSystem
    requestsToInitilize = checkIfRequestIncludedAnyInitiator(
        externalSystemsMW, req)
    for single in requestsToInitilize:
        req = HttpRequest(requestOptions,
                          thisRequestTypeID=single,
                          monitor=monitorExternalSystem)
        firstComponentID = req.getFirstComponentID()
        firstComponent = allComponents.getComponentByID(firstComponentID)
        if checkQueueLength(firstComponent, env, req):
            monitor_request(env, req)
            env.process(requestExternalSystem(env, req, firstComponent))


def requestExternalSystem(env, req, destination):
    global allSessions
    with destination.resource.request() as request:
        yield request
        yield env.process(destination.process(req))
        monitor_response(env, req)


def request_session(env, req, destination, externalSystemsMW, requestOptions,
                    ssl, allSessions, databaseReplication):
    with destination.resource.request() as request:
        yield request
        yield env.process(destination.process(req))
        monitor_response(env, req)
        session = getSessionByID(allSessions, req.sessionID)
        updateCompletedSession(session, env)

    # If Request included any initiator from MW send DB request
    processMiddleware(externalSystemsMW, env, req, requestOptions)
    # If Request included any async Write send Write Request to all other databases
    processAsyncDatabaseReplication(env, req, databaseReplication)


def create_sessions(number, env, thinktime, requestTypeID = None):
    sessions = []
    for key in range(number):
        sessions.append(UserSession(env=env, mean_waiting_time=thinktime, requestTypeID=requestTypeID))
    return sessions


def runSessions(config, simtime, databaseReplication, externalSystemsMQ, externalSystemsMW):
    for key in config.UNIQUE_SESSIONS:
        env = simpy.Environment()
        allComponents.setEnv(env)

        env.process(
            request_creator_sessions(
                env=env,
                sessions=key,
                ssl=config.SSL,
                thinktime=config.THINK_TIME,
                externalSystemsMQ=externalSystemsMQ,
                externalSystemsMW=externalSystemsMW,
                externalSystemsRQ=config.EXTERNALSYSTEMS_RQ,
                requestOptions=config.REQUESTS,
                timeoutIntervall=config.TIMEOUT_INTERVALL,
                databaseReplication=databaseReplication
            ))

        env.run(until=simtime)
        # Display Average Data for this run
        display_averages(key, time=simtime)
        # Reset Datastore in order to create graphs later
        add_to_datastore(key)

def runRequests(config, simtime, databaseReplication, externalSystemsMQ, externalSystemsMW):
    for key in config.REQUESTS_PER_SECOND:
        env = simpy.Environment()
        allComponents.setEnv(env)

        env.process(
            request_creator(
                env=env,
                users_per_second=key,
                thinktime=config.THINK_TIME,
                externalSystemsMQ=externalSystemsMQ,
                externalSystemsMW=externalSystemsMW,
                externalSystemsRQ=config.EXTERNALSYSTEMS_RQ,
                requestOptions=config.REQUESTS,
                min_number_of_requests=config.MIN_NUMBER_OF_REQUESTS,
                max_number_of_requests=config.MAX_NUMBER_OF_REQUESTS,
                multiple_requests_per_user=config.MULTIPLE_REQUESTS_PER_USER,
                timeoutIntervall=config.TIMEOUT_INTERVALL,
                databaseReplication=databaseReplication,
                ssl=config.SSL
            ))
        env.run(until=simtime)
        # Display Average Data for this run
        display_averages(key, time=simtime)
        # Reset Datastore in order to create graphs later
        add_to_datastore(key)


def monitorResults(config, simtime):
    plotGraph(
        time=simtime,
        include_compared_results=config.INCLUDE_COMPARED_RESULTS,
        compared_results=config.COMPARED_RESULTS,
        ylabel=config.Y_LABEL,
        metric_response_time=config.RESPONSE_TIME,
        own_name=config.OWN_NAME,
        xlabel=config.X_LABEL,
        xticks=config.UNIQUE_SESSIONS
        if config.USE_SESSIONS else config.REQUESTS_PER_SECOND,
    )
    writeDataToFile(
        time=simtime,
        include_compared_results=config.INCLUDE_COMPARED_RESULTS,
        requests=config.REQUESTS,
        comparedResults=config.COMPARED_RESULTS,
    )

def main(config):
    env = simpy.Environment()
    monitorExternalSystem = config.MONITOR_EXTERNAL_REQUEST
    ssl = config.SSL
    simtime = config.SIM_TIME
    databaseReplication = config.DATABASE_REPLICATION
    externalSystemsMQ = initExternalSystemsMQ(env)
    externalSystemsMW = initExternalSystemsMW(env)

    # Validate config data
    if not validateConfigData(config):
        quit()

    # Differ between the usage of sessions and the usage of requests/s
    if config.USE_SESSIONS:
        runSessions(config, simtime, databaseReplication, externalSystemsMQ, externalSystemsMW)
    else:
        runRequests(config, simtime, databaseReplication, externalSystemsMQ, externalSystemsMW)
    
    monitorResults(config, simtime)


