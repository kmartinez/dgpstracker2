from Message import *
from Log import *
from LCD import *
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
        pym.delay(10000)
    nextpack = None


def readIn():
    global x, y, z, pacc, lat, lon, h, sats, fix, lathp, lonhp, lastLLH, lastTime, lastDateObject, lastStat
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
        # pym.delay(2000)

    return read_status


def printStatus():
    print(stat)


gpsIn = UART(6, 9600)
gpsIn.init(9600, bits=8, parity=None, stop=1, read_buf_len=512, timeout=2000)
time = pym.Timer(8, freq=1)
# time.callback(printStatus)

BUF_SIZ = 4

x = None
y = None
z = None
pacc = None
lat = None
lathp = None
lon = None
lonhp = None
h = None
sats = None
fix = None
# wdt = WDT(timeout=10000)

lastTime = None
lastDateObject = None
lastLLH = None
lastECEF = None
lastStat = None
sVs = None
# fix=None

print("Starting...")
initLCD()

logFile = open("l.log", "a")
cur_hour = 16
# loggedHours={0:False,8:False,16:False} # log every 8 hours - when logHours[hour]==False
loggedHours = {0: False, 8: False, cur_hour: False}  # for debugging


def llhStatus():
    if lastLLH is not None and lastStat is not None and lastTime is not None:
        showLLHStatus(
            lastStat.gpsFixOK and not lastLLH.invalidFix,
            lastStat.diffSol,
            lastLLH.iTOW,
            lastStat.towValid,
            fix,
            not lastStat.solInvalid,
            lastLLH.lat,
            lastLLH.latHp,
            lastLLH.lon,
            lastLLH.lonHp,
            lastLLH.height,
            lastLLH.hMSL,
            lastLLH.vAcc,
            lastLLH.hAcc,
            lastDateObject
        )


def writeLog():
    global logFile
    log = LLHLog(lastDateObject, lastLLH, sats, 0)
    print("Writing log:")
    print(log.getLogString())
    logFile.write(log.getLogString())
    logFile.write("\n")
    logFile.close()


def readAverageLLH():
    # read x times
    # median average over whole list
    # gon compute mean for comparison too
    DATA_BUF_SIZ = 25
    databuff = []
    while len(databuff) < DATA_BUF_SIZ:
        readBytes()
        status = readIn()
        print(status)
        databuff.append(lastLLH)
    databuff.sort()
    median = databuff[len(databuff) / 2]
    return median


def getDistance(x, y, z):
    return (x ** 2 + y ** 2 + z ** 2) ** .5


while True:
    print("---")
    readBytes()
    # wdt.feed()
    # returns a string repr message plus assigns global vars
    # -- need to split into mul functions
    status = readIn()
    # prints out what message was found
    if status is not None:
        print(status)
        # pass
    if (len(pack_buf)) > BUF_SIZ:
        # if too many messages, discard current buffer to prefer newer messages
        # print(pack_buf)
        pack_buf = []

    if lastTime is not None and lastLLH is not None:
        lastDateObject = DateTime(lastTime)
        curHour = lastDateObject.hour
        if curHour in loggedHours and not loggedHours[curHour]:
            writeLog()
            loggedHours[curHour] = True

            # reset other hours to allow further logging
            for time in loggedHours:
                if time is not curHour:
                    loggedHours[time] = False
        elif curHour in loggedHours:
            print("Already logged this hour")

    llhStatus()
    print("Distance:", getDistance(x, y, z))

    # pym.delay(20)
