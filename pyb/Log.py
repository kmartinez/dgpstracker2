import pyb
import Formats
import os

DEVICE_ID = 0
PRECISION = 0  # 0=day,1=hour


class RawLog:
    data = bytearray()

    def __init__(self, data):
        self.data = data

    def getLogString(self):
        return self.data

    def writeLog(self):
        fn = "datalog.bin"
        writeDataToFile(fn, self.getLogString())


class DataLog:
    payload = bytearray()
    logType = bytearray()

    def getLogString(self):
        global DEVICE_ID
        pack = bytearray(b'\xb5b')  # start delim
        pack.extend(curTimeInBytes())  # uses RTC of pyboard, might not match RT if unsynced/drifted
        pack.extend(Formats.u1toBytes(DEVICE_ID))  # identifies device
        pack.extend(self.logType)  # log type
        pack.extend(Formats.u2toBytes(len(self.payload)))  # pack length - set dynamically
        pack.extend(self.payload)

        ck_a, ck_b = Formats.ubxChecksum(self.payload)
        pack.extend(Formats.u1toBytes(ck_a))
        pack.extend(Formats.u1toBytes(ck_b))
        return pack

    def writeLog(self):
        fn = getdtstring() + "log.bin"
        writeDataToFile(fn, self.getLogString())


class ECEFLog(DataLog):
    def __init__(self, ecefMsg, smoothType, satMsg):
        pl = bytearray()
        pl.extend(ecefMsg.ecefX[0])
        pl.extend(ecefMsg.ecefY[0])
        pl.extend(ecefMsg.ecefZ[0])
        pl.extend(ecefMsg.ecefXHp[0])
        pl.extend(ecefMsg.ecefYHp[0])
        pl.extend(ecefMsg.ecefZHp[0])
        pl.extend(ecefMsg.pAcc[0])
        pl.extend(satMsg.numSvs[0])
        self.logType = (bwAnd(b'\x1F', smoothType))
        self.payload = pl


# deprecated due to HUGE latency caused by it - can be re-enabled by looking into functions and uncommenting
class EventLog:
    class_id = bytearray()
    payload = bytearray()
    # used to filter out latency issues caused by over-using I/O with minor, unimportant events
    acceptable_ids = [b'\x00', b'\x01', b'\x02', b'\x1e', b'\x1f', b'\x20', b'\x21', b'\xe2', b'\xf1', b'\xf2', b'\xf3',
                      b'\xf4', b'\xf5', b'\xfe', b'\xff']

    def getLogString(self):
        global DEVICE_ID
        if self.class_id not in self.acceptable_ids:
            return bytearray()
        pack = bytearray(b'\xb5b')  # start delim
        pack.extend(curTimeInBytes())  # uses RTC of pyboard, might not match RT if unsynced/drifted
        pack.extend(Formats.u1toBytes(DEVICE_ID))  # log type
        pack.extend(self.class_id)  # log type
        pack.extend(
            Formats.u2toBytes(len(self.payload)))  # pack length - should be 24 but just in case, calc dynamically
        pack.extend(self.payload)

        ck_a, ck_b = Formats.ubxChecksum(self.payload)
        pack.extend(Formats.u1toBytes(ck_a))
        pack.extend(Formats.u1toBytes(ck_b))
        return pack

    def writeLog(self):
        if self.class_id not in self.acceptable_ids:
            return bytearray()
        fn = getdtstring() + "eventLog.bin"
        writeDataToFile(fn, self.getLogString())


waiting_logs = {}


def writeDataToFile(filename, data):
    if filename not in waiting_logs:
        waiting_logs[filename] = 0
    file = open(filename, "ab")
    file.write(data)
    file.flush()
    file.close()


class StartupEvent(EventLog):
    class_id = b'\x00'


class CalibrateEvent(EventLog):
    class_id = b'\x03'


class CalibrationTimeoutEvent(EventLog):
    class_id = b'\xF4'


class ReadingTimeoutEvent(EventLog):
    class_id = b'\xF5'


class TimeUpdateEvent(EventLog):
    class_id = b'\x01'


class TimeWakeupSyncEvent(EventLog):
    class_id = b'\x02'


class LocationEvent(EventLog):

    def __init__(self, eventType):
        self.class_id = b'\x10'
        self.payload = eventType


class LCDEvent(EventLog):
    def __init__(self, eventType):
        self.class_id = bwAnd(eventType, b'\x2F')


class LengthForceError(EventLog):
    class_id = b'\xE0'

    def __init__(self, parseClass, parseID, byteLength, newLength):
        pl = bytearray()
        pl.extend(Formats.u2toBytes(parseClass))
        pl.extend(Formats.u2toBytes(parseID))
        pl.extend(Formats.u2toBytes(byteLength))
        pl.extend(Formats.u2toBytes(newLength))
        self.payload = pl


class LengthMismatchError(EventLog):
    class_id = b'\xE1'

    def __init__(self, parseClass, parseID, byteLength, parseLength):
        pl = bytearray()
        pl.extend(Formats.u2toBytes(parseClass))
        pl.extend(Formats.u2toBytes(parseID))
        pl.extend(Formats.u2toBytes(byteLength))
        pl.extend(Formats.u2toBytes(parseLength))
        self.payload = pl


class UnacceptableLengthError(EventLog):
    class_id = b'\xF1'

    def __init__(self, lengthbytes):
        self.payload.extend(lengthbytes)


class NoMessageError(EventLog):
    class_id = b'\xE2'

    def __init__(self, parseClass, parseID):
        pl = bytearray(b'\xb5b')
        pl.extend(Formats.u1toBytes(parseClass))
        pl.extend(Formats.u1toBytes(parseID))
        self.payload = pl


class EncodingError(EventLog):
    class_id = b'\xF2'

    def __init__(self, numberStr, format):
        # cap length at 14 bytes
        if len(numberStr) > 14:
            numberStr = numberStr[:14]
        pl = bytearray()
        pl.extend(bytearray(format, "ascii"))
        pl.extend(bytearray(numberStr, "ascii"))
        self.payload = pl


class DecodingError(EventLog):
    class_id = b'\xF3'

    def __init__(self, bytestr, format):
        pl = bytearray()
        pl.extend(bytearray(format, "ascii"))
        pl.extend(bytestr)
        self.payload = pl


class NoSpaceError(EventLog):
    class_id = b'\xFE'


class UnknownError(EventLog):
    class_id = b'\xFF'

    def __init__(self, description):
        # cap length of descr at 25 bytes
        self.payload = bytearray(description[:min(len(description), 50)])


def initLogs(device_id):
    global DEVICE_ID
    DEVICE_ID = device_id


def bwAnd(b1, b2):
    r = b''
    for i in range(min(len(b1), len(b2))):
        r += bytes([b1[i] & b2[i]])
    return r


def bwOr(b1, b2):
    r = b''
    for i in range(min(len(b1), len(b2))):
        r += bytes([b1[i] | b2[i]])
    return r


def getTime(bytes):
    if bytes is None or bytes == b'':
        return 0, 0, 0, 0, 0, 0

    year = Formats.U2(bytes[0:2])
    month = Formats.U1(bytes[2])
    day = Formats.U1(bytes[3])
    hour = Formats.U1(bytes[4])
    minute = Formats.U1(bytes[5])
    second = Formats.U1(bytes[6])
    return year, month, day, hour, minute, second


def curTimeInBytes():
    year, month, day, weekday, hours, minutes, seconds, subseconds = pyb.RTC().datetime()
    return Formats.u2toBytes(year) + Formats.u1toBytes(month) + Formats.u1toBytes(day) + Formats.u1toBytes(hours) + \
           Formats.u1toBytes(minutes) + Formats.u1toBytes(seconds)


def getdtstring():
    time = pyb.RTC().datetime()
    return "{0}-{1}-{2}-".format(time[2], time[1], time[0])


def unparseLogs():
    # try:
    filesToDecode = list(filter(lambda i: ".bin" in i, os.listdir()))
    for fn in filesToDecode:
        # check the extension of files
        print(fn)
        unparseLog(fn)
    # except Exception as e:
    #     print("Error while decoding logs?", e)


def calibrateFile(file):
    start_bit_one = False
    start_bit_two = False
    curr = b'\x00'
    while not (start_bit_one and start_bit_two) and curr is not None and curr != b'':
        curr = file.read(1)
        if curr == b'\xb5':
            start_bit_one = True
        elif curr == b'\x62':
            start_bit_two = True
        else:
            start_bit_one = False
            start_bit_two = False


def getLine(file):
    print("------")
    calibrateFile(file)
    date = file.read(7)
    did = file.read(1)
    type = file.read(1)
    lbytes = file.read(2)
    print(date, did, type, lbytes)
    if lbytes == b'':
        # eof reached
        return None

    length = Formats.U2(lbytes)
    if length > 50:
        return b''

    data = file.read(length)
    print(data)
    crc = file.read(2)
    if crc is None or crc == b'':
        return None

    return date, did, type, data




def unparseLog(filename):
    inf = open(filename, "rb")
    line = b''
    fev = open(filename.split(".")[0] + "_parsed_events.txt", "w")
    fcsv = open(filename.split(".")[0] + "_parsed_data.csv", "w")
    dups = set()
    while line is not None:
        line = getLine(inf)
        if line is None or len(line) == 0:
            continue
        # SHOULD only be on line, since no \n written... but just in case
        # print(line)
        # skip empty lines
        if len(line) == 0:
            continue
        year, month, day, hour, minute, second = list(map(str, getTime(line[0])))
        did = Formats.U1(line[1])
        type = Formats.U1(line[2])
        logdata = line[3]
        readable = "[{0}] - {1}/{2}/{3} {4}:{5}:{6} - ".format(did, day, month, year, hour, minute, second)
        csv = "{0},{1}/{2}/{3} {4}:{5}:{6},".format(did, day, month, year, hour, minute, second)
        print(type, readable, logdata)
        if type == 0x00:
            readable += "Device startup"
        elif type == 0x01:
            readable += "RTC synchronised"
        elif type == 0x02:
            readable += "RTC time updated"
        elif type == 0x02:
            readable += "Wakeup events synced to RTC"
        elif readable == 0x03:
            readable += "Calibration succeeded"
        elif type == 0x10:
            eType = logdata[0]
            if eType == 0x11:
                eType = "unfiltered"
            elif eType == 0x12:
                eType = "median"
            elif eType == 0x13:
                eType = "best-acc"
            else:
                eType = "unknown"
            readable += "ECEF Location logged [{0}]".format(eType)
        elif type == 0x11:
            # raw location log
            x = Formats.I4(logdata[0:4]) + 1e-2 * Formats.I1(logdata[12:13])
            y = Formats.I4(logdata[4:8]) + 1e-2 * Formats.I1(logdata[13:14])
            z = Formats.I4(logdata[8:12]) + 1e-2 * Formats.I1(logdata[14:15])
            pacc = Formats.I4(logdata[15:19]) * .01
            svs = Formats.U1(logdata[19:20])
            readable += "Raw location, accuracy: " + str(pacc)
            csv += "raw,{0:.2f},{1:.2f},{2:.2f},{3:.2f},{4:.2f}".format(x, y, z, pacc, svs)
            print(readable)
        elif type == 0x12:
            x = Formats.I4(logdata[0:4]) + 1e-2 * Formats.I1(logdata[12:13])
            y = Formats.I4(logdata[4:8]) + 1e-2 * Formats.I1(logdata[13:14])
            z = Formats.I4(logdata[8:12]) + 1e-2 * Formats.I1(logdata[14:15])
            pacc = Formats.I4(logdata[15:19]) * .01
            svs = Formats.U1(logdata[19:20])
            readable += "Median-filtered location, accuracy: " + str(pacc)+"cm"
            csv += "med,{0:.2f},{1:.2f},{2:.2f},{3:.2f},{4:.2f}".format(x, y, z, pacc, svs)
            print(readable)
        elif type == 0x13:
            x = Formats.I4(logdata[0:4]) + 1e-2 * Formats.I1(logdata[12:13])
            y = Formats.I4(logdata[4:8]) + 1e-2 * Formats.I1(logdata[13:14])
            z = Formats.I4(logdata[8:12]) + 1e-2 * Formats.I1(logdata[14:15])
            pacc = Formats.I4(logdata[15:19]) * .01
            svs = Formats.U1(logdata[19:20])
            readable += "Best-accuracy-filtered location, accuracy: " + str(pacc)+"cm"
            csv += "ba,{0:.2f},{1:.2f},{2:.2f},{3:.2f},{4:.2f}".format(x, y, z, pacc, svs)
            print(readable)
        elif type == 0x1E:
            readable += "Location logs transmitted"
        elif type == 0x1F:
            readable += "Location logs cleared"
        elif type == 0x20:
            readable += "LCD on"
        elif type == 0x21:
            readable += "LCD off"
        elif type == 0x22:
            readable += "LCD locked"
        elif type == 0x23:
            readable += "LCD unlocked"
        elif type == 0xE0:
            # len forcibly changed by code
            ubxClass = Formats.U1(logdata[:1])
            ubxID = Formats.U1(logdata[1:2])
            byteLength = Formats.U2(logdata[2:4])
            newLength = Formats.U2(logdata[4:6])
            readable += "Length force for " + str([ubxClass, ubxID]) + ": " + str(
                byteLength) + " -> " + str(
                newLength)
        elif type == 0xE1:
            # len mismatch with parsed len
            ubxClass = Formats.U1(logdata[:1])
            ubxID = Formats.U1(logdata[1:2])
            byteLength = Formats.U2(logdata[2:4])
            parseLength = Formats.U2(logdata[4:6])
            readable += "Length mismatch on " + str([ubxClass, ubxID]) + ": " + str(byteLength) + "(b) vs " + str(
                parseLength) + "(p)"
        elif type == 0xE2:
            # no parse data for incoming message
            ubxClass = Formats.U1(logdata[:1])
            ubxID = Formats.U1(logdata[1:2])
            readable += "No class=" + str(ubxClass) + ", id=" + str(ubxID)
        elif type == 0xF0:
            readable += "UART port uncalibrated"
        elif type == 0xF1:
            # unacceptable packet length on uart stream (>100 and not sat)
            print(line)
            try:
                badLength = Formats.U2(logdata[:2])
            except:
                badLength = "<uknown>"
            readable += "Bad UART len: " + str(badLength)
        elif type == 0xF2:
            # number ENcoding error
            badNumber = (logdata[:4])
            format = (logdata[4:6])
            readable += "Number encoding error: " + str(badNumber) + ": " + str(format)
        elif type == 0xF3:
            # number DEcoding error
            badNumber = (logdata[:4])
            format = (logdata[4:6])
            readable += "Number decoding error: " + str(badNumber) + ": " + str(format)
        elif type == 0xF4:
            readable += "Calibration t-o"
        elif type == 0xF5:
            readable += "Reading t-o"
        elif type == 0xFE:
            readable += "No storage space"
        elif type == 0xFF:
            readable += str(logdata)
        else:
            readable += "UE: " + str(type)
        if hash(readable) not in dups:
            # write to file - no check for file space :/
            fev.write(readable + "\n")
            dups.add(hash(readable))
        # csv line complete
        if csv[-1] != "," and hash(csv) not in dups:
            fcsv.write(csv+"\n")
            dups.add(hash(csv))
        # print(readable)
        # print("------")
    fcsv.flush()
    fcsv.close()
    fev.flush()
    fev.close()
