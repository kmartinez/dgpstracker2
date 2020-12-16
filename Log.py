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
        return '0' * (4-len(ys)) + ys

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
        return self.getDateString()+" "+self.getTimeString()

    def getTimeString(self):
        return self.getHour() + ":" + self.getMin() + ":" + self.getSec() + "." + self.getNano()

    def getDateString(self):
        return self.getYear()+"-"+self.getMonth()+"-"+self.getDay()


class DataLog:
    date = None
    svs = None
    pOut = None

    def getLogString(self):
        return ""


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
