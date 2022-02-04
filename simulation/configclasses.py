from dataclasses import dataclass, field
from dataclass_type_validator import dataclass_type_validator

@dataclass
class RequestConfig:
    id: int
    name: str
    probability: float
    path: object
    monitorRequest: bool = True
    sameRequest: bool = False
    nextRequest: list = field(default_factory=list)

    def __post_init__(self):
        dataclass_type_validator(self)

@dataclass
class WebTierConfig:
    serverid: str
    maxuser: int
    processingTime: object
    cpus: int = 1
    weight: int = 1
    cpuNoise: float = 0.05
    queueLength: int = 20000

    def __post_init__(self):
        dataclass_type_validator(self)
    
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

    def __post_init__(self):
        dataclass_type_validator(self)

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

    def __post_init__(self):
        dataclass_type_validator(self)

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

    def __post_init__(self):
        dataclass_type_validator(self)

@dataclass
class ExternalSystemsMQConfig:
    serverid: str
    writeFrequency: int
    writeRequestID: int 
    readRequests: list

    def __post_init__(self):
        dataclass_type_validator(self)

@dataclass    
class ExternalSystemMWConfig:
    serverid: str
    writeFrequency: int 
    # Request Triggered when Write Frequency is reached
    writeRequestID: int 
    # Requests that trigger Read from this Component
    readRequests: list

    def __post_init__(self):
        dataclass_type_validator(self)

@dataclass
class ExternalSystemRequestConfig:
    serverid: str
    writeRequestID: int
    thinktime: int
    numberclients: int

    def __post_init__(self):
        dataclass_type_validator(self)

@dataclass
class DatabaseReplicationConfig:
    cpu: float
    disk: float
    dbs: list
    asyncReplication: bool = False

    def __post_init__(self):
        dataclass_type_validator(self)