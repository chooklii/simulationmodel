from dataclasses import dataclass
from enforce_typing import enforce_types

@enforce_types
@dataclass
class RequestConfig:
    id: int
    name: str
    probability: float
    path: object
    monitorRequest: bool = True
    sameRequest: bool = False
    nextRequest: list = ()

@enforce_types
@dataclass
class WebTierConfig:
    serverid: str
    maxuser: int
    processingTime: object
    cpus: int = 1
    weight: int = 1
    cpuNoise: float = 0.05
    queueLength: int = 20000
    
@enforce_types
@dataclass
class ApplicationServerConfig:
    serverid: str
    maxuser: int
    processingTime: object
    cpuNoise: float = 0.05
    weight: int = 1
    cpus: int = 1
    multipleRequestsCPU: int = False
    multithreading: bool = False
    multithreadingParallelism: int = 0
    queueLength: int = 20000
    resourceSharing: bool = True

@enforce_types
@dataclass
class DatabaseServerConfig:
    serverid: str
    processingTime: object
    maxuser: int = 151
    useDisk: bool = False
    cpus: int = 1
    weight: int = 1
    # If Component is Master
    master: bool = False
    cpuNoise: float = 0.05
    queueLength: int = 1000
    
@enforce_types
@dataclass
class LoadBalancerConfig:
    serverid: str
    processingTime: object
    maxuser: int
    algorithm: str
    usecpu: bool = True
    cpus: int = 1
    cpuNoise:float = 0.05
    multipleRequestsCPU: int = False
    multithreading: bool = False
    multithreadingParallelism: int = 0

@enforce_types
@dataclass
class ExternalSystemsMQConfig:
    serverid: str
    writeFrequency: int
    writeRequestID: int 
    readRequests: list
    
@enforce_types
@dataclass    
class ExternalSystemMWConfig:
    serverid: str
    writeFrequency: int 
    # Request Triggered when Write Frequency is reached
    writeRequestID: int 
    # Requests that trigger Read from this Component
    readRequests: list

@enforce_types
@dataclass
class ExternalSystemRequestConfig:
    serverid: str
    writeRequestID: int
    thinktime: int
    numberclients: int

@enforce_types
@dataclass
class DatabaseReplicationConfig:
    cpu: float
    disk: float
    dbs: list
    asyncReplication: bool = False