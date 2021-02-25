from Message import *
from Log import *
from LCD import *
import lcd160cr
import pyb
# from machine import WDT
from pyb import UART

# global byte_buf
# global nextbyte
from Log import BinaryECEFLog
from LCD import showSVINStatus

stat = None
pack_buf = []
nextpack = None
pl_length_rem = 0  # will be assigned when first packet found
until_len = None  # will be assigned when first packet found
calibrated = False

gpsIn = UART(6, 38400)
gpsIn.init(38400, bits=8, parity=None, stop=1, read_buf_len=512, timeout=1500) # timeout should overlap epochs -> 1s atm

BUF_SIZ = 4

# wdt = WDT(timeout=10000)
TIME_CONF_LIMIT = 24 # number of hours before time-resync
timeConfidence = 0 # update time on 0 ==> on reset or start time is set

print("Starting...")
initLCD()
PAGE = 0 # used for LCD display

msg_buf = {}
msg_count = 0

## MUST BE SET FROM 0 -> NO_MSGS ##
# determines location in each epoch list - don't change!
LOC_CODE = 0
STAT_CODE = 1
SATINF_CODE = 2
TIMEUTC_CODE = 3

LOG_RAW = False
LOG_MEDIAN = True
LOG_BEST = True

NO_READINGS = 50  # number of positions used in one reading
NO_MSGS = 4  # number of messages per epoch (HPECEF, SAT, STATUS) = 3
MSG_PERIOD = 8 * 60 * 60  # every eight hours, min. 1 minute (50 readings taken with a delay of 1s between them)
if MSG_PERIOD < 60:
    MSG_PERIOD = 60

MSG_START_TIME
clock = pyb.RTC()
clock.wakeup(MSG_PERIOD, getReadings)

b = pyb.Switch()
b.callback(buttonPress)


def calibrate():
    print("Calibrating")
    start_bit_one = False
    start_bit_two = False
    while not (start_bit_one and start_bit_two):
        curr = gpsIn.read(1)
        if curr == b'\xb5':
            start_bit_one = True
        elif curr == b'\x62':
            start_bit_two = True
        else:
            start_bit_one = False
            start_bit_two = False
    print("Calibration Finished")


def readBytes():
    global nextpack, pack_buf, calibrated
    calibrated = gpsIn.read(2) == b'\xb5\x62'
    if not calibrated:
        calibrate()
        calibrated = True
    nextpack = bytearray(b'\xb5\x62')
    class_id = gpsIn.read(2)
    # pack_len_bytes = uart.read(2)
    pack_len_bytes = gpsIn.read(2)
    pack_len = int.from_bytes(pack_len_bytes, 'little')
    # print(pack_len_bytes,pack_len, "bytes long")
    if pack_len > 100:
        print(pack_len)
        return
    payload = gpsIn.read(pack_len)
    crc = gpsIn.read(2)
    if crc is None:
        crc = b'\x00\x00'
    # print(crc,"crc")
    try:
        # print(class_id)
        nextpack.extend(class_id)  # append class and ID to byte
        nextpack.extend(pack_len_bytes)
        nextpack.extend(payload)
        nextpack.extend(crc)
        pack_buf.append(nextpack)
    except:
        print("Error:")
        print(class_id)
        print(pack_len)
        print(payload)
        print(crc)
        print("End error")
        # log error?
    nextpack = None


def readIn():
    global x, y, z, pacc, lat, lon, h, sats, fix, lathp, lonhp, lastLLH, lastTime, lastDateObject, lastStat, survey
    if len(pack_buf) == 0:
        return None

    byte_stream = pack_buf[0]
    del pack_buf[0]

    read_status = "Unparsed"

    msg = parseUBXMessage(byte_stream)
    if isinstance(msg, HPECEF):
        x = msg.ecefX
        y = msg.ecefY
        z = msg.ecefZ
        pacc = msg.pAcc
        read_status = "HPECEF msg, x=" + str(msg.ecefX)
    elif isinstance(msg, HPLLH):
        lastLLH = msg
        lat = msg.lat
        lathp = msg.latHp
        lon = msg.lon
        lonhp = msg.lonHp
        h = msg.height
        read_status = "HPLLH msg, lat=" + str(msg.lat)
    elif isinstance(msg, ECEF):
        if x is None:
            x = msg.ecefX
        if y is None:
            y = msg.ecefY
        if z is None:
            z = msg.ecefZ
        if pacc is None:
            pacc = msg.pAcc
        read_status = "ECEF msg, x=" + str(msg.ecefX)
    elif isinstance(msg, LLH):
        # lastLLH=msg
        if lat is None:
            lat = msg.lat
        if lon is None:
            lon = msg.lon
        if h is None:
            h = msg.height
        read_status = "LLH msg, lat=" + str(msg.lat)
    elif isinstance(msg, Status):
        lastStat = msg
        fix = msg.gpsFix
        read_status = "Status msg, fix=" + str(msg.gpsFix)
    elif isinstance(msg, SatInfo):
        sats = msg.numSvs
        read_status = "Sat info, no. sats=" + str(msg.numSvs)
    elif isinstance(msg, Solution):
        if x is None:
            x = msg.ecefX
        if y is None:
            y = msg.ecefY
        if z is None:
            z = msg.ecefZ
        if pacc is None:
            pacc = msg.pAcc
        if fix is None:
            fix = msg.gpsFix
        if sats is None:
            sats = msg.numSv
        read_status = "Solution information, pdop=" + str(msg.pDOP)
    elif isinstance(msg, TimeUTC):
        lastTime = msg
        read_status = "TimeUTC message, hour=" + str(msg.hour)
        # print("found time message "+str(msg.hour))
        # pyb.delay(2000)
    elif isinstance(msg, SVIN):
        survey = msg
        read_status = "Survey-in: " + str(msg.active)
    return read_status


# 0 -> High-precision ECEF data
# 1 -> GPS Status (ttff, fix status, etc.)
# 2 -> Satellite information (notably the number of satellites used)
# 3 -> Survey-in data (base station)
def getMessageFromBuffer():
    global msg_buf, msg_count, LOC_CODE, STAT_CODE, SATINF_CODE, NO_MSGS
    if len(pack_buf) == 0:
        return None, -1

    byte_stream = pack_buf[0]
    del pack_buf[0]

    msg = binaryParseUBXMessage(byte_stream)
    tow = msg.getTOW()
    print(len(msg_buf))
    if tow not in msg_buf:
        msg_buf[tow] = [None] * NO_MSGS

    if isinstance(msg, HPECEF):
        code = LOC_CODE
    elif isinstance(msg, Status):
        code = STAT_CODE
    elif isinstance(msg, SatInfo):
        code = SATINF_CODE
    # SVIN should only come in on base station, leaving code here for ease of copying, could also make code more
    # deployable by copying gps-read code?
    # elif isinstance(msg, SVIN):
    #     return msg, 3
    else:
        code = -1

    msg_count += 1
    msg_buf[tow][code] = msg
    return msg, code


def getReadings():
    global msg_buf, msg_count, NO_READINGS, STAT_CODE, timeConfidence, MSG_PERIOD
    while msg_count < NO_READINGS * NO_MSGS:
        readBytes()
        msg, id = getMessageFromBuffer()
        if id == STAT_CODE:
            validFix = msg.gpsFixOK
            if not validFix:
                msg_count -= 1
                del msg_buf[msg.iTOW]

    # clock will drift as time continues, update time when this reaches 0 (see TIME_CONF_LIMIT for hours before reset)
    timeConfidence -= MSG_PERIOD
    chosen_msg = None
    if LOG_MEDIAN:
        chosen_msg = getMedianMsg(msg_buf)
        type_code = b'\x01'

    if LOG_BEST:
        # take message with smallest pAcc --> most accurate of the readings
        chosen_msg = getBestAcc(msg_buf)
        type_code = b'\x02'

    if LOG_RAW:
        # take last message
        chosen_msg = msg_buf[max(msg_buf)]
        type_code = b'\x00'

    if chosen_msg is not None:
        location = chosen_msg[LOC_CODE]
        log = BinaryECEFLog()
        log.tow = location.iTOW  # want to keep the binary here - getTOW() implicitly converts to int
        log.setECEFData(location)  # works ONLY if we use binaryParseUBXMessage - needs reprogramming to ECEFLog or use
        # conversion functions
        log.setSvs(chosen_msg[SATINF_CODE])
        log.setDataType(type_code)
        writeLog(log)

    transmitLogs()
    updateLCD()
    updateLEDs()
    msg_buf = []
    msg_count = 0
    # pyb.stop() # put in sleep mode when all done


def updateTime(timeMsg):
    global clock, timeConfidence, TIME_CONF_LIMIT
    if type(timeMsg) is not TimeUTC or timeMsg.validTime() or timeConfidence > 0:
        return

    timeConfidence = TIME_CONF_LIMIT
    # assume Monday as gps doesn't give this data hence weekday=0
    clock.datetime(timeMsg.getYear(), timeMsg.getMonth(), timeMsg.getDay(), 1,
                   timeMsg.getHour(), timeMsg.getMinute(), timeMsg.getSeconds(), timeMsg.getNano())


def writeLog(log):
    global logFile
    print("Writing log:", end=" ")
    print(log.getLogString())
    logFile = open("location.log", "a")
    logFile.write(log.getLogString())
    logFile.flush()
    logFile.close()


# 300 readings - for loop?
# long timeout - .5s to keep in 1s epoch?
#

# RTC.wakeup(timeout, callback)
# can be used to do frequent events (callback might be typed badly idk)
# means we can wakeup from pyb.stop() (500uA) and immediately call a few iterations of main()

def getAverageLocation(msgs):
    global LOC_CODE, STAT_CODE, SATINF_CODE
    if len(msgs) == 0:
        return 0, 0, 0, 0, 0, 0, 0, 0
    tot_x = 0.
    tot_y = 0.
    tot_z = 0.
    tot_xhp = 0.
    tot_yhp = 0.
    tot_zhp = 0.
    tot_sats = 0.
    tot_acc = 0.
    for msgSet in msgs:
        loc_msg, stat_msg, satinf_msg = msgSet
        tot_x += loc_msg.ecefX
        tot_y += loc_msg.ecefY
        tot_z += loc_msg.ecefZ
        tot_xhp += loc_msg.ecefXHp
        tot_yhp += loc_msg.ecefYHp
        tot_zhp += loc_msg.ecefZHp
        tot_sats += satinf_msg.getNumSvs()
        tot_acc += loc_msg.getPAcc()

    tot_x /= len(msgs)
    tot_y /= len(msgs)
    tot_z /= len(msgs)
    tot_xhp /= len(msgs)
    tot_yhp /= len(msgs)
    tot_zhp /= len(msgs)
    tot_sats /= len(msgs)
    tot_acc /= len(msgs)

    return msgSet[0].iTOW, tot_x, tot_y, tot_z, tot_xhp, tot_yhp, tot_zhp, tot_acc, tot_sats


# allow for further implementation of LR comms - UART?
def transmitLogs():
    print("Might be transmitting..?")
    # original intent was to transmit once per day, so could accumulate value
    # based on period and number of logs taken
    # implementation could be abstracted to UART or SPI output -> currently no plan to use real satellite link


# not needed for now
def updateLCD():
    global page
    if page == 0:
        pass


# might be useful for visual status - green on fix etc.
def updateLEDs():
    pass


# while True:
#     msg = getMessage()
#     updateTime(msg)
#     getLocation(msg)
#     logLocation(msg)
#     transmitLocation(msg)
#     updateLCD()

def resetCallback():
    global rtc
    rtc.wakeup(None)


def triggerWakeup():
    print("Waiting for read...")
    rtc.wakeup(30 * 1000, readLoc)


def getAvgMsg(msgs):
    global LOC_CODE, STAT_CODE, SATINF_CODE
    if len(msgs) == 0:
        return 0, 0, 0, 0, 0, 0, 0, 0
    tot_x = 0.
    tot_y = 0.
    tot_z = 0.
    tot_xhp = 0.
    tot_yhp = 0.
    tot_zhp = 0.
    tot_acc = 0.

    for loc_msg in msgs:
        tot_x += loc_msg.getX()
        tot_y += loc_msg.getY()
        tot_z += loc_msg.getZ()
        tot_xhp += loc_msg.getXHP()
        tot_yhp += loc_msg.getYHP()
        tot_zhp += loc_msg.getZHP()
        tot_acc += loc_msg.getPAcc()

    tot_x /= len(msgs)
    tot_y /= len(msgs)
    tot_z /= len(msgs)
    tot_xhp /= len(msgs)
    tot_yhp /= len(msgs)
    tot_zhp /= len(msgs)
    tot_acc /= len(msgs)
    return HPECEF(msgs[0].iTOW, tot_x, tot_y, tot_z, tot_xhp, tot_yhp, tot_zhp, tot_acc, 0)


def getAcc(msgSet):
    global LOC_CODE
    return msgSet[LOC_CODE].getPAcc()


def getPos(msg):
    return msg.get3DPos()


def getEuclidiean(msgTriple):
    msg = msgTriple[0]
    px, py, pz = msg.get3DPos()
    return px ** 2 + py ** 2 + pz ** 2


# SHOULD return a list of messages with indexes matching the codes
def getMedianMsg(msgs):
    sorted_msg_values = {key: value for key, value in
                         sorted(msgs.items(), key=lambda item: getEuclidiean(item))}.values()
    halfway_point = (len(sorted_msg_values) + 1) / 2 - 1
    # easier to choose left value rather than average between the two
    med = sorted_msg_values[int(halfway_point)]
    return med


def getBestAcc(msgs):
    msgs = sorted(msgs.values(), key=getAcc)
    return msgs[0]


def readLoc(i):
    global LOC_CODE, s, msg_buf
    resetCallback()
    print("READING LOCATION")
    msg = None
    msgs = []
    msg_buf = {}
    NO_MSGS = 51
    for i in range(NO_MSGS):
        id = -1
        while id != LOC_CODE:
            readBytes()
            msg, id = getMessageFromBuffer()

        print(msg.get3DPos(), msg.getPAcc())
        msgs.append(msg)

    # tow, x, y, z, xhp, yhp, zhp, pacc, flags
    normal = msgs[0]
    mean = getAvgMsg(msgs)
    median = getMedianMsg(msgs)
    best = getBest(msgs)

    print("OUT LOOP", len(msgs))
    if id == LOC_CODE:
        print(normal == mean, normal == median, normal == best)
        print(mean == median, mean == best)
        print(median == best)
        writeMsgToFile(normal, "normalResults.csv")
        writeMsgToFile(mean, "meanResults.csv")
        writeMsgToFile(median, "medianResults.csv")
        writeMsgToFile(best, "bestResults.csv")

    drawSquares()
    s += .1
    print("Written")


def writeMsgToFile(msg, fn):
    global s
    x, y, z = msg.get3DPos()
    # loc = str(s) + "," + str(x) + "," + str(y) + "," + str(z) + "," + str(msg.getPAcc())
    loc = "{0:.2f},{1:.2f},{2:.2f},{3:.2f},{4:.2f}".format(s, x, y, z, msg.getPAcc())
    print(loc)
    outpfile = open(fn, "a")
    outpfile.write(loc + "\n")
    outpfile.flush()
    outpfile.close()

# while True:
#     print("---")
#     readBytes()
#     # wdt.feed()
#     # returns a string repr message plus assigns global vars
#     # -- need to split into mul functions
#     status = readIn()
#
#     showSVINStatus(survey)
#
#     # # prints out what message was found
#     # if status is not None:
#     #     print(status)
#     #     # pass
#     # if (len(pack_buf)) > BUF_SIZ:
#     #     # if too many messages, discard current buffer to prefer newer messages
#     #     print(pack_buf)
#     #     pack_buf = []
#
#     if lastTime is not None and lastLLH is not None:
#         lastDateObject = DateTime(lastTime)
#         curHour = lastDateObject.hour
#         if curHour in loggedHours and not loggedHours[curHour]:
#             writeLog()
#             loggedHours[curHour] = True
#
#             # reset other hours to allow further logging
#             for time in loggedHours:
#                 if time is not curHour:
#                     loggedHours[time] = False
#         elif curHour in loggedHours:
#             print("Already logged this hour")
#
#     llhStatus()
#     print("Distance:", getDistance(x, y, z))
#
#     #
