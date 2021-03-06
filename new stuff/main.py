from Message import *
import Log
import LCD
import lcd160cr
import pyb
# from machine import WDT
from pyb import UART

# global byte_buf
# global nextbyte

stat = None
pack_buf = []
nextpack = None
pl_length_rem = 0  # will be assigned when first packet found
until_len = None  # will be assigned when first packet found
calibrated = False

gpsIn = UART(6, 38400)
gpsIn.init(38400, bits=8, parity=None, stop=1, read_buf_len=512,
           timeout=1200)  # timeout should overlap epochs -> 1s atm

BUF_SIZ = 4

# wdt = WDT(timeout=10000)
TIME_CONF_LIMIT = 24 * 60 * 60  # number of readings before time-resync
timeConfidence = 0  # update time on 0 ==> on reset or start time is set

msg_buf = {}
msg_count = 0

monitoring = False

## MUST BE SET FROM 0 -> NO_MSGS ##
# determines location in each epoch list - don't change!
LOC_CODE = 0
STAT_CODE = 1
SATINF_CODE = 2
TIMEUTC_CODE = 3
SVIN_CODE = 4

LOG_RAW = False
LOG_MEDIAN = True
LOG_BEST = True
UPDATE_DELAY = 100

NO_READINGS = 5  # number of positions used in one reading
NO_MSGS = 3  # ROVER: number of messages per epoch (HPECEF, SAT, STATUS) = 3 --> NOTE that TIMUTC is used then discarded once time is updated
MAX_READING_ATTEMPTS = 100 # prevents livelock in case no message triples are valid
# NO_MSGS = 5 # BASE STATION: number of messages per epoch (HPECEF, SAT, STATUS, TIMEUTC, SVIN) = 5
# MSG_PERIOD = 8 * 60 * 60  # (in seconds) every eight hours - min. 1 minute (50 readings taken with a delay of 1s
# between them)
MSG_PERIOD = 120  # two-minute debug mode
if MSG_PERIOD < 60:
    MSG_PERIOD = 60
MSG_PERIOD *= 1000  # convert from s to ms

MSG_START_TIME = 12  # defines the first hour in which the readings will take place. no sub-hour accuracy as intended
# use is for < 10 readings per day

print("Starting...")
LCD.initLCDAPI(MSG_PERIOD, MSG_START_TIME, LOG_RAW, LOG_MEDIAN, LOG_BEST, False)
PAGE = 0  # used for LCD display


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
    pack_len = U2(pack_len_bytes)
    # print(pack_len_bytes,pack_len, "bytes long")

    if pack_len > 100 and class_id != bytearray(b'\x01\x35'):
        print(pack_len, "invalid length")
        return
    elif class_id == bytearray(b'\x01\x35'):
        print("Sat message, length capped")
        pack_len = 8
        pack_len_bytes = u2toBytes(pack_len)
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
    except Exception as e:
        print(e)
        print("Error:")
        print(class_id)
        print(pack_len_bytes)
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
    global pack_buf, msg_buf, LOC_CODE, STAT_CODE, SATINF_CODE, NO_MSGS
    if len(pack_buf) == 0:
        return None, -1

    byte_stream = pack_buf[0]
    del pack_buf[0]
    # print(byte_stream)
    msg = binaryParseUBXMessage(byte_stream)
    if msg is None:
        return None, -1

    tow = msg.getTOW()
    print(len(msg_buf), "messages in buffer")
    if tow not in msg_buf:
        msg_buf[tow] = [None] * NO_MSGS
    code = -1
    if isinstance(msg, HPECEF):
        code = LOC_CODE
    elif isinstance(msg, Status):
        code = STAT_CODE
    elif isinstance(msg, SatInfo):
        code = SATINF_CODE
    elif isinstance(msg, TimeUTC):
        print("TIME message incoming")
        updateTime(msg)
    # SVIN should only come in on base station, leaving code here for ease of copying, could also make code more
    # deployable by copying gps-read code?
    # elif isinstance(msg, SVIN):
    #     return msg, 3
    else:
        code = -1

    if code != -1:  # just in case msg is not being used -> TIMEUTC? maybe another message has been enabled by accident i.e. LLH
        msg_buf[tow][code] = msg
    return msg, code


reading = False


def getReadings(i=0):
    global msg_buf, msg_count, NO_READINGS, STAT_CODE, timeConfidence, MSG_PERIOD, reading
    reading = True
    LCD.makeLCDBusy()
    msg_count = 0
    msg_buf = {}
    lastepoch = 0
    chosen_msgs = []
    ttl = MAX_READING_ATTEMPTS # time to live, prevents livelock
    while msg_count < (NO_READINGS + 1) * NO_MSGS + 1 and ttl > 0:
        ttl -= 1
        readBytes()
        msg, id = getMessageFromBuffer()
        if msg is None:
            continue
        curepoch = msg.getTOW()
        if curepoch != lastepoch and lastepoch != 0:
            print("------ ### ------")
            # if any messages are missing from last epoch, delete data from that epoch as unreliable (incomplete metadata)
            if any(map(lambda r: r is None, msg_buf[lastepoch])) or len(msg_buf[lastepoch]) < NO_MSGS:
                msg_count -= sum(map(lambda r: r is not None, msg_buf[lastepoch]))
                print("Some messages none on turn of next epoch, deleting epoch...")
                del msg_buf[lastepoch]
                lastepoch = 0
            elif LOG_RAW:
                # safe to log as raw data
                chosen_msgs.append((b'\xF1', msg_buf))
        print(msg, id, msg_count)
        lastepoch = curepoch
        invalidFix = id == STAT_CODE and not msg.gpsFixOK or id == LOC_CODE and msg.invalidFix
        if invalidFix:
            msg_count -= id
            del msg_buf[msg.iTOW]
            print("Invalid fix, deleting msg", msg_buf, msg_count, id == STAT_CODE and not msg.gpsFixOK, id == LOC_CODE and msg.invalidFix)
        else:
            msg_count += 1

    del msg_buf[curepoch] # trim last epoch from buffer
    # clock will drift as time continues, update time when this reaches 0 (see TIME_CONF_LIMIT for readings before reset)
    timeConfidence -= msg_count
    if LOG_MEDIAN:
        print(msg_buf, msg_count)
        type_code = b'\xF1'
        chosen_msgs.append((type_code, getMedianMsg(msg_buf)))

    if LOG_BEST:
        # take message with smallest pAcc --> most accurate of the readings
        type_code = b'\xF2'
        chosen_msgs.append((type_code, getBestAcc(msg_buf)))

    if len(chosen_msgs) > 0:
        for t, m in chosen_msgs:
            location = m[LOC_CODE]
            sats = m[SATINF_CODE]
            log = Log.ECEFLog(location, t, sats)
            n = log.writeLog()
            print(n, "bytes written to file")
            # log = BinaryECEFLog()
            # log.tow = location.iTOW  # want to keep the binary here - getTOW() implicitly converts to int
            # log.setECEFData(location)  # works ONLY if we use binaryParseUBXMessage - needs reprogramming to ECEFLog or use
            # # conversion functions
            # log.setSvs(msg[SATINF_CODE])
            # log.setDataType(type_code)
            # writeLog(log)

    transmitLogs()
    updateLCD()
    updateLEDs()
    msg_buf = {}
    msg_count = 0
    LCD.makeLCDFree()
    reading = False
    # pyb.stop() # put in sleep mode when all done


def updateTime(timeMsg):
    global clock, timeConfidence, TIME_CONF_LIMIT
    if type(timeMsg) is not TimeUTC or not timeMsg.validTime() or timeConfidence > 0:
        print("No clock update: ", timeConfidence)
        timeConfidence -= 1
        return
    print("!!! Updating clock !!!")
    timeConfidence = TIME_CONF_LIMIT
    # assume Monday as gps doesn't give this data hence weekday=0
    print((timeMsg.getYear(), timeMsg.getMonth(), timeMsg.getDay(), 1,
           timeMsg.getHour(), timeMsg.getMinute(), timeMsg.getSeconds(), timeMsg.getNano()))
    clock.datetime((timeMsg.getYear(), timeMsg.getMonth(), timeMsg.getDay(), 1,
                    timeMsg.getHour(), timeMsg.getMinute(), timeMsg.getSeconds(), timeMsg.getNano()))


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
    global UPDATE_DELAY
    LCD.updateLCD(UPDATE_DELAY)


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
    msg = msgTriple[1][0]
    print(msgTriple, msg)
    px, py, pz = msg.get3DPos()
    return px ** 2 + py ** 2 + pz ** 2


# SHOULD return a list of messages with indexes matching the codes
def getMedianMsg(msgs):
    print(msgs)
    sorted_msg_values = list({key: value for key, value in
                         sorted(msgs.items(), key=lambda item: getEuclidiean(item))})
    halfway_point = (len(sorted_msg_values) + 1) / 2 - 1
    # easier to choose left value rather than average between the two
    print(halfway_point, int(halfway_point), sorted_msg_values)
    med = msgs[sorted_msg_values[int(halfway_point)]]
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

        # print(msg.get3DPos(), msg.getPAcc())
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


# resets clock to use actual period synced up to the time specified
def intialReading(i=0):
    global MSG_PERIOD, clock
    getReadings()  # take readings immediately
    clock.wakeup(MSG_PERIOD, getReadings)


# used to synchronise the readings with the clock
def initialTimer():
    global MSG_START_TIME, MSG_PERIOD, clock
    if timeConfidence != 0:
        time = clock.datetime()
        hour = time[4]
        diff = (hour - MSG_START_TIME) * 60 * 60
        if diff == 0 or diff % MSG_PERIOD == 0:
            clock.wakeup(MSG_PERIOD, initialReading)
            print("Wakeup in", MSG_PERIOD)
        elif diff < 0:
            clock.wakeup(abs(diff), initialReading)
            print("Wakeup in", abs(diff))
        elif diff > 0:
            nextLogTime = MSG_START_TIME
            while diff > 0:
                nextLogTime += MSG_PERIOD
                diff = hour - nextLogTime
            clock.wakeup(abs(diff), initialReading)
            print("Wakeup in", abs(diff))
    else:
        print("No time confidence")


clock = pyb.RTC()
# clock.wakeup(1000, initialTimer()) # start checking each second if time accurate, then start reading properly
# main loop
svs = 0
while True:
    if not reading:  # don't update LCD if taking a reading
        monitoring = LCD.monitoring
        if monitoring:
            # get a locaiton message from buffer
            msg_buf = {}  # reset to stop memory leaks - shouldn't interfere with periodic reading as won't be reachable during
            readBytes()
            msg, code = getMessageFromBuffer()
            if code == LOC_CODE:
                print("Updating location data")
                LCD.updateLocMonitorData(msg, svs)
            elif code == SVIN_CODE:
                print("Updating survey data")
                LCD.updateSVINMonitorData(msg)
            elif code == SATINF_CODE:
                print("SAT DATA INCOMING")
                svs = msg.getNumSvs()
        print("Updating LCD")
        updateLCD()
        pyb.delay(UPDATE_DELAY)
    pyb.wfi()  # put in low-power mode to reduce power consumption

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
