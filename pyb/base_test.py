# Title: base_test.py
# brief: Send High Precision NMEA message that are forwarded through the radio uart to the rover.
# author: Sherif Attia (sua2g16)
from pyb import UART
from pyb import RTC
# from Formats import *
from Message import *
# from Message import littleEndianOf, bigEndianOf, binaryParseUBXMessage
import time
import pyb

# from Emily's code
# source: main.py
MAX_CALIBRATE_FAILURES = 50
SVIN_CODE = -2
MAX_PACK_BUF = 25

RADIO_BUFFER_SIZE = 1024
RADIO_PORT = 1
RADIO_BAUDRATE = 115200

GPS_PORT = 4
GPS_BUFFER_SIZE = 512
GPS_BAUDRATE = 115200

radio_uart = UART(RADIO_PORT, RADIO_BAUDRATE)
radio_uart.init(RADIO_BAUDRATE, bits=8, stop=1, read_buf_len=RADIO_BUFFER_SIZE)

gps_uart = UART(GPS_PORT, GPS_BAUDRATE)
gps_uart.init(GPS_BAUDRATE, bits=8, stop=1, read_buf_len=GPS_BUFFER_SIZE)

# bytearray format
message_byte_buffer = bytearray()
# normal buffer - may not work
message_buffer = {}

# Enable Surveying-In
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
    gps_uart.write(bs)
    return bs

dgpsUsed = False
fixOK = False
# might be useful for visual status - green on fix etc.
def updateLEDs():
    global fixOK, dgpsUsed
    if fixOK:
        pyb.LED(2).on()
        pyb.LED(1).off()
    else:
        pyb.LED(2).off()
        pyb.LED(1).on()

    if dgpsUsed:
        pyb.LED(4).on()
    else:
        pyb.LED(4).off()


# Stop Surveying-in - To be used if conditions have been met.
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
    gps_uart.write(bs)
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
    gps_uart.write(bs)
    return bs


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
    global nextpack, pack_buf, calibrated, gpsIn
    if gpsIn is None or len(pack_buf) > MAX_PACK_BUF:
        return False
    print("Reading...", end="")
    calibrated = gpsIn.read(2) == b'\xb5\x62'
    if not calibrated:
        calibrated = calibrate()
        Log.CalibrateEvent().writeLog()
    if not calibrated:
        Log.CalibrationTimeoutEvent().writeLog()
        return False
    # print(calibrated)
    nextpack = bytearray(b'\xb5\x62')
    class_id = gpsIn.read(2)
    pack_len_bytes = gpsIn.read(2)
    pack_len = U2(pack_len_bytes)
    # print(pack_len_bytes,pack_len, "bytes long")

    if pack_len > 100 and class_id != bytearray(b'\x01\x35'):
        Log.UnacceptableLengthError(pack_len_bytes).writeLog()
        print(class_id)
        print("BAD LENGTH", pack_len)
        return False
    elif class_id == bytearray(b'\x01\x35'):
        print("Sat message, length capped...", end="")
        Log.LengthForceError(b'\x01', b'\x35', pack_len_bytes, u2toBytes(8)).writeLog()
        pack_len = 8
        pack_len_bytes = u2toBytes(pack_len)
    payload = gpsIn.read(pack_len)
    crc = gpsIn.read(2)
    if crc is None:
        crc = b'\x00\x00'
    # print(crc,"crc")
    try:
        nextpack.extend(class_id)  # append class and ID to byte
        nextpack.extend(pack_len_bytes)
        nextpack.extend(payload)
        nextpack.extend(crc)
        pack_buf.append(nextpack)
    except Exception as e:
        Log.UnknownError("Reading bytes from UART").writeLog()
        print(e)
        print("Error:")
        print(class_id)
        print(pack_len_bytes)
        print(payload)
        print(crc)
        print("End error")
        # log error?
        return False
    nextpack = None
    print("Finished.")
    return True


def updateTime(timeMsg):
    global clock, timeConfidence, TIME_CONF_LIMIT
    if type(timeMsg) is not TimeUTC or not timeMsg.validTime() or timeConfidence > 0:
        print("No clock update: ", timeConfidence)
        timeConfidence -= 1
        return
    print("!!! Updating clock !!!")
    # LCD.makeLCDBusy("Time update")
    Log.TimeUpdateEvent().writeLog()
    timeConfidence = TIME_CONF_LIMIT
    # assume Monday as gps doesn't give this data hence weekday=0
    # LCD.makeLCDFree()
    clock.datetime((timeMsg.getYear(), timeMsg.getMonth(), timeMsg.getDay(), 1,
                    timeMsg.getHour(), timeMsg.getMinute(), timeMsg.getSeconds(), timeMsg.getNano()))

def getMessageFromBuffer():
    global pack_buf, msg_buf, LOC_CODE, STAT_CODE, SATINF_CODE, NO_MSGS, TIMEUTC_ENABLED, fixOK, dgpsUsed
    if len(pack_buf) == 0:
        return None, -1
    print(len(pack_buf))
    byte_stream = pack_buf[0]
    del pack_buf[0]
    print(byte_stream)
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
        fixOK = msg.gpsFixOK
        dgpsUsed = msg.diffSol
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
    updateLEDs()  # update LEDs as readings taken - shows if fix dies during read
    return msg, code
# Code To be Modified LATER
# def searchForSVIN():
#     global SVIN_CODE
#     code=-1
#     while code != SVIN_CODE:
#         pyb.delay(200)
#         readBytes()
#         msg, code = getMessageFromBuffer()
#     return msg

# Code To be Modified LATER
# cursvin=None
# def toggleSVIN():
#     global surveying, cursvin
#     surveying = not surveying
#     LCD.surveying = not LCD.surveying
#     LCD.forceUpdateLCD()
#     if surveying:
#         print("Starting survey")
#         startSVIN(SVIN_DUR, SVIN_ACC)
#     elif not surveying and cursvin is not None:
#         print("Stopping survey")
#         stopSVIN(cursvin)
#     saveCFG()

# TODO: Checksum for ACK


print("Pyboard Green - Base")
# create a poll i.e. wait for incoming messages
print("Checking For Messages")
print("Forwarding to Radio UART")
PACKET_BUFFER_MESSAGE = bytearray()

#TODO:
# - Configure the base to send RTCM3 corrections
# - have the rover accept these messages
# - use these corrections to parse through the contents of an nmea format
# - send this information back to the base.

def parseMessage(message):
    ba = message
    valid = ba[0] == 0xb5 and ba[1] == 0x62
    if not valid:
        print("Data Corrupted")


while True:
    if gps_uart.any() == 0:
        print("Nothing Yet...")
        pyb.delay(500)
    elif gps_uart.any() > 0:
        PACKET_BUFFER_MESSAGE = bytearray(gps_uart.read())
        radio_uart.write(PACKET_BUFFER_MESSAGE)
        pyb.delay(500)
        # need to decode incoming byte formatted data
        # TODO: Validate that information is in the right format
        #   Send an ACK back to the rover continue sending messages.
        if radio_uart.any() > 0:
            messages = radio_uart.readline()
            # print(radio_uart.readline())
            print(messages)
            # can use ubxChecksum and VerifyChecksum() from Formats
            # need to check message format (or just read the checksum bytes and make sure they are valid.)
            # when we receive anything from the radio, we need to verify that the checksum (using crc) is of
            # the right length

            # check message header must be 0xb5 and 0x62
            try:
                readBytes()
                message, code = getMessageFromBuffer()
            except:
                message = None
                code = -1
            pyb.delay(500)
        else:
            print("Nothing in buffer, waiting for message...")
            pyb.delay(1000)

