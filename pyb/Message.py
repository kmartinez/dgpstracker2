# General set of classes used to indentify and parse messages
# field names are direct copy to documentation found here:
# https://www.u-blox.com/en/docs/UBX-13003221

from Formats import *

fixes = ["No fix", "Dead reckoning", "2D", "3D", "GPS + DR", "Time"]


class InvalidFixError(Exception):
    msg = None

    def __init__(self, msg):
        self.msg = msg

    def getMessage(self):
        return self.msg


class Message:
    iTOW = None

    def __init__(self, iTOW):
        self.iTOW = iTOW

    def getTOW(self):
        if type(self.iTOW) is not tuple:
            return self.iTOW
        else:
            return self.iTOW[1](self.iTOW[0])


# 01 01
class ECEF(Message):
    ecefX = None
    ecefY = None
    ecefZ = None
    pAcc = None

    def __init__(self, tow, x, y, z, acc):
        self.iTOW = tow
        self.ecefX = x
        self.ecefY = y
        self.ecefZ = z
        self.pAcc = acc

    def getX(self):
        if type(self.ecefX) is not tuple:
            return self.ecefX
        else:
            return self.ecefX[1](self.ecefX[0])

    def getY(self):
        if type(self.ecefY) is not tuple:
            return self.ecefY
        else:
            return self.ecefY[1](self.ecefY[0])

    def getZ(self):
        if type(self.ecefZ) is not tuple:
            return self.ecefZ
        else:
            return self.ecefZ[1](self.ecefZ[0])

    def getPAcc(self):
        if type(self.pAcc) is not tuple:
            return self.pAcc * 1e-4
        else:
            return self.pAcc[1](self.pAcc[0]) * 1e-2


# 01 02
class LLH(Message):
    lon = None
    lat = None
    height = None
    hMSL = None
    hAcc = None
    vAcc = None

    def __init__(self, tow, lon, lat, h, hmsl, hacc, vacc):
        self.iTOW = tow
        self.lon = lon
        self.lat = lat
        self.height = h
        self.hMSL = hmsl
        self.hAcc = hacc
        self.vAcc = vacc


# 01 03
class Status(Message):
    gpsFix = None
    flags = None
    fixStat = None
    flags2 = None
    ttff = None
    msss = None
    diffSol = None
    gpsFixOK = None
    wknValid = None
    towValid = None
    solInvalid = None

    def __init__(self, tow, fix, flags, fixstat, flags2, ttff, msss):
        self.iTOW = tow
        self.fixStat = fixstat if type(fixstat) is not tuple else fixstat[1](fixstat[0])
        self.flags = flags if type(flags) is not tuple else flags[1](flags[0])
        # translate flags to variables
        self.towValid = self.flags & 8 == 8
        self.wknValid = self.flags & 4 == 4
        self.diffSol = self.flags & 2 == 2
        self.gpsFixOK = self.flags & 1 == 1

        self.solInvalid = self.fixStat & 2 == 2

        self.ttff = ttff
        self.flags2 = flags2 if type(flags2) is not tuple else flags2[1](flags2[0])
        self.msss = msss

        try:
            self.gpsFix = fixes[fix[0]]
        except:
            # print(fix)
            self.gpsFix = "E - Reserved " + str(flags) + " " + str(fixstat)

# 01 06
class Solution(Message):
    fTOW = None
    week = None
    gpsFix = None
    ecefX = None
    ecefY = None
    ecefZ = None
    pAcc = None
    ecefVX = None
    ecefVY = None
    ecefVZ = None
    sAcc = None
    pDOP = None
    numSv = None

    def __init__(self, tow, ftow, week, fix, x, y, z, pacc, vx, vy, vz, sacc, pdop, numsats):
        self.iTOW = tow
        self.fTOW = ftow
        self.week = week
        self.gpsFix = fix
        self.ecefX = x
        self.ecefY = y
        self.ecefZ = z
        self.pAcc = pacc
        self.ecefVX = vx
        self.ecefVY = vy
        self.ecefVZ = vz
        self.sAcc = sacc
        self.pDOP = pdop
        self.numSv = numsats


# Precise coordinate in cm = ecefX + (ecefXHp * 1e-2).
# 01 13
class HPECEF(ECEF):
    ecefXHp = None
    ecefYHp = None
    ecefZHp = None
    pAcc = None
    invalidFix = None

    def __init__(self, tow, x, y, z, xhp, yhp, zhp, pacc, flags):
        super(HPECEF, self).__init__(tow, x, y, z, pacc)
        self.ecefXHp = xhp
        self.ecefYHp = yhp
        self.ecefZHp = zhp
        if type(flags) is not tuple:
            self.invalidFix = flags == b'\x01'
        else:
            self.invalidFix = flags[0] == b'\x01'

    def getXHP(self):
        if type(self.ecefXHp) is not tuple:
            return self.ecefXHp
        else:
            return self.ecefXHp[1](self.ecefXHp[0])

    def getYHP(self):
        if type(self.ecefYHp) is not tuple:
            return self.ecefYHp
        else:
            return self.ecefYHp[1](self.ecefYHp[0])

    def getZHP(self):
        if type(self.ecefZHp) is not tuple:
            return self.ecefZHp
        else:
            return self.ecefZHp[1](self.ecefZHp[0])

    def getXPos(self):
        return self.getX() + self.getXHP() * 1e-2

    def getYPos(self):
        return self.getY() + self.getYHP() * 1e-2

    def getZPos(self):
        return self.getZ() + self.getZHP() * 1e-2

    def get3DPos(self):
        return self.getXPos(), self.getYPos(), self.getZPos()


# Precise longitude in deg * 1e-7 = lon + (lonHp * 1e-2).
# 01 14
class HPLLH(LLH):
    lon = None
    lat = None
    height = None
    hMSL = None
    lonHp = None
    latHp = None
    heightHp = None
    hMSLHp = None
    invalidFix = None

    def __init__(self, tow, lon, lat, h, hmsl, lonhp, lathp, hhp, hmslhp, hacc, vacc, flags):
        self.iTOW = tow
        self.lon = (lon + lonhp * .01) * .0000001
        self.lat = (lat + lathp * .01) * .0000001
        self.height = h
        self.hMSL = hmsl
        self.lonHp = lonhp
        self.latHp = lathp
        self.heightHp = hhp
        self.hMSLHp = hmslhp
        self.hAcc = hacc
        self.vAcc = vacc
        self.invalidFix = flags == 1


# 01 35
class SatInfo(Message):
    numSvs = None

    # there is more information but I don't know if I need it yet

    def __init__(self, tow, nosats):
        self.iTOW = tow
        self.numSvs = nosats

    def getNumSvs(self):
        if type(self.numSvs) is not tuple:
            return self.numSvs
        else:
            return self.numSvs[1](self.numSvs[0])


class TimeUTC(Message):
    tAcc = None
    nano = None
    year = None
    month = None
    day = None
    hour = None
    min = None
    sec = None
    valid = None

    validTime = None
    validDate = None

    def __init__(self, iTOW, tAcc, nano, year, month, day, hour, min, sec, valid):
        self.iTOW = iTOW
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.min = min
        self.sec = sec
        self.valid = valid
        self.tAcc = tAcc
        self.nano = nano

    def getYear(self):
        if notLazy(self.year):
            return self.year
        else:
            return self.year[1](self.year[0])

    def getMonth(self):
        if notLazy(self.month):
            return self.year
        else:
            return self.month[1](self.month[0])

    def getDay(self):
        if notLazy(self.day):
            return self.year
        else:
            return self.day[1](self.day[0])

    def getHour(self):
        if notLazy(self.hour):
            return self.year
        else:
            return self.hour[1](self.hour[0])

    def getMinute(self):
        if notLazy(self.min):
            return self.year
        else:
            return self.min[1](self.min[0])

    def getSeconds(self):
        if notLazy(self.sec):
            return self.year
        else:
            return self.sec[1](self.sec[0])

    def getNano(self):
        if notLazy(self.nano):
            return self.nano
        else:
            return self.nano[1](self.nano[0])

    def validTime(self):
        if notLazy(self.valid):
            return self.valid & 4
        else:
            return self.valid[1](self.valid[0]) & 4


# 01 3B
class SVIN(Message):
    dur = None
    meanX = None
    meanY = None
    meanZ = None
    meanXHp = None
    meanYHp = None
    meanZHp = None
    meanAcc = None
    obs = None
    valid = None
    active = None

    def __init__(self, dur, meanX, meanY, meanZ, meanXHp, meanYHp, meanZHp, meanAcc, obs, valid, active):
        self.iTOW = 0
        self.dur = dur
        self.meanX = meanX
        self.meanY = meanY
        self.meanZ = meanZ
        self.meanXHp = meanXHp
        self.meanYHp = meanYHp
        self.meanZHp = meanZHp
        self.meanAcc = meanAcc
        self.obs = obs
        self.valid = valid
        self.active = active

    def getX(self):
        if type(self.meanX) is not tuple:
            return self.meanX
        else:
            return self.meanX[1](self.meanX[0])

    def getY(self):
        if type(self.meanY) is not tuple:
            return self.meanY
        else:
            return self.meanY[1](self.meanY[0])

    def getZ(self):
        if type(self.meanZ) is not tuple:
            return self.meanZ
        else:
            return self.meanZ[1](self.meanZ[0])

    def getPAcc(self):
        if type(self.meanAcc) is not tuple:
            return self.meanAcc * 1e-4
        else:
            return self.meanAcc[1](self.meanAcc[0]) * 1e-4

    def getXHP(self):
        if type(self.meanXHp) is not tuple:
            return self.meanXHp
        else:
            return self.meanXHp[1](self.meanXHp[0])

    def getYHP(self):
        if type(self.meanYHp) is not tuple:
            return self.meanYHp
        else:
            return self.meanYHp[1](self.meanYHp[0])

    def getZHP(self):
        if type(self.meanZHp) is not tuple:
            return self.meanZHp
        else:
            return self.meanZHp[1](self.meanZHp[0])

    def getXPos(self):
        return self.getX() + self.getXHP() * 1e-2

    def getYPos(self):
        return self.getY() + self.getYHP() * 1e-2

    def getZPos(self):
        return self.getZ() + self.getZHP() * 1e-2

    def get3DPos(self):
        return self.getXPos(), self.getYPos(), self.getZPos()

    def getDuration(self):
        if type(self.dur) is not tuple:
            return self.dur
        else:
            return self.dur[1](self.dur[0])

    def getObs(self):
        if type(self.obs) is not tuple:
            return self.obs
        else:
            return self.obs[1](self.obs[0])

    def getValid(self):
        if type(self.valid) is not tuple:
            return self.valid
        else:
            return self.valid[1](self.valid[0])

    def getActive(self):
        if type(self.active) is not tuple:
            return self.active
        else:
            return self.active[1](self.active[0])


def notLazy(x):
    return type(x) is not tuple


# U1 Unsigned char
# I1 Signed char, 2c
# X1 bitfield (1 byte)
# U2 unsigned short
# I2 signed short 2c
# X2 bitfield (2 bytes)
# U4 Unsigned long
# I4 signed long
# X4 bitfield (4 bytes)

# Little endian format of a hex string separated by spaces
def littleEndianOf(bytes):
    if bytes is None:
        return 0
    elif isinstance(bytes, int):
        return bytes
    return int.from_bytes(bytes, 'little')


def bigEndianOf(bytes):
    if bytes is None:
        return 0
    elif isinstance(bytes, int):
        return bytes
    return int.from_bytes(bytes, 'big')


def binaryParseUBXMessage(msg):
    # ba = msg.split(" ")
    ba = msg
    # print(ba[6:14])
    confirm = ba[0] == 0xb5 and ba[1] == 0x62
    if not confirm:
        print("Data corrupted: preamble")

    # print(ba)

    classs = U1(ba[2:3])
    id = U1(ba[3:4])
    length = U2(ba[4:6])  # little endian for length, only defines length of payload
    # also note is number of bytes in pl not bits

    cid = [classs, id]
    # print("\n",cid,"\n")

    pl = ba[6:-2]
    crc = (ba[-2], ba[-1])

    corrupted = verifyChecksum(pl, crc)

    # print(id)
    # print(len(pl))
    # crc = int(ba[-2] + ba[-1], 16)

    if length != (len(ba) - 6 - 2):
        print("Data corrupted: Length")
        # log - don't halt since might be sat msg

    # ids in decimal here, comments above classes are in hex
    if classs == 1:
        if id == 0x01:
            return ECEF((pl[0:4], U4),
                        (pl[4:8], I4),
                        (pl[8:12], I4),
                        (pl[12:16], I4),
                        (pl[16:], U4))
        elif id == 0x02:
            return LLH((pl[0:4], U4),
                       (pl[4:8], I4),
                       (pl[8:12], I4),
                       (pl[12:16], I4),
                       (pl[16:20], I4),
                       (pl[20:24], U4),
                       (pl[24:], U4))
        elif id == 0x03:
            # print("not long enough?", pl[12:], len(pl), length)
            return Status((pl[0:4], U4),
                          (pl[4:5], U1),
                          (pl[5:6], U1),
                          (pl[6:7], U1),
                          (pl[7:8], U1),
                          (pl[8:12], U4),
                          (pl[12:], U4))
        elif id == 0x06:
            # print(ba)
            return Solution((pl[0:4], U4),
                            (pl[4:8], I4),
                            (pl[8:10], I2),
                            (pl[10:11], U1),
                            (pl[12:16], I4),
                            (pl[16:20], I4),
                            (pl[20:24], I4),
                            (pl[24:28], I4),
                            (pl[28:32], I4),
                            (pl[32:36], I4),
                            (pl[36:40], I4),
                            (pl[40:44], U4),
                            (pl[44:46], U2),
                            (pl[47:48], U1))
        elif id == 0x13:
            # print(pl[20:21], pl[20])
            return HPECEF((pl[4:8], U4),
                          (pl[8:12], I4),
                          (pl[12:16], I4),
                          (pl[16:20], I4),
                          (pl[20:21], I1),
                          (pl[21:22], I1),
                          (pl[22:23], I1),
                          (pl[24:], U4),
                          (pl[23:24], U1))
        elif id == 0x14:
            return HPLLH((pl[4:8], U4),
                         (pl[8:12], I4),
                         (pl[12:16], I4),
                         (pl[16:20], I4),
                         (pl[20:24], I4),
                         (pl[24], I1),
                         (pl[25], I1),
                         (pl[26], I1),
                         (pl[27], I1),
                         (pl[28:32], U4),
                         (pl[32:], U4),
                         (pl[3], U1))
        elif id == 0x21:
            # print("pvt..?")
            return TimeUTC((pl[0:4], U4),
                           (pl[4:8], U4),
                           (pl[8:12], I4),
                           (pl[12:14], U2),
                           (pl[14:15], U1),
                           (pl[15:16], U1),
                           (pl[16:17], U1),
                           (pl[17:18], U1),
                           (pl[18:19], U1),
                           (pl[19:20], U1))
        elif id == 0x35:
            return SatInfo((pl[0:4], U4),
                           (pl[5:6], U1))
        elif id == 0x3B:
            # print("ITS A SURVEY YAAY")
            return SVIN((pl[8:12], U4),
                        (pl[12:16], I4),
                        (pl[16:20], I4),
                        (pl[20:24], I4),
                        (pl[24:25], I1),
                        (pl[25:26], I1),
                        (pl[26:27], I1),
                        (pl[28:32], U4),
                        (pl[32:36], U4),
                        (pl[36:37], U1),
                        (pl[37:38], U1))
        else:
            print("No id for", id, "in class 01-NAV")
            Log.NoMessageError(classs, id)