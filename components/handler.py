# Handle all Components
from components.applicationserver import ApplicationServer
from components.webtier import WebTier
from components.database import Database
from components.externalSystems import ExternalSystem
from components.loadbalancer import LoadBalancer

import config

# this class contains all possible components and provides some general functions 
# like a getByID to enable a selection of the required component


class Components(object):
    def __init__(self):
        self.env = None
        self.components = None

    def setEnv(self, env):
        self.env = (env,)
        self.components = self.initComponents(env)

    def getComponentByID(self, cID):
        value = filter(lambda x: x.serverid == cID, self.components)
        return next(iter(list(value)))

    def initComponents(self, env):
        components = []
        for single in config.WEB_TIERS:
            components.append(
                WebTier(
                    env=env,
                    serverid=single.serverid,
                    maxuser=single.maxuser,
                    processingTime=single.processingTime,
                    queueLength=single.queueLength,
                    cpus=single.cpus,
                    weight=single.weight,
                    cpuNoise=single.cpuNoise,
                    sslTimeout=config.SSL_TIMEOUT,
                    fullSSLConnectionTime=config.FULL_SSL_CONNECTION_TIME,
                    reuseSSLConnectionTime=config.REUSE_SSL_CONNECTION_TIME,
                )
            )
        for single in config.APP_SERVER:
            components.append(
                ApplicationServer(
                    env=env,
                    serverid=single.serverid,
                    maxuser=single.maxuser,
                    processingTime=single.processingTime,
                    resourceSharing=single.resourceSharing,
                    cpus=single.cpus,
                    weight=single.weight,
                    multipleRequestsCPU=single.multipleRequestsCPU,
                    multithreading=single.multithreading,
                    multithreadingParallelism=single.multithreadingParallelism,
                    cpuNoise=single.cpuNoise,
                    queueLength=single.queueLength,
                    sslTimeout=config.SSL_TIMEOUT,
                    fullSSLConnectionTime=config.FULL_SSL_CONNECTION_TIME,
                    reuseSSLConnectionTime=config.REUSE_SSL_CONNECTION_TIME,
                )
            )
        for single in config.DATABASES:
            components.append(
                Database(
                    env=env,
                    serverid=single.serverid,
                    maxuser=single.maxuser,
                    processingTime=single.processingTime,
                    useDisk=single.useDisk,
                    weight=single.weight,
                    cpuNoise=single.cpuNoise,
                    queueLength=single.queueLength,
                    cpus=single.cpus,
                    master=single.master,
                    databaseReplication=config.DATABASE_REPLICATION,
                )
            )
        for single in config.LOADBALANCER:
            components.append(
                LoadBalancer(
                    env=env,
                    serverid=single.serverid,
                    maxuser=single.maxuser,
                    processingTime=single.processingTime,
                    algoritm=single.algorithm,
                    sslTimeout=config.SSL_TIMEOUT,
                    fullSSLConnectionTime=config.FULL_SSL_CONNECTION_TIME,
                    reuseSSLConnectionTime=config.REUSE_SSL_CONNECTION_TIME,
                    cpus=single.cpus,
                    useCPU=single.usecpu,
                    cpuNoise=single.cpuNoise,
                    multipleRequestsCPU=single.multipleRequestsCPU,
                    multithreading=single.multithreading,
                    multithreadingParallelism=single.multithreadingParallelism
                )
            )
        return components


allComponents = Components()


def initExternalSystemsMQ(env):
    externalSystems = []
    for single in config.EXTERNALSYSTEMS_MQ:
        if single.writeFrequency > 0:
            externalSystems.append(
                ExternalSystem(
                    env=env,
                    serverid=single.serverid,
                    writeFrequency=single.writeFrequency,
                    writeRequestID=single.writeRequestID,
                    readRequests=single.readRequests,
                )
            )
    return externalSystems


def initExternalSystemsMW(env):
    externalSystems = []
    for single in config.EXTERNALSYSTEMS_MW:
        externalSystems.append(
            ExternalSystem(
                env=env,
                serverid=single.serverid,
                writeFrequency=single.writeFrequency,
                writeRequestID=single.writeRequestID,
                readRequests=single.readRequests,
            )
        )
    return externalSystems
