from simulation.configclasses import (
    ApplicationServerConfig,
    DatabaseServerConfig,
    WebTierConfig,
    ExternalSystemMWConfig,
    ExternalSystemsMQConfig,
    RequestConfig,
    LoadBalancerConfig,
    DatabaseReplicationConfig
)

# All numbers of requests and sessions used for simulation - each value in the list results in a new simulation
REQUESTS_PER_SECOND = []
UNIQUE_SESSIONS = [500, 1000, 1250, 1500, 1750, 2000]
# If Sessions or Requests per Second should be used
USE_SESSIONS = True
# The time the simulation sleeps - large values result in a faster, but more inaccurate simulation
TIMEOUT_INTERVALL = 0.001
# The think time for sessions
THINK_TIME = 7
# The time (in s) the simulation is run
SIM_TIME = 40
# If one request results in one or multiple requests per request - It is possible that requests are used, but each request sends an average of 5 requests
MULTIPLE_REQUESTS_PER_USER = False
# These values define the minimum and maximum parameters for the number of requests - a random value inbetween will be selected
MIN_NUMBER_OF_REQUESTS = 1
MAX_NUMBER_OF_REQUESTS = 1
# If SSL is used
SSL = False
# SSL Timeout before a full connection is required
SSL_TIMEOUT = 10
FULL_SSL_CONNECTION_TIME = 0.17
REUSE_SSL_CONNECTION_TIME = 0.02

# All Types of Requests

"""
REQUESTS = [
    RequestConfig(
        id = ID of the Request
        name = Name of the Request
        probability = Probability, that this request is selected
        path = Path is the path the request is taking. The step-id is required for the processing time on component level. The componentIDs are all possible
        components for this step. If their are multiple possible components a Load Balancer is required prior to these, as a normal component is 
        not capable of selecting
        monitorRequest = If the Request should be monitored
        sameRequest = If the Request is considered the same request like the previous one - This 
        is used if e.g. all JS, HTML and CSS Files are considered as one request "Home Page"
        
        nextRequest = The possible next requests. This can be used to include some scenarios into 
        the simulation. e.g. If a user requests the startpage the next request is allways a login.
        If this value is not defined the next request is selected based on the probability
    )
        RequestConfig(
        id=1,
        name="New Order",
        name="Buy",
        probability=0.5,
        path={
            0: [{"step-id": 1, "componentIDs": ["AS"]}],
            1: [{"step-id": 1, "componentIDs": ["DB1"]}],
        },
        nextRequest=[
            {
                id: 1, probability: 0.5
            }
        ]
        
    ),
]
"""

REQUESTS = [
    RequestConfig(
        id=1,
        name="Buy",
        probability=0.5,
        path={
            0: [{"step-id": 1, "componentIDs": ["WT"]}],
            1: [{"step-id": 1, "componentIDs": ["AS"]}],
            2: [{"step-id": 1, "componentIDs": ["DB"]}],
        },
    ),
    RequestConfig(
        id=2,
        name="Background",
        probability=0.5,
        path={
            0: [{"step-id": 2, "componentIDs": ["WT"]}],
            1: [{"step-id": 2, "componentIDs": ["AS"]}],
            2: [{"step-id": 2, "componentIDs": ["DB"]}],
        },
    ),

]

# All Components and their informations - It is important to match the step-ids within the processing times

"""
procesingTime={
    1: 0.01,
    2: 0.1
}
"""

WEB_TIERS = [
    WebTierConfig(
        serverid="WT",
        maxuser=500,
        processingTime={
            1: 0.0008710,
            2: 0.0008710
        })
]
APP_SERVER = [
    ApplicationServerConfig(
        serverid="AS",
        maxuser=500,
        processingTime={
            1: 0.008761,
            2: 0.004505,
        }),
]

"""
 Databases are a special case, as they require a disk and cpu processing time
processingTime={
     1: {
        "disk": {
            "read": 0.012,
            "write": 0
        },
        "cpu": {
            "read": 0.053,
            "write": 0
        }
    },
"""


DATABASE_REPLICATION = {
    # REQUEST-ID : DatabaseReplicationConfig
}

DATABASES = [
    DatabaseServerConfig(
        serverid="DB",
        processingTime={
            1: {
                "cpu": {
                    "read": 0.001613,
                    "write": 0
                },
                "disk": {
                    "read": 0,
                    "write": 0
                }
            },
            2: {
                "cpu": {
                    "read": 0.0008294,
                    "write": 0
                },
                "disk": {
                    "read": 0,
                    "write": 0
                }
            }
        })
]

LOADBALANCER = [
    # LoadBalancerConfig()
]

# If Requests from external Systems should be monitored
MONITOR_EXTERNAL_REQUEST = True
# External Systems with Message Queue
EXTERNALSYSTEMS_MQ = []
# External Systems with Middleware
EXTERNALSYSTEMS_MW = []
# External Systems which send random requests
EXTERNALSYSTEMS_RQ = []

# Monitoring Variables
INCLUDE_COMPARED_RESULTS = True
# If the Response Time or Throughput should be included in the graph
RESPONSE_TIME = True
OWN_NAME = "Model"
# Compared Results displayed in the graph - Make sure that a value for all number of clients / requests is givens
COMPARED_RESULTS = {
    "(Bacigalupo et al., 2004)": {
        500: 0.1, 
        1000: 0.15, 
        1250: 0.2, 
        1500: 1.1, 
        1750: 2.5, 
        2000: 4.1
    },
}

# X and Y Label of the Graph
X_LABEL = "Concurrent Sessions"
Y_LABEL = "Response Time"
