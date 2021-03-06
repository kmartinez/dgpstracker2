from Formats import *


#       ---------------------
#      | Log type |   Code   |
#      |----------|-----------
#      |  Error   |   0x00   |
#      |  BinLLH  |   0x01   |
#      |  BinECEF |   0x02   |
#      |  LLH     |   0x11   |
#      |  ECEF    |   0x12   |
#       ---------------------


class DateTime:
    year = None
    month = None
    day = None
    hour = None
    min = None
    sec = None
    nano = None

    def __init__(self, pvtMsg):
        self.year = pvtMsg.year
        self.month = pvtMsg.month
        self.day = pvtMsg.day
        self.hour = pvtMsg.hour
        self.min = pvtMsg.min
        self.sec = pvtMsg.sec
        self.nano = pvtMsg.nano

    # def __init__(self, year, month, day, hour, min, sec, nano):
    #     self.year = year
    #     self.month = month
    #     self.day = day
    #     self.hour = hour
    #     self.min = min
    #     self.sec = sec
    #     self.nano = nano

    def getYear(self):
        ys = str(self.year)
        return '0' * (4 - len(ys)) + ys

    def getMonth(self):
        mons = str(self.month)
        return '0' * (2 - len(mons)) + mons

    def getDay(self):
        ds = str(self.day)
        return '0' * (2 - len(ds)) + ds

    def getHour(self):
        hs = str(self.hour)
        return '0' * (2 - len(hs)) + hs

    def getMin(self):
        ms = str(self.min)
        return '0' * (2 - len(ms)) + ms

    def getSec(self):
        ss = str(self.sec)
        return '0' * (2 - len(ss)) + ss

    def getNano(self):
        ns = str(self.nano)
        return '0' * (2 - len(ns)) + ns

    def getDateTimeString(self):
        return self.getDateString() + " " + self.getTimeString()

    def getTimeString(self):
        return self.getHour() + ":" + self.getMin() + ":" + self.getSec() + "." + self.getNano()

    def getDateString(self):
        return self.getYear() + "-" + self.getMonth() + "-" + self.getDay()


class BinaryDateTime:
    class DateTime:
        year = None
        month = None
        day = None
        hour = None
        min = None
        sec = None

        def __init__(self, pvtMsg):
            self.year = u2toBytes(pvtMsg.year)
            self.month = u1toBytes(pvtMsg.month)
            self.day = u1toBytes(pvtMsg.day)
            self.hour = u1toBytes(pvtMsg.hour)
            self.min = u1toBytes(pvtMsg.min)
            self.sec = u1toBytes(pvtMsg.sec)


class DataLog:
    date = None
    svs = None
    pOut = None  # possible / probability of outlier?

    def getLogString(self):
        pass


class LLHLog(DataLog):
    hp = None
    lat = None
    lon = None
    h = None
    hmsl = None
    hAcc = None
    vAcc = None

    def __init__(self, dateTime, llhObj, sVs, pOut):
        self.date = dateTime
        self.hp = "hp" if llhObj.lonHp is not None or llhObj.latHp is not None else "lp"
        self.lat = llhObj.lat
        self.lon = llhObj.lon
        self.h = llhObj.height
        self.hmsl = llhObj.hMSL
        self.hAcc = llhObj.hAcc
        self.vAcc = llhObj.vAcc
        self.svs = sVs
        self.pOut = pOut

    def getLogString(self):
        return "[{0}] llh {2} {3} {4} {5} {6} {7} {8} {9}".format(
            self.date.getDateTimeString(),
            self.hp,
            self.lat,
            self.lon,
            self.h,
            self.hmsl,
            self.hAcc,
            self.vAcc,
            self.svs,
            self.pOut
        )


class ECEFLog(DataLog):
    x = None
    y = None
    z = None
    pAcc = None

    def __init__(self, date, hp, x, y, z, pAcc, sVs, pOut):
        self.date = date
        self.hp = hp
        self.x = x
        self.y = y
        self.z = z
        self.pAcc = pAcc
        self.svs = sVs
        self.pOut = pOut

    def getLogString(self):
        return "{0} {1} {2} {3} {4} {5} {6} {7} {8} {9} {10} {11} {12} {13}".format(
            self.date.getYear(),
            self.date.getMonth(),
            self.date.getDay(),
            self.date.getHour(),
            self.date.getMin(),
            self.date.getSec(),
            "ecef",
            self.hp,
            self.x,
            self.y,
            self.z,
            self.pAcc,
            self.svs,
            self.pOut
        )


class BinaryLLHLog(DataLog):
    type = b'\x01'
    dateTime = None
    lat = None
    lon = None
    h = None
    hmsl = None
    hacc = None
    vacc = None
    hp = None
    sats = None

    def __init__(self, binaryDateTime, llhObj, sVs):
        self.dateTime = binaryDateTime
        self.hp = b'1' if llhObj.lonHp is not None and llhObj.latHp is not None else b'0'
        self.lat = i4toBytes(llhObj.lat)
        self.lon = i4toBytes(llhObj.lon)
        self.h = i4toBytes(llhObj.height)
        self.hmsl = i4toBytes(llhObj.hMSL)
        self.hAcc = u4toBytes(llhObj.hAcc)
        self.vAcc = u4toBytes(llhObj.vAcc)
        self.svs = u1toBytes(sVs)

    def getLogString(self):
        log = bytearray()
        log.extend(self.dateTime.year)
        log.extend(self.dateTime.month)
        log.extend(self.dateTime.day)
        log.extend(self.dateTime.hour)
        log.extend(self.dateTime.minute)
        log.extend(self.dateTime.second)

        payload = bytearray()
        payload.extend(self.hp)
        payload.extend(self.lat)
        payload.extend(self.lon)
        payload.extend(self.h)
        payload.extend(self.hmsl)
        payload.extend(self.hAcc)
        payload.extend(self.vAcc)
        payload.extend(self.sats)

        crca, crcb = ubxChecksum(payload)

        log.extend(payload)
        log.extend(crca)
        log.extend(crcb)

        return log


class BinaryECEFLog(DataLog):
    tow = None
    x = None
    xhp = None
    y = None
    yhp = None
    z = None
    zhp = None
    pAcc = None
    svs = None
    datatype = None

    def setECEFData(self, ecefLog):
        self.x = ecefLog.ecefX
        self.y = ecefLog.ecefY
        self.z = ecefLog.ecefZ
        self.xhp = ecefLog.ecefXHp
        self.yhp = ecefLog.ecefYHp
        self.zhp = ecefLog.ecefZHp
        self.pAcc = ecefLog.pAcc

    def setSvs(self, satsMsg):
        self.svs = satsMsg.getNumSvs()

    # 0x00 = raw, 0x01 = median filtered, 0x02 = best accuracy
    def setDataType(self, dtype):
        self.datatype = dtype

    def getLogString(self):
        log = bytearray()
        year, month, day, weekday, hour, minute, second, nano = pyb.RTC().datetime()
        log.extend(u2fromBytes(year))
        log.extend(u1fromBytes(month))
        log.extend(u1fromBytes(day))
        log.extend(u1fromBytes(hour))
        log.extend(u1fromBytes(minute))
        log.extend(u1fromBytes(second))
        log.extend(i4fromBytes(nano))
        log.append(self.datatype)

        payload = bytearray()
        payload.extend(self.x)
        payload.extend(self.y)
        payload.extend(self.z)
        payload.extend(self.xhp)
        payload.extend(self.yhp)
        payload.extend(self.zhp)
        payload.extend(self.pAcc)
        payload.extend(self.svs)

        crca, crcb = ubxChecksum(payload)

        log.extend(payload)
        log.extend(crca)
        log.extend(crcb)

        return log


# log format:
# yyyy mm dd hh mm ss LLH LP/HP Lat Lon Height hmsl hacc vacc sats p_outlier
# yyyy mm dd hh mm ss ECEF LP/HP x y z pacc sats pout
class ErrorLog:
    date = None
    errorMsg = None

    def __init__(self, date, errorMsg):
        self.date = date
        self.errorMsg = errorMsg


# error log format:
# yyyy mm dd hh mm ss error

def unparse(bs):
    clazs = bs[0]
    dateTime = bs[1:8]
    pl = bs[8:-2]
    checksum = (bs[-2], bs[-1])
    corrupted = verifyChecksum(pl, checksum)
    # switch on clazs to parse pl with dateTime - unparse dateTime seperately
