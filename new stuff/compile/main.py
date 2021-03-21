from random import randint

import pyb
import json
# from machine import WDT
from pyb import UART

import LCD
import Log
from Message import *
from Formats import *
import os

stat = None
pack_buf = []
nextpack = None
pl_length_rem = 0  # will be assigned when first packet found
until_len = None  # will be assigned when first packet found
calibrated = False

DEVICE_ID = 0
GPS_UART_PORT = 6
GPS_BAUDRATE = 38400
GPS_TIMEOUT = 1001 # ms
GPS_BUF_SIZ = 512 # bytes
IS_BASE_STATION = False
SVIN_DUR = 600 # 5 min
SVIN_ACC = 10000 # 10m

# gpsIn = UART(6, 38400)
# gpsIn.init(38400, bits=8, parity=None, stop=1, read_buf_len=512,
#            timeout=1001)  # timeout should overlap epochs -> 1s atm

# wdt = WDT(timeout=10000)
TIME_CONF_LIMIT = 500  # number of readings before time-resync
timeConfidence = 0  # update time on 0 ==> on reset or start time is set

msg_buf = {}
msg_count = 0

monitoring = False

## MUST BE SET FROM 0 -> NO_MSGS ##
# determines location in each epoch list - don't change!
# LOC_CODE = 0
# STAT_CODE = 1
# SATINF_CODE = 2
# TIMEUTC_CODE = 3
# SVIN_CODE = 4
# set to -2 to disable (since -1 is used for no message, could cause accidental matches)
LOC_CODE = -2
STAT_CODE = -2
SATINF_CODE = -2
SVIN_CODE = -2
TIMEUTC_ENABLED = True

LOG_RAW = False
LOG_MEDIAN = True
LOG_BEST = True
UPDATE_DELAY = 125 # works best if harmonises with 1000ms i.e. 250, 500, 125, etc.

NO_READINGS = 5  # number of positions used in one reading
NO_MSGS = 4  # ROVER: number of messages per epoch (HPECEF, SAT, STATUS) = 3 --> NOTE that TIMUTC is used then discarded once time is updated
MAX_READING_ATTEMPTS = 100 # prevents livelock in case no message triples are valid
CALIBRATION_TTL = 1000 # maximum number of bytes that will be read in one calibration before timeout
MAX_CALIBRATE_FAILURES = 50 # number of UART timeouts until calibration attepts stopped
# NO_MSGS = 5 # BASE STATION: number of messages per epoch (HPECEF, SAT, STATUS, TIMEUTC, SVIN) = 5
# MSG_PERIOD = 8 * 60 * 60  # (in seconds) every eight hours - min. 1 minute (50 readings taken with a delay of 1s
# between them)
MSG_PERIOD = 120  # two-minute debug mode
# MSG_PERIOD = 28800  # two-minute debug mode
if MSG_PERIOD < 60:
    MSG_PERIOD = 60
MSG_PERIOD *= 1000  # convert from s to ms

MSG_START_TIME = 12  # defines the first hour in which the readings will take place. no sub-hour accuracy as intended
                     # use is for < 10 readings per day
TRANSMIT_AFTER = 3 # 12am
MAX_TRANSMIT_ATTEMPTS = 3 # defines how many times a file will be transmitted before deletion

gpsIn = None

def loadBaseStationParams(data):
    global IS_BASE_STATION, SVIN_ACC, SVIN_DUR
    IS_BASE_STATION = True
    if 'svin_acc' in data:
        SVIN_ACC = data['svin_acc']
    if 'svin_dur' in data:
        SVIN_DUR = data['svin_dur']

def loadLogParams(data):
    global LOC_CODE, STAT_CODE, SATINF_CODE, TIMEUTC_ENABLED, SVIN_CODE, NO_MSGS, NO_READINGS, MAX_READING_ATTEMPTS, LOG_RAW, LOG_MEDIAN, LOG_BEST
    if 'no_readings' in data:
        NO_READINGS = data['no_readings']
    if 'max_reading_attempts' in data:
        MAX_READING_ATTEMPTS = data['max_reading_attempts']
    if 'log_raw' in data:
        LOG_RAW = data['log_raw']
    if 'log_median' in data:
        LOG_MEDIAN = data['log_median']
    if 'log_best' in data:
        LOG_BEST = data['log_best']
    if 'msgs_enabled' in data:
        msgs = data['msgs_enabled']
        c = 0
        for msg_type in msgs:
            if msgs[msg_type]:
                if msg_type == 'HPECEF':
                    LOC_CODE = c
                elif msg_type == 'STATUS':
                    STAT_CODE = c
                elif msg_type == 'SAT_INFO':
                    SATINF_CODE = c
                elif msg_type == 'TIMEUTC':
                    TIMEUTC_ENABLED = True
                    c -= 1
                elif msg_type == 'SVIN':
                    SVIN_CODE = c
                c += 1
                print(LOC_CODE, STAT_CODE, SATINF_CODE,     SVIN_CODE, c)
        NO_MSGS = c


def loadTimeParams(data):
    global MSG_PERIOD, MSG_START_TIME, TIME_CONF_LIMIT, UPDATE_DELAY, TRANSMIT_AFTER, MAX_TRANSMIT_ATTEMPTS
    if 'log_period_s' in data:
        MSG_PERIOD = data['log_period_s']
    if 'log_start' in data:
        MSG_START_TIME = data['log_start']
    if 'update_rtc_time' in data:
        TIME_CONF_LIMIT = data['update_rtc_time']
    if 'update_delay' in data:
        UPDATE_DELAY = data['update_delay']
    if 'transmit_after' in data:
        TRANSMIT_AFTER = data['transmit_after']
    if 'transmit_attempts' in data:
        MAX_TRANSMIT_ATTEMPTS = data['transmit_attempts']

def loadUARTParams(data):
    global GPS_UART_PORT, GPS_BAUDRATE, GPS_TIMEOUT, CALIBRATION_TTL, GPS_BUF_SIZ, gpsIn, DEVICE_ID, MAX_CALIBRATE_FAILURES
    if 'device_id' in data:
        DEVICE_ID = data['device_id']
    if 'gps_uart' in data:
        GPS_UART_PORT = data['gps_uart']
    if 'gps_baudrate' in data:
        GPS_BAUDRATE = data['gps_baudrate']
    if 'gps_timeout' in data:
        GPS_TIMEOUT = data['gps_timeout']
    if 'gps_buffer_size' in data:
        GPS_BUF_SIZ = data['gps_buffer_size']
    if 'calibration_ttl' in data:
        CALIBRATION_TTL = data['calibration_ttl']
    if 'max_calibration_fail' in data:
        CALIBRATION_TTL = data['max_calibration_fail']
    gpsIn = UART(GPS_UART_PORT, GPS_BAUDRATE)
    gpsIn.init(GPS_BAUDRATE, bits=8, parity=None, stop=1, read_buf_len=GPS_BUF_SIZ,
               timeout=GPS_TIMEOUT)  # timeout should overlap epochs -> 1s atm

def getParamsFromConfig():
    try:
        with open("config.json") as f:
            data = json.load(f)
        # print(data)
        baseStation = 'base_station' in data and data['base_station']
        if baseStation:
            loadBaseStationParams(data)

        loadLogParams(data)
        loadTimeParams(data)
        loadUARTParams(data)
    except:
        print("Error, using default parameters")


def calibrate():
    global CALIBRATION_TTL
    print("Calibrating...", end=" ")
    start_bit_one = False
    start_bit_two = False
    ttl = CALIBRATION_TTL
    remaining_failures = MAX_CALIBRATE_FAILURES
    while not (start_bit_one and start_bit_two) and ttl > 0 and remaining_failures > 0:
        curr = gpsIn.read(1)
        ttl -= 1
        if curr == b'\xb5':
            start_bit_one = True
        elif curr == b'\x62':
            start_bit_two = True
        elif curr is None:
            # uart timeout
            remaining_failures -= 1
        else:
            start_bit_one = False
            start_bit_two = False

    if ttl > 0 and remaining_failures > 0:
        print("Calibration Finished")
    else:
        print("Calibration timed out")
    return ttl > 0 and remaining_failures > 0


def readBytes():
    global nextpack, pack_buf, calibrated
    calibrated = gpsIn.read(2) == b'\xb5\x62'
    if not calibrated:
        calibrated = calibrate()
        Log.CalibrateEvent().writeLog()
    if not calibrated:
        Log.CalibrationTimeoutEvent().writeLog()
        return False
    nextpack = bytearray(b'\xb5\x62')
    class_id = gpsIn.read(2)
    # pack_len_bytes = uart.read(2)
    pack_len_bytes = gpsIn.read(2)
    pack_len = U2(pack_len_bytes)
    # print(pack_len_bytes,pack_len, "bytes long")

    if pack_len > 100 and class_id != bytearray(b'\x01\x35'):
        Log.UnacceptableLengthError().writeLog()
        return False
    elif class_id == bytearray(b'\x01\x35'):
        print("Sat message, length capped")
        Log.LengthForceError(b'\x01', b'\x35', pack_len_bytes, u2toBytes(8)).writeLog()
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
        Log.UnknownError().writeLog()
        print(e)
        print("Error:")
        print(class_id)
        print(pack_len_bytes)
        print(payload)
        print(crc)
        print("End error")
        # log error?
    nextpack = None
    return True


# 0 -> High-precision ECEF data
# 1 -> GPS Status (ttff, fix status, etc.)
# 2 -> Satellite information (notably the number of satellites used)
# 3 -> Survey-in data (base station)
def getMessageFromBuffer():
    global pack_buf, msg_buf, LOC_CODE, STAT_CODE, SATINF_CODE, NO_MSGS, TIMEUTC_ENABLED
    if len(pack_buf) == 0:
        return None, -1

    byte_stream = pack_buf[0]
    del pack_buf[0]
    # print(byte_stream)
    msg = None
    try:
        msg = binaryParseUBXMessage(byte_stream)
    except:
        Log.UnknownError("when parsing ubx message from bytestream")

    if msg is None:
        return None, -1

    tow = msg.getTOW()
    # print(len(msg_buf), "messages in buffer")
    if tow not in msg_buf:
        msg_buf[tow] = [None] * NO_MSGS
    code = -1
    if isinstance(msg, HPECEF) and LOC_CODE >= 0:
        code = LOC_CODE
    elif isinstance(msg, Status) and STAT_CODE >= 0:
        code = STAT_CODE
    elif isinstance(msg, SatInfo) and SATINF_CODE >= 0:
        code = SATINF_CODE
    elif isinstance(msg, TimeUTC) and TIMEUTC_ENABLED:
        updateTime(msg)
    # SVIN should only come in on base station, leaving code here for ease of copying, could also make code more
    # deployable by copying gps-read code?
    elif isinstance(msg, SVIN) and SVIN_CODE >= 0:
        return msg, SVIN_CODE
    else:
        code = -1

    if code != -1:  # just in case msg is not being used -> TIMEUTC? maybe another message has been enabled by accident i.e. LLH
        msg_buf[tow][code] = msg
    return msg, code


reading = False

# tells us if the last epoch was corrupted by:
# - not enough messages read from gps
# - some messages invalid from last epoch
def invalidEpoch(epoch_msgs):
    global NO_MSGS, STAT_CODE, LOC_CODE
    return any(map(lambda r: r is None, epoch_msgs)) or len(epoch_msgs) < NO_MSGS or not epoch_msgs[
        STAT_CODE].gpsFixOK or epoch_msgs[LOC_CODE].invalidFix


def getReadings(i=0):
    global msg_buf, msg_count, NO_READINGS, STAT_CODE, timeConfidence, MSG_PERIOD, reading
    # shoudln't read twice at same time
    if reading:
        print("Duplicate call?")
        return
    reading = True
    LCD.makeLCDBusy()
    msg_count = 0
    msg_buf = {}
    curepoch = 0
    lastepoch = 0
    chosen_msgs = []
    ttl = MAX_READING_ATTEMPTS # time to live, prevents livelock
    while msg_count < (NO_READINGS + 1) * NO_MSGS + 1 and ttl > 0:
        bytes_available = readBytes()
        if not bytes_available:
            ttl -= 1
            # add random delay to try to dislodge timeout / get more data in buffer
            pyb.delay(1000 + randint(1,999))
            continue # restart iteration with hopefully more bytes in buffer - ttl should stop if many attempts taken
        msg, id = getMessageFromBuffer()
        if msg is None:
            continue
        curepoch = msg.getTOW()
        if curepoch != lastepoch and lastepoch != 0:
            print("------ ### ------")
            # if any messages are missing from last epoch, delete data from that epoch as unreliable (incomplete metadata)
            lastepoch_msgs = msg_buf[lastepoch]
            if invalidEpoch(lastepoch_msgs):
                msg_count -= sum(map(lambda r: r is not None, lastepoch_msgs))
                print("Some messages none on turn of next epoch, deleting epoch...")
                print(lastepoch_msgs)
                del msg_buf[lastepoch]
                ttl -= 1
                lastepoch = curepoch # might not work? needs testing
                continue # skip count increment
            elif LOG_RAW:
                # safe to log as raw data
                Log.ECEFLog(lastepoch_msgs[LOC_CODE], b'\xF1', lastepoch_msgs[SATINF_CODE]).writeLog()
                Log.LocationEvent(b'\xF1').writeLog()  # write event log for location write
        # print(msg, id, msg_count)
        lastepoch = curepoch
        # original code for detecting location invalid -> moved to last epoch calculation
        # invalidFix = id == STAT_CODE and not msg.gpsFixOK or id == LOC_CODE and msg.invalidFix
        # if invalidFix:
        #     msg_count -= id
        #     del msg_buf[msg.iTOW]
        #     print("Invalid fix, deleting msg", msg_buf, msg_count, id == STAT_CODE and not msg.gpsFixOK, id == LOC_CODE and msg.invalidFix)
        #     Log.UnknownError("Invalid location deleted from buffer").writeLog()
        # else:
        msg_count += 1
    # 0 msgs will only happen if timeout
    if len(msg_buf) > 0:
        del msg_buf[curepoch] # trim last epoch from buffer
    timeConfidence -= msg_count

    # clock will drift as time continues, update time when this reaches 0 (see TIME_CONF_LIMIT for readings before
    # reset)
    if LOG_MEDIAN and len(msg_buf) > 0:
        # print(msg_buf, msg_count)
        type_code = b'\xF1'
        chosen_msgs.append((type_code, getMedianMsg(msg_buf)))

    if LOG_BEST and len(msg_buf) > 0:
        # take message with smallest pAcc --> most accurate of the readings
        type_code = b'\xF2'
        chosen_msgs.append((type_code, getBestAcc(msg_buf)))

    if len(chosen_msgs) > 0:
        print(chosen_msgs)
        for t, m in chosen_msgs:
            # print(t, m)
            location = m[LOC_CODE]
            sats = m[SATINF_CODE]
            Log.ECEFLog(location, t, sats).writeLog()
            Log.LocationEvent(t).writeLog() # write event log for location write

    transmitLogs()
    updateLCD()
    updateLEDs()
    msg_buf = {}
    msg_count = 0
    LCD.makeLCDFree()
    reading = False
    # pyb.stop() # put in sleep mode when all done ?

def forceReading():
    global clock
    print("\n\nForcing reading\n\n")
    clock.wakeup(None)
    getReadings()
    clock.wakeup(10000, initialTimer)


def updateTime(timeMsg):
    global clock, timeConfidence, TIME_CONF_LIMIT
    if type(timeMsg) is not TimeUTC or not timeMsg.validTime() or timeConfidence > 0:
        print("No clock update: ", timeConfidence)
        timeConfidence -= 1
        return
    print("!!! Updating clock !!!")
    Log.TimeUpdateEvent().writeLog()
    timeConfidence = TIME_CONF_LIMIT
    # assume Monday as gps doesn't give this data hence weekday=0
    clock.datetime((timeMsg.getYear(), timeMsg.getMonth(), timeMsg.getDay(), 1,
                    timeMsg.getHour(), timeMsg.getMinute(), timeMsg.getSeconds(), timeMsg.getNano()))


radio = UART(3,38400)
radio.init(38400,bits=8, parity=None, stop=1, read_buf_len=512,
               timeout=100)
t_attempts = 0
# 300 readings - for loop?
# long timeout - .5s to keep in 1s epoch?
#

# RTC.wakeup(timeout, callback)
# can be used to do frequent events (callback might be typed badly idk)
# means we can wakeup from pyb.stop() (500uA) and immediately call a few iterations of main()

# allow for further implementation of LR comms - UART?
def transmitLogs():
    global TRANSMIT_AFTER, MAX_TRANSMIT_ATTEMPTS, t_attempts
    # don't run if don't want to transmit for some reason
    if MAX_TRANSMIT_ATTEMPTS <= 0:
        return
    elif t_attempts >= TRANSMIT_AFTER:
        try:
            for file in Log.waiting_logs:
                with open(file+"log.bin", "rb") as f:
                    data = f.read()
                radio.write(data)
                Log.waiting_logs[file] += 1
                if Log.waiting_logs[file] >= MAX_TRANSMIT_ATTEMPTS:
                    os.remove(file + "log.bin")
                    Log.LocationEvent(b'\x1F').writeLog()
            print("Might be transmitting..?")
            Log.LocationEvent(b'\x1E').writeLog()
        except:
            print("Error while transmitting")
            Log.UnknownError("Transmit error").writeLog()
        t_attempts = 0
    else:
        t_attempts += 1
    # original intent was to transmit once per day, so could accumulate value
    # based on period and number of logs taken
    # implementation could be abstracted to UART or SPI output -> currently no plan to use real satellite link


def updateLCD():
    global UPDATE_DELAY
    Log.LCDEvent(b'\x20').writeLog()
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

def getAcc(msgSet):
    global LOC_CODE
    return msgSet[LOC_CODE].getPAcc()


def getEuclidiean(msgTriple):
    global LOC_CODE
    msg = msgTriple[1][LOC_CODE]
    px, py, pz = msg.get3DPos()
    return px ** 2 + py ** 2 + pz ** 2


# SHOULD return a list of messages with indexes matching the codes
def getMedianMsg(msgs):
    sorted_msg_values = list({key: value for key, value in
                         sorted(msgs.items(), key=lambda item: getEuclidiean(item))})
    halfway_point = (len(sorted_msg_values) + 1) / 2 - 1
    # easier to choose left value rather than average between the two
    med = msgs[sorted_msg_values[int(halfway_point)]]
    return med


def getBestAcc(msgs):
    msgs = sorted(msgs.values(), key=getAcc)
    return msgs[0]


surveying = False
def startSVIN(dur=600, acc=1000):
    global surveying
    bs = bytearray()
    bs.append(0xb5)
    bs.append(0x62)
    bs.append(0x06)
    bs.append(0x71)
    bs.append(0x28)
    bs.append(0)

    bs.append(0)
    bs.append(0)
    bs.append(1)
    bs.append(0)

    for i in range(20):
        bs.append(0)
    # bs.append(0x58)
    # bs.append(0x02)
    # bs.append(0)
    # bs.append(0)

    bs.extend(u4toBytes(dur))
    bs.extend(u4toBytes(acc))

    # bs.append(0xe8)
    # bs.append(0x03)
    # bs.append(0)
    # bs.append(0)
    for i in range(8):
        bs.append(0)

    ck_a, ck_b = ubxChecksum(bs[2:])
    bs.append(ck_a)
    bs.append(ck_b)
    gpsIn.write(bs)
    return bs

def stopSVIN(svinmsg):
    bs = bytearray()
    bs.append(0xb5)
    bs.append(0x62)
    bs.append(0x06)
    bs.append(0x71)
    bs.append(0x28)
    bs.append(0)

    bs.append(0)
    bs.append(0)
    bs.append(2)
    bs.append(0)

    bs.extend(svinmsg.meanX[0])
    bs.extend(svinmsg.meanY[0])
    bs.extend(svinmsg.meanZ[0])

    bs.extend(svinmsg.meanXHp[0])
    bs.extend(svinmsg.meanYHp[0])
    bs.extend(svinmsg.meanZHp[0])

    bs.append(0)
    bs.extend(svinmsg.meanAcc[0])

    bs.append(0)
    bs.append(0)
    bs.append(0)
    bs.append(0)

    bs.append(0)
    bs.append(0)
    bs.append(0)
    bs.append(0)
    for i in range(8):
        bs.append(0)

    ck_a, ck_b = ubxChecksum(bs[2:])
    bs.append(ck_a)
    bs.append(ck_b)
    gpsIn.write(bs)
    return bs

def saveCFG():
    bs = bytearray()
    bs.append(0xb5)
    bs.append(0x62)
    bs.append(0x06)
    bs.append(0x09)
    bs.extend(u2toBytes(13))

    bs.extend(x4toBytes(0))
    bs.extend(x4toBytes(7967))
    bs.extend(x4toBytes(0))
    bs.extend(x1toBytes(2))

    ck_a, ck_b = ubxChecksum(bs[2:])
    bs.append(ck_a)
    bs.append(ck_b)
    gpsIn.write(bs)
    return bs

def searchForSVIN():
    global SVIN_CODE
    code=-1
    while code != SVIN_CODE:
        pyb.delay(200)
        readBytes()
        msg, code = getMessageFromBuffer()
    return msg

cursvin=None
def toggleSVIN():
    global surveying, cursvin
    surveying = not surveying
    if surveying:
        print("Starting survey")
        startSVIN(SVIN_DUR, SVIN_ACC)
    elif not surveying and cursvin is not None:
        print("Stopping survey")
        stopSVIN(cursvin)
    saveCFG()

# resets clock to use actual period synced up to the time specified
def initialReading(i=0):
    global MSG_PERIOD, clock
    getReadings()  # take readings immediately
    clock.wakeup(MSG_PERIOD*1000, getReadings)
    Log.TimeWakeupSyncEvent().writeLog()

# used to synchronise the readings with the clock
def initialTimer(i=0):
    global MSG_START_TIME, MSG_PERIOD, clock
    if timeConfidence != 0:
        LCD.makeLCDBusy()
        clock.wakeup(None)
        time = clock.datetime()
        hour = time[4]
        diff = (hour - MSG_START_TIME) * 60 * 60
        if diff == 0 or diff % MSG_PERIOD == 0:
            clock.wakeup(MSG_PERIOD*1000, initialReading)
            print("Wakeup in", MSG_PERIOD*1000)
        elif diff < 0:
            clock.wakeup(abs(diff)*1000, initialReading)
            print("Wakeup in", abs(diff)*1000)
        elif diff > 0:
            nextLogTime = MSG_START_TIME
            period_h = MSG_PERIOD / 60 ** 2
            while diff > 0:
                nextLogTime += period_h
                diff = hour - nextLogTime
            clock.wakeup(MSG_PERIOD*1000 if diff == 0 else abs(diff)*60*60*1000, initialReading)
            print("Wakeup in", abs(diff)*1000)
    else:
        print("No time confidence")
    LCD.makeLCDFree()


print("Starting...")
getParamsFromConfig()
Log.initLogs(DEVICE_ID)
LCD.initLCDAPI(MSG_PERIOD, MSG_START_TIME, LOG_RAW, LOG_MEDIAN, LOG_BEST, IS_BASE_STATION, readCallback=forceReading, svintoggle=toggleSVIN, svin_dur=SVIN_DUR, svin_acc=SVIN_ACC)
# LCD.initLCDAPI(MSG_PERIOD, MSG_START_TIME, LOG_RAW, LOG_MEDIAN, LOG_BEST, False, readCallback=forceReading)
clock = pyb.RTC()
if not IS_BASE_STATION:
    clock.wakeup(10000, initialTimer) # start checking every 10 seconds if time is accurate, then start reading
                                        # properly
# main loop
svs = 0
Log.StartupEvent().writeLog()
while True:
    if not reading and LCD.powered == 1 or surveying:  # don't update LCD if taking a reading or if it's unpowered
        # LCD power check is done in LCD.updateLCD(..) but put here too to stop pyb.delay() from triggering = redundancy
        monitoring = LCD.monitoring
        if monitoring or surveying:
            # get a locaiton message from buffer
            msg_buf = {}  # reset to stop memory leaks - shouldn't interfere with periodic reading as won't be reachable during
            try:
                readBytes()
                msg, code = getMessageFromBuffer()
            except:
                msg = None
                code = -1
                Log.UnknownError("msg for LCD update")
            if code == LOC_CODE:
                print("Updating location data")
                LCD.updateLocMonitorData(msg, svs)
            elif code == SVIN_CODE:
                print("Updating survey data")
                LCD.updateSVINMonitorData(msg, surveying)
                cursvin = msg
            elif code == SATINF_CODE:
                svs = msg.getNumSvs()
        print("Updating LCD")
        updateLCD()
        pyb.delay(UPDATE_DELAY)
    pyb.wfi()  # put in low-power mode to reduce power consumption
