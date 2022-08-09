# Title: base_test.py
# brief: Send High Precision NMEA message that are forwarded through the radio uart to the rover.
# author: Sherif Attia (sua2g16)
from pyb import UART
from pyb import RTC
from Formats import *
import time
import pyb

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
            # need to check message format (or just read the checksum bytes and make sure they are valid.)
            pyb.delay(500)
        else:
            print("Nothing in buffer, waiting for message...")
            pyb.delay(1000)

