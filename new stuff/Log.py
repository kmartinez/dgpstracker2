import pyb
from Formats import *
from LCD import getPrintableDate, getPrintableTime


class DataLog:
    payload = bytearray()
    logType = bytearray()

    def getLogString(self):
        ck_a, ck_b = ubxChecksum(self.payload)

        pack = bytearray(b'\xb5b')  # start delim
        pack.extend(curTimeInBytes()) # uses RTC of pyboard, might not match RT if unsynced/drifted
        pack.extend(self.logType)  # log type
        pack.extend(u2toBytes(len(self.payload)))  # pack length - should be 24 but just in case, calc dynamically
        pack.extend(self.payload)
        pack.extend(u1toBytes(ck_a))
        pack.extend(u1toBytes(ck_b))
        return pack

    def writeLog(self):
        logfile = open("log.bin", "ab")
        logfile.write(self.getLogString())
        logfile.flush()
        logfile.close()


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


class EventLog:
    class_id = bytearray()
    payload = bytearray()

    def getLogString(self):
        ck_a, ck_b = ubxChecksum(self.payload)
        pack = bytearray(b'\xb5b')  # start delim
        pack.extend(curTimeInBytes()) # uses RTC of pyboard, might not match RT if unsynced/drifted
        pack.extend(self.class_id)  # log type
        pack.extend(u2toBytes(len(self.payload)))  # pack length - should be 24 but just in case, calc dynamically
        pack.extend(self.payload)
        pack.extend(u1toBytes(ck_a))
        pack.extend(u1toBytes(ck_b))
        return pack

    def writeLog(self):
        file = open("eventLog.bin", "ab")
        file.write(self.getLogString())
        file.flush()
        file.close()

class StartupEvent(EventLog):
    class_id = b'\x00'

class CalibrateEvent(EventLog):
    class_id = b'\x03'

class TimeUpdateEvent(EventLog):
    class_id = b'\x01'

class TimeWakeupSyncEvent(EventLog):
    class_id = b'\x02'

class LocationEvent(EventLog):

    def __init__(self, eventType):
        self.class_id = bwAnd(eventType, b'\x1F')

class LCDEvent(EventLog):
    def __init__(self, eventType):
        self.class_id = bwAnd(eventType, b'\x2F')


class LengthForceError(EventLog):
    class_id = b'\xE0'

    def __init__(self, parseClass, parseID, byteLength, newLength):
        pl = bytearray()
        pl.extend(u2toBytes(parseClass))
        pl.extend(u2toBytes(parseID))
        pl.extend(u2toBytes(byteLength))
        pl.extend(u2toBytes(newLength))
        self.payload = pl


class LengthMismatchError(EventLog):
    class_id = b'\xE1'

    def __init__(self, parseClass, parseID, byteLength, parseLength):
        pl = bytearray()
        pl.extend(u2toBytes(parseClass))
        pl.extend(u2toBytes(parseID))
        pl.extend(u2toBytes(byteLength))
        pl.extend(u2toBytes(parseLength))
        self.payload = pl


class NoMessageError(EventLog):
    class_id = b'\xE2'

    def __init__(self, parseClass, parseID):
        pl = bytearray(b'\xb5b')
        pl.extend(u1toBytes(parseClass))
        pl.extend(u1toBytes(parseID))
        self.payload = pl


class EncodingError(EventLog):
    class_id = b'\xF2'

    def __init__(self, encode, number, format):
        if not encode:
            self.logType = b'\xF3'
        pl = bytearray()
        pl.extend(u4toBytes(number))
        pl.extend(u2toBytes(format))
        self.payload = pl


class NoSpaceError(EventLog):
    class_id = b'\xFE'


class GenericMemoryError(EventLog):
    class_id = b'\xFF'


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
    year = U2(bytes[0:2])
    month = U1(bytes[2])
    day = U1(bytes[3])
    hour = U1(bytes[4])
    minute = U1(bytes[5])
    second = U1(bytes[6])
    return year, month, day, hour, minute, second

def curTimeInBytes():
    year, month, day, weekday, hours, minutes, seconds, subseconds = pyb.RTC().datetime()
    return u2toBytes(year) + u1toBytes(month) + u1toBytes(day) + u1toBytes(hours) + u1toBytes(minutes) + u1toBytes(seconds)


def unparseLogs(filename):
    inf = open(filename, "rb")
    lines = inf.readlines()
    inf.close()
    logs = lines.split(b'\xb5b')  # uses same preamble as ubx logs for simplicity
    f = open("readablelogs.txt", "w")
    for line in logs:
        # skip empty lines
        if len(line) == 0:
            continue
        type = line[0]
        year, month, day, hour, minute, second = list(map(str, getTime(line[1:9])))
        logdata = line[9:]
        readable = year + "/" + month + "/" + day + "/" + " " + hour + ":" + minute + ":" + second + " - "
        if type == 0x00:
            readable += "Device startup"
        elif type == 0x02:
            readable += "RTC time updated"
        elif type == 0x02:
            readable += "Wakeup events synced to RTC"
        elif type == 0x10:
            readable += "ECEF Location logged"
        elif type == 0x11:
            # raw location log
            x = str( I4(logdata[0:4]) + .1 * I1(logdata[12:13]) )
            y = str( I4(logdata[4:8]) + .1 * I1(logdata[13:14]) )
            z = str( I4(logdata[8:12]) + .1 * I1(logdata[14:15]) )
            pacc = str( I4(logdata[15:19]) * .01)
            svs = str( U1(logdata[19:20]) )
            readable += "Raw location: [" + x + ", " + y + ", " + z + "]: " + pacc+"cm, svs="+svs
        elif type == 0x12:
            x = str(I4(logdata[0:4]) + .1 * I1(logdata[12:13]))
            y = str(I4(logdata[4:8]) + .1 * I1(logdata[13:14]))
            z = str(I4(logdata[8:12]) + .1 * I1(logdata[14:15]))
            pacc = str(I4(logdata[15:19]) * .01)
            svs = str(U1(logdata[19:20]))
            readable += "Median-smoothed location: [" + x + ", " + y + ", " + z + "]: " + pacc + "cm, svs=" + svs
        elif type == 0x13:
            x = str(I4(logdata[0:4]) + .1 * I1(logdata[12:13]))
            y = str(I4(logdata[4:8]) + .1 * I1(logdata[13:14]))
            z = str(I4(logdata[8:12]) + .1 * I1(logdata[14:15]))
            pacc = str(I4(logdata[15:19]) * .01)
            svs = str(U1(logdata[19:20]))
            readable += "Best-accuracy location: [" + x + ", " + y + ", " + z + "]: " + pacc + "cm, svs=" + svs
        elif type == 0x1E:
            readable += "Location logs transmitted"
        elif type == 0x1F:
            readable += "Location logs cleared"
        elif type == 0x21:
            readable += "LCD on"
        elif type == 0x22:
            readable += "LCD off"
        elif type == 0x23:
            readable += "LCD locked"
        elif type == 0x24:
            readable += "LCD unlocked"
        elif type == 0xE0:
            # len forcibly changed by code
            ubxClass = U1(logdata[:1])
            ubxID = U1(logdata[1:2])
            byteLength = U2(logdata[2:4])
            newLength = U2(logdata[4:6])
            readable += "Length forcibly changed for " + str([ubxClass, ubxID]) + ": " + str(byteLength) + " -> " + str(
                newLength)
        elif type == 0xE1:
            # len mismatch with parsed len
            ubxClass = U1(logdata[:1])
            ubxID = U1(logdata[1:2])
            byteLength = U2(logdata[2:4])
            parseLength = U2(logdata[4:6])
            readable += "Length mismatch on " + str([ubxClass, ubxID]) + ": " + str(byteLength) + "(b) vs " + str(
                parseLength) + "(p)"
        elif type == 0xE2:
            # no parse data for incoming message
            ubxClass = U1(logdata[:1])
            ubxID = U1(logdata[1:2])
            readable += "No programmed message for class="+str(ubxClass)+", id="+str(ubxID)
        elif type == 0xF0:
            readable += "UART port uncalibrated"
        elif type == 0xF1:
            # unacceptable packet length on uart stream (>100 and not sat)
            badLength = U2(logdata[:2])
            readable += "Unacceptable packet length read from UART stream: "+str(badLength)
        elif type == 0xF2:
            # number ENcoding error
            badNumber = I4(logdata[:4])
            format = U2(logdata[4:6])
            readable += "Number encoding error: "+str(badNumber) + ": "+str(format)
            pass
        elif type == 0xF3:
            # number DEcoding error
            badNumber = I4(logdata[:4])
            format = U2(logdata[4:6])
            readable += "Number decoding error: " + str(badNumber) + ": " + str(format)
            pass
        elif type == 0xFE:
            readable += "Not enough space in storage to keep logs"
        elif type == 0xFF:
            readable += "Unknown error"
        # write to file - no check for file space :/
        f.write(readable + "\n")
