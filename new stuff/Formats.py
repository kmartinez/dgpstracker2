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


def decode(bytearr, format):
    try:
        if type(bytearr) is int:
            return bytearr
        # print("is", bytearr)
        return struct.unpack(format, bytearr)[0]
    except:
        print("Number decoding error")


def encode(val, format):
    try:
        if type(val) is bytearray:
            return val
        # print("is", bytearr)
        return struct.pack(format, val)
    except:
        print("Number encoding error")


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


def u1toBytes(val):
    return encode(val, "<B")


def u2toBytes(val):
    return encode(val, "<H")


def u4toBytes(val):
    return encode(val, "<L")


def i1toBytes(val):
    return encode(val, "<b")


def i2toBytes(val):
    return encode(val, "<h")


def i4toBytes(val):
    return encode(val, "<l")


def x1toBytes(bytearr):
    return encode(bytearr, "<c")


def x2toBytes(bytearr):
    return encode(bytearr, "<h")


def x4toBytes(bytearr):
    return encode(bytearr, "<l")


# fletcher's algorithm (8-bit)
def ubxChecksum(bytes):
    ck_a, ck_b = 0, 0
    for i in range(len(bytes)):
        ck_a += bytes[i]
        ck_b += ck_a

    # mask to preserve 8-bit
    ck_a &= 255
    ck_b &= 255

    return ck_a, ck_b


def verifyChecksum(payload, checksum):
    if type(payload) == list:
        payload = (payload[0], payload[1])

    return ubxChecksum(payload) == checksum

def padBytes(byte_string, N):
    if N == 0:
        return byte_string

    elen = len(byte_string) % N
    if elen:
        byte_string += byte_string(N - elen)