from simulation.monitoring.monitor import monitor_rejection, monitor_queue

# check if max number of queued requests is reached, if so reject and monitor
def checkQueueLength(selectedServer, env, req):
    if selectedServer.resource.count >= selectedServer.resource.capacity:
        # Monitor queueing of the request
        monitor_queue(req, env,selectedServer.serverid)
    # If nextComponent has no Queue reject if full
    if not hasattr(selectedServer, "queueLength"):
        if selectedServer.resource.count >= selectedServer.resource.capacity:
            monitor_rejection(req, selectedServer.serverid)
            return False
        else:
            return True
    queueLength = selectedServer.queueLength
    if(queueLength != 0 and queueLength <= len(selectedServer.resource.queue)):
        # Queue is full - Reject request
        monitor_rejection(req, selectedServer.serverid)
        return False
    else:
        return True