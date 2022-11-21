# Write your code here :-)

#from datetime import datetime
from pyb import UART
import machine
from pyb import RTC
import time
from Formats import *
#import ntptime
import pyb


# rtc = RTC()

# GPS_BUFFER_SIZE = 512
# GPS_PORT = 6
# GPS_BAUDRATE = 38400
# gps_uart = UART(GPS_PORT, GPS_BAUDRATE)
# gps_uart.init(GPS_BAUDRATE, bits=8, parity=None, stop=1, read_buf_len=GPS_BUFFER_SIZE)

CHECK_BYTES = 2

RADIO_BUFFER_SIZE = 1024
RADIO_PORT = 1
RADIO_OTHER_PORT = 2

GPS_PORT = 4
GPS_BUFFER_SIZE = 512
GPS_BAUDRATE = 115200

RADIO_BAUDRATE = 115200
radio_uart = UART(RADIO_PORT, RADIO_BAUDRATE)
radio_uart.init(RADIO_BAUDRATE, bits=8, stop=1, read_buf_len=RADIO_BUFFER_SIZE)

gps_uart = UART(GPS_PORT, GPS_BAUDRATE)
gps_uart.init(GPS_BAUDRATE, bits=8, stop=1, read_buf_len=GPS_BUFFER_SIZE)

PACKET_BUFFER = []  # stores a bytearray
# PACKET_BUFFER = bytearray()
# RADIO_BUFFER = []
RADIO_BUFFER = bytearray()

#maybe there is a way to get the time from the PC?
word = 'Communication Established.'
byte_message = bytearray(b'\x08\x09\x10\n')
int_value = bytearray(5)
word_byte = str.encode(word)
# print(type(word_byte)) - converted to bytes

# Enable Surveying In
surveying = False
def startSVIN(dur=600, acc=2500):
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

# Stop Surveying-In - to be used if conditions have been met.
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


# Save Configurations
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

# def searchForSVIN():
#     global SVIN_CODE
#     code=-1
#     while code != SVIN_CODE:
#         pyb.delay(200)
#         readBytes()
#         msg, code = getMessageFromBuffer()
#     return msg
#
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

def checkMessage():
    global PACKET_BUFFER
    print("Checking for message")
    #GPS Uart check preamble sync characters
#     if gps_uart.read(2) != b'\xb5\x62':
#         return False
    print("Forwarding to Radio Uart")
    PACKET_BUFFER = bytearray(gps_uart.read())
    while True:
        radio_uart.write(PACKET_BUFFER)
        pyb.delay(500)
        if radio_uart.any() > 0:
            radio_uart.read()
            pyb.delay(500)

print('Pyboard green - Base')

print("Checking for message")
    #GPS Uart check preamble sync characters
#     if gps_uart.read(2) != b'\xb5\x62':
#         return False
print("Forwarding to Radio Uart")
PACKET_BUFFER_MESSAGE = bytearray()
while True:
    if gps_uart.any == 0:
        print("Nothing yet")
        pyb.delay(1000)
    elif gps_uart.any() > 0:
        # TODO: append checksum checker
        PACKET_BUFFER_MESSAGE = bytearray(gps_uart.read())
        radio_uart.write(PACKET_BUFFER_MESSAGE)
        pyb.delay(500)
#         print("Checking for fix")
        if radio_uart.any() > 0:
            data = radio_uart.readline()
            #TODO: Write any incoming data to to a file, appended to a timestamp
            final_data = str(data.decode())
#             print("=" * 20)
            print(str(final_data))
            # open file on SD card and write incoming messages appended with timestamp
            # TODO: receive Timestamp using RTC
            # TODO: receive incoming messages appended to timestamp

            # TODO: store these strings into the file and write them every 10 seconds to the file.
            pyb.delay(1000)
        else:
            print("Nothing in buffer, waiting for message...")
            pyb.delay(1000)






