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


# 01 01
class ECEF:
    iTOW = None
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


# 01 02
class LLH:
    iTOW = None
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
class Status:
    iTOW = None
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
        self.fixStat = fixstat
        self.flags = flags

        # translate flags to variables
        self.towValid = flags & 8 == 8
        self.wknValid = flags & 4 == 4
        self.diffSol = flags & 2 == 2
        self.gpsFixOK = flags & 1 == 1

        self.solInvalid = fixstat & 2 == 2

        self.ttff = ttff
        self.flags2 = flags2
        self.msss = msss

        try:
            self.gpsFix = fixes[fix]
        except:
            print(fix)
            self.gpsFix = "E - Reserved " + str(flags) + " " + str(fixstat)


# 01 06
class Solution:
    iTOW = None
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
        self.iTOW = tow
        self.ecefX = x + (xhp * .01)
        self.ecefY = y + (yhp * .01)
        self.ecefZ = z + (zhp * .01)
        self.ecefX = xhp
        self.ecefY = yhp
        self.ecefZ = zhp
        self.pAcc = pacc * .1
        self.invalidFix = flags == 1


# Precise longitude in deg * 1e-7 = lon + (lonHp * 1e-2).
# 01 14
class HPLLH(LLH):
    iTOW = None
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
class SatInfo:
    iTOW = None
    numSvs = None

    # there is more information but I don't know if I need it yet

    def __init__(self, tow, nosats):
        self.iTOW = tow
        self.numSvs = nosats


class TimeUTC:
    iTOW = None
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


def parseUBXMessage(msg):
    # ba = msg.split(" ")
    ba = msg
    # print(ba[6:14])
    confirm = ba[0] == 181 and ba[1] == 98
    if not confirm:
        pass
        print("Data corrupted: bit code")

    # print(ba)

    classs = U1(ba[2])
    id = U1(ba[3])
    length = U2(ba[4:6])  # little endian for length, only defines length of payload
    # also note is number of bytes in pl not bits

    cid = [classs, id]
    # print(cid)

    pl = ba[6:-2]
    crc = (ba[-2:])
    # print(id)
    # print(len(pl))
    # crc = int(ba[-2] + ba[-1], 16)

    if length != (len(ba) - 6 - 2):
        pass
        # print("Data corrupted: CRC")

    # ids in decimal here, comments above classes are in hex
    if classs == 1:
        if id == 1:
            return ECEF(U4(pl[0:4]),
                        I4(pl[4:8]),
                        I4(pl[8:12]),
                        I4(pl[12:16]),
                        U4(pl[16:]))
        elif id == 2:
            return LLH(U4(pl[0:4]),
                       I4(pl[4:8]),
                       I4(pl[8:12]),
                       I4(pl[12:16]),
                       I4(pl[16:20]),
                       U4(pl[20:24]),
                       U4(pl[24:]))
        elif id == 3:
            # print("not long enough?", pl[12:], len(pl), length)
            return Status(U4(pl[0:4]),
                          U1(pl[4]),
                          X1(pl[5]),
                          X1(pl[6]),
                          X1(pl[7]),
                          U4(pl[8:12]),
                          U4(pl[12:]))
        elif id == 6:
            # print(ba)
            return Solution(U4(pl[0:4]),
                            I4(pl[4:8]),
                            I2(pl[8:10]),
                            U1(pl[10]),
                            X1(pl[12:16]),
                            I4(pl[16:20]),
                            I4(pl[20:24]),
                            I4(pl[24:28]),
                            I4(pl[28:32]),
                            I4(pl[32:36]),
                            I4(pl[36:40]),
                            U4(pl[40:44]),
                            U2(pl[44:46]),
                            U1(pl[47]))
        elif id == 19:
            return HPECEF(U4(pl[4:8]),
                          I4(pl[8:12]),
                          I4(pl[12:16]),
                          I4(pl[16:20]),
                          I1(pl[20]),
                          I1(pl[21]),
                          I1(pl[22]),
                          U4(pl[24:]),
                          X1(pl[23]))
        elif id == 20:
            return HPLLH(U4(pl[4:8]),
                         I4(pl[8:12]),
                         I4(pl[12:16]),
                         I4(pl[16:20]),
                         I4(pl[20:24]),
                         I1(pl[24]),
                         I1(pl[25]),
                         I1(pl[26]),
                         I1(pl[27]),
                         U4(pl[28:32]),
                         U4(pl[32:]),
                         X1(pl[3]))
        elif id == 33:
            # print("pvt..?")
            return TimeUTC(U4(pl[0:4]),
                           U4(pl[4:8]),
                           I4(pl[8:12]),
                           U2(pl[12:14]),
                           U1(pl[14]),
                           U1(pl[15]),
                           U1(pl[16]),
                           U1(pl[17]),
                           U1(pl[18]),
                           X1(pl[19]),
                           )
        elif id == 53:
            return SatInfo(U4(pl[0:4]),
                           X1(pl[5]))
        else:
            print("No id for", id, "in class 01-NAV")

def binaryParseUBXMessage(msg):
    # ba = msg.split(" ")
    ba = msg
    # print(ba[6:14])
    confirm = ba[0] == 181 and ba[1] == 98
    if not confirm:
        pass
        print("Data corrupted: bit code")

    # print(ba)

    classs = U1(ba[2])
    id = U1(ba[3])
    length = U2(ba[4:6])  # little endian for length, only defines length of payload
    # also note is number of bytes in pl not bits

    cid = [classs, id]
    # print(cid)

    pl = ba[6:-2]
    crc = (ba[-2], ba[-1])

    corrupted = verifyChecksum(pl, crc)

    # print(id)
    # print(len(pl))
    # crc = int(ba[-2] + ba[-1], 16)

    if length != (len(ba) - 6 - 2):
        pass
        # print("Data corrupted: CRC")

    # ids in decimal here, comments above classes are in hex
    if classs == 1:
        if id == 1:
            return ECEF(pl[0:4],
                        pl[4:8],
                        pl[8:12],
                        pl[12:16],
                        pl[16:])
        elif id == 2:
            return LLH(pl[0:4],
                       pl[4:8],
                       pl[8:12],
                       pl[12:16],
                       pl[16:20],
                       pl[20:24],
                       pl[24:])
        elif id == 3:
            # print("not long enough?", pl[12:], len(pl), length)
            return Status(pl[0:4],
                          pl[4],
                          pl[5],
                          pl[6],
                          pl[7],
                          pl[8:12],
                          pl[12:])
        elif id == 6:
            # print(ba)
            return Solution(pl[0:4],
                            pl[4:8],
                            pl[8:10],
                            pl[10],
                            pl[12:16],
                            pl[16:20],
                            pl[20:24],
                            pl[24:28],
                            pl[28:32],
                            pl[32:36],
                            pl[36:40],
                            pl[40:44],
                            pl[44:46],
                            pl[47])
        elif id == 19:
            return HPECEF(pl[4:8],
                          pl[8:12],
                          pl[12:16],
                          pl[16:20],
                          pl[20],
                          pl[21],
                          pl[22],
                          pl[24:],
                          pl[23])
        elif id == 20:
            return HPLLH(pl[4:8],
                         pl[8:12],
                         pl[12:16],
                         pl[16:20],
                         pl[20:24],
                         pl[24],
                         pl[25],
                         pl[26],
                         pl[27],
                         pl[28:32],
                         pl[32:],
                         pl[3])
        elif id == 33:
            # print("pvt..?")
            return TimeUTC(pl[0:4],
                           pl[4:8],
                           pl[8:12],
                           pl[12:14],
                           pl[14],
                           pl[15],
                           pl[16],
                           pl[17],
                           pl[18],
                           pl[19])
        elif id == 53:
            return SatInfo(pl[0:4],
                           pl[5])
        else:
            print("No id for", id, "in class 01-NAV")
