# U1 Unsigned char
# I1 Signed char, 2c
# X1 bitfield (1 byte)
# U2 unsigned short
# I2 signed short 2c
# X2 bitfield (2 bytearr)
# U4 Unsigned long
# I4 signed long
# X4 bitfield (4 bytearr)
import struct

conversions = {
    "mm": .001,
    "cm": .01,
    "deg": .0000001,
    "ecefhp": .1,
    "llhhp": .01,
    "unit": 1,
    "ms": .001
}


def getConversionFactor(unit="unit"):
    global conversions
    try:
        return conversions[unit]
    except:
        return 1


def signed(bytearr):
    if type(bytearr) is int:
        return bytearr
    # print("is", bytearr)
    return struct.unpack("<l", bytearr)[0]


def unsigned(bytearr):
    if type(bytearr) is int:
        return bytearr
    # print("is", bytearr)
    return struct.unpack("<L", bytearr)[0]


def decode(bytearr, format):
    if type(bytearr) is int:
        return bytearr
    # print("is", bytearr)
    return struct.unpack(format, bytearr)[0]


def U1(bytearr):
    return decode(bytearr, "<B")


def U2(bytearr):
    return decode(bytearr, "<H")


def U4(bytearr):
    return decode(bytearr, "<L")


def I1(bytearr):
    return decode(bytearr, "<b")


def I2(bytearr):
    return decode(bytearr, "<h")


def I4(bytearr):
    i = decode(bytearr, "<l")
    # print(bytearr, "is signed I4 as", i)
    return i


def X1(bytearr):
    return bytearr


def X2(bytearr):
    return bytearr


def X4(bytearr):
    return bytearr
