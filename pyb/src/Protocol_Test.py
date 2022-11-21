# Title: Protocol_Test.py
# @brief: try to verify communication is going through from gps uart to radio uart
# Author: Sherif Attia
# Date:   15/07/2022

# Importing necessary modules
import pyb
from pyb import UART
from pyb import RTC
from Formats import *
import time

# Global Variables
rtc = RTC()

GPS_BUFFER_SIZE = 512
GPS_PORT = 6
GPS_BAUDRATE = 115200
gps_uart = UART(GPS_PORT, GPS_BAUDRATE)
gps_uart.init(GPS_BAUDRATE, bits=8, parity=None, stop=1, read_buf_len=GPS_BUFFER_SIZE)

RADIO_BUFFER_SIZE = 1024
RADIO_PORT = 3
RADIO_BAUDRATE = 115200
radio_uart = UART(RADIO_PORT, RADIO_BAUDRATE)
radio_uart.init(RADIO_BAUDRATE, bits=8, stop=1, read_buf_len=RADIO_BUFFER_SIZE)


PACKET_BUFFER = []  # stores a bytearray
RADIO_BUFFER = []

#TODO: set the parameters for the configuraiton
# every time we power it down we want it to save its current configuration
# allow ability to start survey-in
# have function to stop survey-in
# have function to save configuration to stop board from resetting configuration to rover

surveying = False


# start Survey-in process. Should support a duration of 60s and an accuracy of around 2.5m
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


# stop Surveypin process.
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


# TODO: Initialise RTC & UART Communication
# rtc init
# def initRTC(rtc):
    # get realtime date time from rtc
    # rtc.datetime()
    # compare rtc datetime with gps

# def initUART():
# uart init
#TODO:
# Copy incoming data to Radio
# setup radio uart and gps uart
# verify that messages are coming in and are stored to the gps uart
# write these messages over to the radio uart.

# TODO: verify messages are being read from the gps uart port
# verify messages are coming through
def pollMessages():
    global gps_uart, PACKET_BUFFER
    if gps_uart.any() == 0:
        return False
#     else:
    print("Reading...", end="")
    # reading each bit of data byte by byte
    message = bytearray(gps_uart.read())
    PACKET_BUFFER = [message]
    return PACKET_BUFFER

# TODO: on confirmation, store these messages in a bytearray - byte by byte
# validate messages are being sent to the radio
# def confirmMessages():


#TODO: write these to the radio_uart buffer
# fill the packets up byte by byte until full
def writeToRadio():
    # attempt to read messages from gps uart
    pollMessages()
    global radio_uart, RADIO_BUFFER
    if gps_uart.any() > 0:
        RADIO_BUFFER = pollMessages()
        for data in RADIO_BUFFER:
            if data != b'':
                radio_uart.write(data)
            else:
                return False
    print("Successfully written to radio uart")


#TODO: acknowledge receiving code response


NUMBER_OF_BYTES = 10
def acceptResponse():
    if gps_uart.any() > 0:
        PACKET_MESSAGE_BUFFER = bytearray(gps_uart.read(NUMBER_OF_BYTES))
        # forward byte array contents to the radio_uart
        # for data in PACKET_MESSAGE_BUFFER:
        radio_uart.write(PACKET_MESSAGE_BUFFER)
        while True:
            if radio_uart.any() > 0:
                print(radio_uart.read())
                pyb.delay(1000)

#TODO: Listen uart1 for nmea fixes
# Rover Loop
# check xb5 and x62 as the first two bytes in hex format to be coming in when reading from the uart
# RTCM pending -> send them to GPS
# So it's the reverse of the base
# Once that works, it can move onto processing NMEA from GPS to see if fix type == 4
# if it does it can send the fix back down the radio
# it gets both ends using the radio

# ROVER LOOP
def roverCorrections():
    gps_uart.read()

while True:
    # print(pollMessages())
    writeToRadio()
    time.sleep_ms(1000)
    print(radio_uart.read())
#     writeToRadio()
