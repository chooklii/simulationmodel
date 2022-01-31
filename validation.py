# Validate the config File - called before the simulation is started

def checkIfAllStepIDsAreDefined(config):
    allComponents: list = []
    allComponents += [x for x in config.DATABASES]
    allComponents += [x for x in config.APP_SERVER]
    allComponents += [x for x in config.WEB_TIERS]
    allComponents += [x for x in config.LOADBALANCER]

    for request in config.REQUESTS:
        for stepKey, stepValue in request.path.items():
            for singleStep in stepValue:
                for component in singleStep["componentIDs"]:
                    if not checkIfStepIDIsDefined(allComponents, component, singleStep["step-id"]):
                        print("!!Attention!! -  Component {} has not defined the Step-ID {}".format(component, singleStep["step-id"]))
                        return False
    return True


def checkIfStepIDIsDefined(allComponents, serverid, stepid):
    requiredComponent = [x for x in allComponents if x.serverid == serverid]
    if len(requiredComponent) == 0:
        print("!!Attention!! - Component {} is not defined".format(serverid))
        return True
    elif stepid in requiredComponent[0].processingTime:
        return True

def checkIfAllComponentsAreUsed(config):
    allComponents: list = []
    allComponents += [x.serverid for x in config.DATABASES]
    allComponents += [x.serverid for x in config.APP_SERVER]
    allComponents += [x.serverid for x in config.WEB_TIERS]
    allComponents += [x.serverid for x in config.LOADBALANCER]

    allUsedComponents: list = []

    for request in config.REQUESTS:
        for key, value in request.path.items():
            for step in value:
                for component in step["componentIDs"]:
                    if component not in allUsedComponents:
                        allUsedComponents.append(component)

    allUnusedComponents = [x for x in allComponents if x not in allUsedComponents]
    if len(allUnusedComponents) > 0:
        for item in allUnusedComponents:
            print("!!Attention!! - Component {} is not used".format(item))
            return False
    return True
                    

def checkIfAllStepsAreUsed(config):
    allComponents: list = []
    allComponents += [x for x in config.DATABASES]
    allComponents += [x for x in config.APP_SERVER]
    allComponents += [x for x in config.WEB_TIERS]
    allComponents += [x for x in config.LOADBALANCER]

    for component in allComponents:
        for key, value in component.processingTime.items():
            if not checkIfKeyIsUsed(config, component.serverid, key):
                print("!!Attention!! -  Component {} has an unused Key {}".format(component.serverid, key))
                return False
    return True


def checkIfKeyIsUsed(config,serverid, key):
    for request in config.REQUESTS:
        for stepKey, stepValue in request.path.items():
            for singleStep in stepValue:
                if singleStep["step-id"] == key and serverid in singleStep["componentIDs"]:
                    return True
    


def validateConfigData(config):
    if checkIfAllComponentsAreUsed(config) and checkIfAllStepIDsAreDefined(config) and checkIfAllStepsAreUsed(config):
        return True
    else: 
        print("Simulation stopped due to config Errors!")
        return False