import simpy
import random
from simulation.monitoring.monitor import monitorStart, monitorCompletion
from simulation.components.disk import Disk
from simulation.components.cpu import CPU

#Single Instance of Database
class Database(object):

    def __init__(
        self, 
        env, 
        serverid,
        maxuser, 
        processingTime,
        useDisk,
        cpuNoise,
        weight,
        queueLength,
        cpus,
        master,
        databaseReplication,
        ):
        self.env = env
        self.weight = weight
        self.serverid = serverid
        self.cpus = cpus
        self.cpu = CPU(env=env, amount=cpus, noise=cpuNoise)
        self.disk = Disk(env=env)
        self.useDisk = useDisk
        self.processingTime=processingTime
        self.resource = simpy.PriorityResource(env, maxuser)
        self.queueLength = queueLength
        self.master = master
        self.databaseReplication=databaseReplication
        # save all own completed RequestIDs for replication
        self.completedRequestIDs = []
        
    def process(self, req, index=None):
        monitorStart(self.env, req, self.serverid)
        if not index == None:
            stepID = req.path[req.currentDestination][index]["step-id"]
        else: 
            stepID = req.path[req.currentDestination][0]["step-id"]

        processingTimeCPU_read = self.processingTime[stepID]["cpu"]["read"]
        processingTimeCPU_write = self.processingTime[stepID]["cpu"]["write"]
        processingTimeDisk_read = self.processingTime[stepID]["disk"]["read"]
        processingTimeDisk_write = self.processingTime[stepID]["disk"]["write"]

        if(processingTimeDisk_read > 0):
            yield self.env.process(self.requestDisk(processingTimeDisk_read))
        if(processingTimeDisk_write > 0):
            yield self.env.process(self.requestDisk(processingTimeDisk_write))
        if(processingTimeCPU_read > 0):
            yield self.env.process(self.requestCPU(processingTimeCPU_read))
        if(processingTimeCPU_write > 0):   
            yield self.env.process(self.requestCPU(processingTimeCPU_write))

        # If the database has either a disk or cpu write
        # is Maser and the database replication is sync
        if((processingTimeCPU_write > 0 or processingTimeDisk_write > 0) 
            and self.master and not self.databaseReplication[req.requestTypeID].asyncReplication):
            yield self.env.process(self.syncReplication(req))
                
        # add RequestID to the completed Requests for this Database to prevent replication to this DB
        self.completedRequestIDs.append(req.reqid)
        monitorCompletion(self.env, req, self.serverid)

    def processReplication(self, index):
        processingData = self.databaseReplication[index]
        cpu = processingData.cpu
        disk = processingData.disk

        if(cpu > 0):
            yield self.env.process(self.requestCPU(cpu))
        if(disk > 0):   
            yield self.env.process(self.requestCPU(disk))


    def syncReplication(self, req):
        from components.handler import allComponents
        for component in self.databaseReplication[req.requestTypeID].dbs:
            nextComponent = allComponents.getComponentByID(component)
            if nextComponent != self.serverid:
                yield self.env.process(self.requestReplicatedComponent(nextComponent, req.requestTypeID))
            else:
                print(nextComponent, self.serverid)

    def requestReplicatedComponent(self, component, reqTypeID):
        with component.resource.request(priority=-1) as request:
            yield request
            yield self.env.process(component.processReplication(reqTypeID))


    def requestDisk(self, processingtime):
        with self.disk.resource.request() as request:
            yield request
            yield self.env.process(self.disk.process(processingtime))
    
    def requestCPU(self, processingtime):
        with self.cpu.resource.request() as request:
            yield request
            yield self.env.process(self.cpu.process(processingtime))

    def getOwnStepsID(self, req):
        destinationID = req.currentDestination
        return req.path[destinationID]