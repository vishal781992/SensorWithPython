# Codetimestamp=None for the OPS243-c sensor with python and UART and USB interface by - Vishal Chopade (
# c-vishal.chopade@charter.com)t Version provides - duplicate deletion, converts the floats into int to keep the
# plot smooth for the same range diff mag. uniform naming scheme throughout code

import json
# from MQTT_handle import MQTTHandle as mqtt
import logging
import math
import platform
import psutil
import re
import socket
import sys
import time
import uuid
import GPUtil

from matplotlib import pyplot as plt
from pip._internal.utils.misc import tabulate
from termcolor import colored

# mention the config file being used

Gui = True
Debug = True
# values are received from the config file
if Gui:
    fig = plt.figure()
    ax1 = fig.add_subplot(1, 1, 1)

'''
Files are opened here for writing/appending the data while the process starts
'''

if Debug:
    strr = "Creating/Opening the Files for collecting Debug Data"
    print(strr)
    Handle_writeJSONtoFile = open("Testdata_jsonStrings.txt", 'a')
    Handle_writeToTestFile = open("Testdata.txt", 'a')

'''
definitions for small processes
'''


# helps the user to get the direction of the object based on the signed speed.
def getObjDirection(var_avgSpd):
    try:
        if var_avgSpd < 0:
            var_direction = "AwayFromSensor"
        elif var_avgSpd >= 0:
            var_direction = "TowardsSensor"
        else:
            var_direction = "Unknown"
    except:
        var_direction = "Unknown"

    return var_direction


flag_lastJsonDetected = False


# helps the user to get the json format string to the server. Includes everything from direction to range.
def getJsonFormat(var_time, var_config, var_avgSpd, var_sUnit, var_rng, var_runit, var_length, var_lUnit, var_whichData,
                  var_lengthOfObj):
    global flag_lastJsonDetected

    var_direction = getObjDirection(var_avgSpd)
    var_avgSpd = abs(var_avgSpd)

    if var_whichData == "speed":
        try:
            dict_jsonToSend = {"timestamp": var_time, "config": var_config,
                               "detections": {"dirOfObj": var_direction, "element": "start", "avgSpeed": var_avgSpd,
                                              "sUnit": var_sUnit,
                                              "range": var_rng, "rUnit": var_runit,
                                              "length A1": abs(var_length), "length A2": abs(var_lengthOfObj),
                                              "lUnit": var_lUnit}}
            print(colored(json.dumps(dict_jsonToSend), 'cyan'))
            file1 = open("AlgorithComparison.txt", "a")  # append mode
            file1.write(json.dumps(dict_jsonToSend) + "\n")
            # mqtt = MQTT_handle.MQTTHandle("vishal!!!!!")
            # mqtt.run()
            flag_lastJsonDetected = True
        except:
            print(colored("Error occurred while processing json", 'blue'))

    elif var_whichData == "range":

        if flag_lastJsonDetected:
            try:
                dict_jsonToSend = {"timestamp": var_time, "config": var_config,
                                   "detections": {"dirOfObj": var_direction, "element": "end_linkedToAboveJson",
                                                  "avgSpeed": var_avgSpd, "sUnit": var_sUnit,
                                                  "range": var_rng, "rUnit": var_runit,
                                                  "length A1": abs(var_length), "length A2": abs(var_lengthOfObj),
                                                  "lUnit": var_lUnit}}
                print(colored(json.dumps(dict_jsonToSend), 'red'))
                file1 = open("AlgorithComparison.txt", "a")  # append mode
                file1.write(json.dumps(dict_jsonToSend) + "\n")
                file1.close()
                flag_lastJsonDetected = False
            except:
                print(colored("Error occurred while processing json", 'blue'))
        else:
            pass


def AvgTimeCalc(time_last, time_reference, SAMPLER_SIZE_FOR_CALIB):
    return float((time_last - time_reference) / SAMPLER_SIZE_FOR_CALIB)


def getAvgSpeed(list_realSpeedValues):
    var_avgOfSpeedValues = sum(list_realSpeedValues)
    var_avgOfSpeedValues = var_avgOfSpeedValues / len(list_realSpeedValues)
    return var_avgOfSpeedValues


def getKey(item):
    return item[0]


'''
Get the real speed considering the deployment angle
'''


def getRealSpeed(float_speedRawValue):
    return float_speedRawValue * math.cos(0)


# main loop to run while True

def main():
    global Gui
    global Debug

    # list and dictionary init
    tuples_rangeMag, list_mValues = [], []  # list
    list_magnitudes = []
    list_magMaxValue = []

    # using set
    list_visitedValues = set()
    list_realSpeedValues = []

    # Output variables init
    var_avgTime = 0.0
    var_magDiffFactor = 0  # the value is calculated dynamically
    var_speed = 0
    var_previousSpeed = 0
    str_direction = "-"
    str_unitFeet = "ft"
    str_unitFramesPerSec = "fps"
    str_nullStringPresent = "null"
    var_lengthOfObj = 0.0
    var_referenceMagValue = 0.00
    var_referenceMagBG = 0
    var_realSpeedValue = 0
    var_jsonReferenceRangeValue = 0.0
    var_nullFloat = 0.0

    const_numMaxTuples = 50
    const_percentileToNet = 0.30
    const_stopConfirmationFactor = 10
    const_trainDetectionFactor = 4
    const_samplerSizeForCalib = 15
    const_sleepSecInterval = 1
    const_refMagDiffFactor = 0
    const_noSpeedValueFactor = 5

    counter_RangeValues = 0
    counter_AvgTime = 0
    counter_count15UntilDie = 0

    time_referenceForCalib = 0
    time_hardwareForSpeed = 0
    time_referenceBGTracker = 0
    time_objEntered = 0
    time_start = time.time()
    time_objStart = 0
    time_s1 = 0.0
    time_sinceStartOfProgram = 0
    time_timeInitialJson = 0
    time_timeFinalJson = 0
    time_usedForDifference = 0
    time_forSleep = 0.06

    # flags for the program
    flag_firstValue = True
    flag_objEntered = False
    flag_speedDetected = False
    flag_objLeft = False
    flag_firstTime = True
    flag_speedIsDetectedOnSensor = False
    flag_sendJsonInitial = True
    flag_sendJsonFinal = False

    const_config = "sample"

    while True:
        time.sleep(time_forSleep)
        # string receives the data from the sensor
        if time_referenceBGTracker == 0:
            # this timer is dedicated to the background tracker reference calculator.
            time_referenceBGTracker = time.time()
            # the timer for the program starts here
            time_sinceStartOfProgram = time.time()

        receiveString = handle_fileRead.readline()
        if len(receiveString) > 0:
            try:
                json_msg = json.loads(receiveString)

            except:
                continue

            # range measurement
            if 'range' in json_msg:
                time_hardwareForRange = 0

                try:
                    var_magnitudes = json_msg['magnitude']
                    var_ranges = json_msg['range']
                    time_hardwareForRange = float(json_msg['time'])
                    # it resets the time everytime the line is hit.
                    # This will give the sensor 25 seconds everytime it stops sending the data.
                    time_sinceStartOfProgram = time.time()
                except:
                    continue

                # calculates the hardware time value for the time between two outputs, helpful for the obj detection
                if counter_AvgTime == 0:
                    time_referenceForCalib = time_hardwareForRange
                    counter_AvgTime += 1

                if counter_AvgTime == const_samplerSizeForCalib:
                    time_lastForCalib = time_hardwareForRange
                    var_avgTime = AvgTimeCalc(time_lastForCalib, time_referenceForCalib, const_samplerSizeForCalib)
                    print(var_avgTime)
                    time_forSleep = var_avgTime
                    print("Program has started reading the Sensor!")
                # counter is incremented here for sampling time.
                counter_AvgTime = counter_AvgTime + 1

                # make the tuple of range and mag
                for (rng, mag) in zip(var_ranges, var_magnitudes):
                    try:
                        tuples_rangeMag.append([float(rng), float(mag)])
                        # counter for the range/mag values
                        counter_RangeValues += 1

                    except:
                        tuples_rangeMag.append([float(0), float(0.00)])

                # checks for the value set for 50 units approx.
                if len(tuples_rangeMag) < const_numMaxTuples:
                    continue

                time_Mid = time.time()
                # if the samplers are not collected until 1 min, it will continue
                if time_Mid < (time_start + const_sleepSecInterval):
                    continue

                time_start = time_Mid

                # clearing the plot
                if Gui:
                    plt.clf()

                # sorting the values in a tuple, def above
                tuples_rangeMag = sorted(tuples_rangeMag, key=getKey)

                # creating the list
                list_magnitudesNormalize = []
                list_ranges = []
                list_magnitudes = []

                # clearing the list to make sure the list does not contain any previous data..observed already!
                list_ranges.clear()
                list_magnitudes.clear()
                list_visitedValues.clear()

                # Iteration, duplicate ranges
                for rng, magnitude in tuples_rangeMag:
                    if int(rng) not in list_visitedValues:
                        list_visitedValues.add(int(rng))
                        list_ranges.append((int(rng)))
                        list_magnitudes.append(magnitude)

                # loop for normalizing the values for magnitude
                for magnitude in list_magnitudes:
                    list_magnitudesNormalize.append(float(magnitude / max(list_magnitudes)))

                tuple_rangeMaxMag = list(filter(lambda x: x[1] == max(list_magnitudes), tuples_rangeMag))
                max_rangeMag = dict(maxRange=tuple_rangeMaxMag[0][0], maxMag=tuple_rangeMaxMag[0][1])
                currentMaxMag = float(max_rangeMag["maxMag"])
                currentMaxRange = float(max_rangeMag["maxRange"])

                if Debug:
                    Handle_writeToTestFile.write(str(tuple_rangeMaxMag[0]) + "\n")

                if not flag_objEntered:
                    list_magMaxValue.append(float(max_rangeMag["maxMag"]))

                # Annotate the graph with peak range and mag for the samples we have collected.
                if Gui:
                    plt.annotate('Cur. Max R:%.2f, M:%.2f' % (
                        currentMaxRange, float(currentMaxMag / max(list_magnitudes))),
                                 xy=(currentMaxRange,
                                     float(currentMaxMag / max(list_magnitudes))),
                                 xytext=(currentMaxRange + 10,
                                         float(currentMaxMag / max(list_magnitudes)) - 0.1),
                                 arrowprops=dict(facecolor='green', shrink=0.05))

                    # label and title for the plot
                    plt.title(str_direction + " Curr Speed:%.2f Past Speed:%.2f\nMag vs Range" % (
                        var_speed, var_previousSpeed),
                              fontsize=10)
                    plt.xlabel("Range", labelpad=-5)
                    plt.ylabel("Magnitude", labelpad=-5)

                # if the obj is not present in the view of sensor it will update the reference
                time_ReferenceBGTracker_current = time.time()

                if not flag_objEntered and ((time_ReferenceBGTracker_current - time_referenceBGTracker) > 6):
                    var_referenceMagBG = float(sum(list_magMaxValue) / len(list_magMaxValue))
                    const_refMagDiffFactor = const_percentileToNet * var_referenceMagBG
                    print(
                        colored("reference BG value: %d  ... diff Factor: %.2f" % (
                            var_referenceMagBG, const_refMagDiffFactor),
                                'green'))
                    time_referenceBGTracker = 0
                    time_ReferenceBGTracker_current = 0
                    list_magMaxValue.clear()

                if flag_firstValue:
                    ReferenceRangeValue = currentMaxRange
                    var_referenceMagValue = currentMaxMag
                    var_referenceMagBG = currentMaxMag
                    const_refMagDiffFactor = const_percentileToNet * var_referenceMagBG
                    # print(colored("reference value of mag MAX %f" % var_referenceMagValue, 'green'))

                    flag_firstValue = False

                # The obj detection is done here. main logic
                # checks with the reference of range, if the object is in the view or not
                if flag_speedIsDetectedOnSensor:

                    if not flag_objEntered:
                        # if the statements is activated, mag value will be set to current max mag
                        var_referenceMagValue = currentMaxMag
                        var_jsonReferenceRangeValue = currentMaxRange
                        var_magDiffFactor = const_percentileToNet * var_referenceMagValue
                        time_objEntered = time.time()
                        # if the below statement doest work, keep it out of the above if not loop
                        flag_objEntered = True
                    time_ObjInView = time.time()

                    # abs value keeps teh sum positive, always!
                    time_ElapsedSinceObjDetectedFirst = abs(int(float(time_objEntered) - float(time_ObjInView)))

                    if (((currentMaxMag < float(var_referenceMagValue) - var_magDiffFactor) or
                         (currentMaxMag > float(var_referenceMagValue) + var_magDiffFactor)) and (
                            time_ElapsedSinceObjDetectedFirst) < const_trainDetectionFactor):
                        strr = "Object might have stopped!"
                        # print(strr)
                    elif const_trainDetectionFactor < time_ElapsedSinceObjDetectedFirst < const_stopConfirmationFactor:
                        strr = "Train might have detected!"
                        print(strr)

                    if time_ElapsedSinceObjDetectedFirst > const_stopConfirmationFactor:
                        strr = "Object stopped!"
                        # print(strr)

                # if the object is already entered in the view, perform the below elif statement

                # print(flag_objEntered, flag_speedIsDetectedOnSensor,time_hardwareForRange - time_hardwareForSpeed,
                # Avg_time*3)

                if ((flag_objEntered and flag_speedIsDetectedOnSensor) and
                    ((time_hardwareForRange - time_hardwareForSpeed) > var_avgTime * const_noSpeedValueFactor)) and \
                        ((currentMaxMag > float(var_referenceMagBG) - const_refMagDiffFactor) and
                         (currentMaxMag < float(var_referenceMagBG) + const_refMagDiffFactor)):
                    time_ObjLeaving = time.time()
                    time_ObjTimeSpend = (time_ObjLeaving - time_objEntered)
                    time_objEntered = 0
                    time_ObjLeaving = 0

                    # resetting the flags for next readings
                    flag_speedIsDetectedOnSensor = False
                    flag_objEntered = False
                    flag_objLeft = True

                    var_referenceMagBG = currentMaxMag
                    const_refMagDiffFactor = const_percentileToNet * var_referenceMagBG

                if Gui:
                    plt.xlim(0, 30, 3)
                    plt.ylim(0, 1.2, 0.1)
                    # plt.plot(list_ranges, list_magnitudes_normalize, linewidth='3')
                    plt.plot(list_ranges, list_magnitudesNormalize, 'o', color='green')

                    plt.legend(["Max:%d" % max(list_magnitudes)], bbox_to_anchor=(0.65, 0.50), ncol=2)

                    plt.pause(.05)

                # stopping  detection.
                time_objEnd = time.time()
                time_passedByObjInSensor = abs(time_objEnd - time_objStart)

                if flag_speedDetected and (time_passedByObjInSensor > 1):

                    if flag_objLeft:
                        flag_objLeft = False

                        # sends the data to make a dict which then can be converted to the json.
                        if flag_sendJsonFinal:
                            print("len of list: ", len(list_realSpeedValues))
                            var_avgSpeed = getAvgSpeed(list_realSpeedValues)
                            # time_timeFinalJson = abs(time.time() - time_timeInitialJson)
                            time_timeFinalJson = abs(time_usedForDifference - time_hardwareForRange)
                            strr = "train detect" if (time_timeFinalJson > 2.5 and var_avgSpeed > 20) else "noise"
                            print(strr)
                            print("time difference: ", time_timeFinalJson)
                            var_distance = abs(var_avgSpeed * time_timeFinalJson)

                            print("length : ", var_lengthOfObj)

                            getJsonFormat(time_hardwareForRange, strr, var_avgSpeed, str_unitFramesPerSec,
                                          var_jsonReferenceRangeValue, str_unitFeet, var_distance, str_unitFeet,
                                          "range", var_lengthOfObj)

                            # resetting the flag for another speed json output, assumes that the objectg has
                            #  completely left
                            flag_sendJsonFinal = False
                            flag_sendJsonInitial = True
                            list_realSpeedValues.clear()  # clearing the list for next reading set
                            time_usedForDifference = 0

                        flag_speedDetected = False

                if flag_firstTime:
                    flag_firstTime = False
                else:
                    del tuples_rangeMag[:counter_RangeValues]

                counter_RangeValues = 0

            # Time_xx refers to Speed section, time_xx refers to range section if the speed is detected
            # in the field, The function will come here to set the flags and calculate the length
            elif 'speed' in json_msg:
                time_hardwareForSpeed = 0
                time_objStart = time.time()
                flag_speedIsDetectedOnSensor = True
                flag_speedDetected = True

                # current speed occupies the var_speed var and var_previousSpeed is taken by previous speed.
                # helps to show both the speeds
                var_previousSpeed = var_speed
                try:
                    speedRawValue = float(json_msg['speed'])  # use try except
                    time_hardwareForSpeed = float(json_msg['time'])
                except:
                    continue

                # the deployment angle will decide th real speed of the object
                var_realSpeedValue = getRealSpeed(speedRawValue)
                list_realSpeedValues.append(abs(var_realSpeedValue))

                # sends the data to make a dict which then can be converted to the json.
                if flag_sendJsonInitial:
                    time_timeInitialJson = time.time()
                    time_usedForDifference = time_hardwareForSpeed
                    # added the hardware time
                    getJsonFormat(time_hardwareForSpeed, const_config, var_realSpeedValue, str_unitFramesPerSec,
                                  var_nullFloat, str_unitFeet, var_lengthOfObj, str_unitFeet, "speed", var_lengthOfObj)
                    flag_sendJsonInitial = False
                    flag_sendJsonFinal = True

                # print(colored("speed %.2f" % var_realSpeedValue, 'grey'))
                time_s2 = time.time()
                var_delta = time_s2 - time_s1
                time_s1 = time_s2

                # more than 1 second
                if var_delta > 1.00:
                    # new movement is detected
                    var_lengthOfObj = 0.00
                else:
                    # accumulate the moments before the obj lefts
                    var_lengthOfObj = var_lengthOfObj + (var_realSpeedValue * var_delta)

                if var_realSpeedValue < 0:  # going away
                    var_speed = abs(var_realSpeedValue)
                    str_direction = "|->"

                else:  # coming inwards
                    var_speed = abs(var_realSpeedValue)
                    str_direction = "|<-"

        elif len(receiveString) == 0:
            time_untilKillsTheApp = time.time()
            time_ = abs(time_untilKillsTheApp - time_sinceStartOfProgram)
            print("time until die: ", (25 - time_))

            if abs(time_) > 25:
                sys.exit()

    if Gui:
        plt.show()  # important


def getSystemInfo():
    try:
        info = {'platform': platform.system(), 'platform-release': platform.release(),
                'platform-version': platform.version(), 'architecture': platform.machine(),
                'hostname': socket.gethostname(), 'ip-address': socket.gethostbyname(socket.gethostname()),
                'mac-address': ':'.join(re.findall('..', '%012x' % uuid.getnode())), 'processor': platform.processor(),
                'ram': str(round(psutil.virtual_memory().total / (1024.0 ** 3))) + " GB"}
        return json.dumps(info)
    except Exception as e:
        logging.exception(e)


def getList():
    gpus = GPUtil.getGPUs()
    list_gpus = []
    for gpu in gpus:
        # get the GPU id
        gpu_id = gpu.id
        # name of GPU
        gpu_name = gpu.name
        # get % percentage of GPU usage of that GPU
        gpu_load = f"{gpu.load * 100}%"
        # get free memory in MB format
        gpu_free_memory = f"{gpu.memoryFree}MB"
        # get used memory
        gpu_used_memory = f"{gpu.memoryUsed}MB"
        # get total memory
        gpu_total_memory = f"{gpu.memoryTotal}MB"
        # get GPU temperature in Celsius
        gpu_temperature = f"{gpu.temperature} °C"
        gpu_uuid = gpu.uuid
        list_gpus.append((
            gpu_id, gpu_name, gpu_load, gpu_free_memory, gpu_used_memory,
            gpu_total_memory, gpu_temperature, gpu_uuid
        ))

    print(tabulate(list_gpus, headers=("id", "name", "load", "free memory", "used memory", "total memory",
                                       "temperature", "uuid")))


json.loads(getSystemInfo())
if __name__ == "__main__":
    try:
        getList()
        print("System info: ", getSystemInfo())
        handle_fileRead = open("testdata_5.txt", 'r')  # _short
        main()
    except:
        print("Error: Error running the Sensor Application, Try again!")

'''
# Iteration, duplicate ranges
for rng, magnitude in tuples_rangeMag:
if rng not in visited:
visited.add(rng)
Output.append((rng, magnitude))
'''
