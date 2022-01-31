import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from monitoring.monitoring import SingleRequestMonitoring, ComponentMonitoring

"""
Monitor all requests
"""

data = {}
datastore = {}

# Monitor income time of the Request
def monitor_request(env, req):
    if req.monitor:
        if req.sameRequest:
            data[req.reqid].setExtraStartTime(round(env.now, 4))
        else:
            data[req.reqid] = SingleRequestMonitoring(req.requestTypeID)
            data[req.reqid].setStartTime(round(env.now, 4))

# Monitor outgo time of the Response
def monitor_response(env, req):
    if req.monitor:
        if req.sameRequest:
            data[req.reqid].setExtraCompleted(round(env.now, 4))
        else:
            data[req.reqid].setRequestCompleted(round(env.now, 4))

def monitor_rejection(req, reasonName):
    if req.monitor:
        data[req.reqid].setRejected()
        if reasonName not in data[req.reqid].components:
            initComponent(req, reasonName)
            data[req.reqid].components[reasonName] = ComponentMonitoring()
        data[req.reqid].components[reasonName].setRejected()

def monitor_queue(req, env, reasonName):
    if req.monitor:
        if reasonName not in data[req.reqid].components:
            initComponent(req, reasonName)
            data[req.reqid].components[reasonName] = ComponentMonitoring()
        data[req.reqid].components[reasonName].setQueued(round(env.now, 4))

def initComponent(req, name):
    data[req.reqid].addComponent(name)

def monitorStart(env, req, name):
    if req.monitor:
        if name not in data[req.reqid].components:
            initComponent(req, name)
            data[req.reqid].components[name] = ComponentMonitoring()
        data[req.reqid].components[name].setStart(round(env.now,4))

def monitorCompletion(env, req, name):
    if req.monitor:
        data[req.reqid].components[name].setCompleted(round(env.now,4))


def display_averages(key, time):
    # Display all averages on the terminal
    amount_rejected = len({k: v for k, v in data.items() if v.rejected})
    amount_completed = len({k: v for k, v in data.items() if v.end is not None and not v.rejected })
    print("___________")
    print("Number of Requests started: {}".format(len(data)))
    print("Data for {} requests/s".format(key))
    print("Average Response Time for successfull requests: {}".format(calculateAverageResponseTime(data)))
    print("Throughput/s: {}".format(amount_completed/time))
    print("Amount rejected Requests: {}%".format(round((amount_rejected / len(data.items()))*100, 4)))   


def calculateAverageResponseTime(data):
    dataWithResponseTime = {k: v for k, v in data.items() if v.responseTime }
    sumOfData = {sum(d.responseTime for d in dataWithResponseTime.values())}.pop()
    return round(sumOfData / len(dataWithResponseTime), 4)

def requestResponseTimes(data, f, requests, time):
    # write the response the for each request to the data file
    f.write("Individual Request Response Times:")
    for request in requests:
        dataForThisRequest = {k: v for k, v in data.items() if v.requestTypeID == request.id and v.end and not v.rejected}
        if(len(dataForThisRequest) > 0):
            averageResponseTime = calculateAverageResponseTime(dataForThisRequest)
            throughput = len(dataForThisRequest) / time
            f.write("\n")
            f.write("{} Response Time: {}".format(request.name, averageResponseTime))
            f.write("\n")
            f.write("{} Throughput: {}".format(request.name, throughput))
            f.write("\n")
            f.write("Amount {}: {}".format(request.name,len(dataForThisRequest)))
    f.write("\n")


def calculateComponentAverages(data, f, requests, time):
    componentResponseTimes = {}
    amountRejected = {}
    amountQueued = {}

    for reqperSecond, values in data.items():
        for name, results in values.components.items():
            if name not in componentResponseTimes:
                componentResponseTimes[name] = []
            if hasattr(results, "responseTime") and results.responseTime is not None:
                componentResponseTimes[name].append(results.responseTime)
            if results.queuedRequest is not None:
                if name not in amountQueued:
                    amountQueued[name] = {}
                    amountQueued[name]["amount"] = 0
                    amountQueued[name]["queueTimes"] = []
                amountQueued[name]["amount"] +=1
                if(results.start and results.queuedRequestStart):
                    amountQueued[name]["queueTimes"].append(results.start - results.queuedRequestStart)     
            if results.rejectedRequest is not None:
                if name not in amountRejected:
                    amountRejected[name] = 0
                amountRejected[name] +=1    
    # Write to File
    f.write("\n")
    requestResponseTimes(data, f, requests, time)
    f.write("\n")
    f.write("Component Response Times:")
    f.write("\n")
    for key, value in componentResponseTimes.items():
        average = round(sum(value) / len(value),4)
        f.write("{} Response Time: {}  - Amount: {}".format(key, average, len(value)))
        f.write("\n")
    if len(amountRejected) > 0:
        f.write("\n")
        f.write("Amount Rejected Requests:")
        f.write("\n")
        f.write("\n")
        for key, value in amountRejected.items():
            f.write("{} Rejected Requests: {}".format(key, value))
            f.write("\n")
    if len(amountQueued) > 0:
        f.write("\n")
        f.write("Amount Queued Requests:")
        f.write("\n")
        f.write("\n")
        for key, value in amountQueued.items():
            average = round(sum(value["queueTimes"]) / len(value["queueTimes"]),4)
            f.write("{} Queued Requests: {}".format(key, value["amount"]))
            f.write("\n")
            f.write("{} Average Queue Time: {}".format(key, average))
            f.write("\n")
            f.write("{} Max Queue Time: {}".format(key, np.max(value["queueTimes"])))
            f.write("\n")


def calculateThroughput(dataset, time):
    amount_completed = amountCompleted(dataset)
    return  amount_completed / time

def amountCompleted(dataset):
    return len({k: v for k, v in dataset.items() if v.end and not v.rejected })

def add_to_datastore(requests_per_second):
    global data
    datastore[requests_per_second] = data
    data = {}


def plotGraph(
    time, 
    include_compared_results, 
    compared_results, 
    own_name,
    xticks,
    metric_response_time,
    ylabel,
    xlabel):
    dict_to_plot = {}
    for key in datastore:
        dict_to_plot[key] = {}
        dict_to_plot[key]["requests"] = key
        if not metric_response_time:
            dict_to_plot[key][own_name] = calculateThroughput(datastore[key], time)
        else:
            dict_to_plot[key][own_name] = calculateAverageResponseTime(datastore[key])
        if(include_compared_results):
            for name, data in compared_results.items():
                dict_to_plot[key][name] = data[key]
    dataframe = pd.DataFrame.from_dict(dict_to_plot, orient='index')
    dataframe.plot(
        x="requests",ylabel=ylabel, xlabel=xlabel, xticks=xticks
    )
    plt.savefig('simulation/simulationModel/output/output.png')


def writeDataToFile(time, include_compared_results, comparedResults, requests):
    with open("simulation/simulationModel/output/data.txt", "w+") as f:
        for key in datastore:
            responseTime = calculateAverageResponseTime(datastore[key])
            f.write("______")
            f.write("\n")
            f.write("______")
            f.write("\n")
            f.write("Requests/s {}".format(key))
            f.write("\n")
            f.write("______")
            f.write("\n")
            f.write("Number of Requests: {}".format(len(datastore[key])))
            f.write("\n")
            f.write("Response Time: {}".format(responseTime))
            f.write("\n")
            f.write("Throughput: {}".format(calculateThroughput(datastore[key], time)))
            f.write("\n")
            f.write("Completed Requests: {}".format(amountCompleted(datastore[key])))
            f.write("\n")
            calculateComponentAverages(datastore[key], f, requests, time)
            if include_compared_results:
                for name, data in comparedResults.items():
                    f.write("Simulation Error {}: {}".format(name, round((1-(data[key] / responseTime))*100,2)))
                    f.write("\n")
            f.write("\n")