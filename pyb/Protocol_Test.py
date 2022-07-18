# Title: Protocol_Test.py
# @brief: try to verify communication is going through from gps uart to radio uart
# Author: Sherif Attia
# Date:   15/07/2022

# Importing necessary modules
import pyb
from pyb import UART
from pyb import RTC
import time

# Global Variables
rtc = RTC()

GPS_BUFFER_SIZE = 512
GPS_PORT = 6
GPS_BAUDRATE = 38400
gps_uart = UART(GPS_PORT, GPS_BAUDRATE)
gps_uart.init(GPS_BAUDRATE, bits=8, parity=None, stop=1, read_buf_len=GPS_BUFFER_SIZE)

RADIO_BUFFER_SIZE = 1024
RADIO_PORT = 3
RADIO_BAUDRATE = 38400
radio_uart = UART(RADIO_PORT, RADIO_BAUDRATE)
radio_uart.init(RADIO_BAUDRATE, bits=8, stop=1, read_buf_len=RADIO_BUFFER_SIZE)


PACKET_BUFFER = []  # stores a bytearray
RADIO_BUFFER = []


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


# TODO: write these to the radio_uart buffer
# fill the packets up byte by byte until full
def writeToRadio():
    # attempt to read messages from gps uart
    pollMessages()
    global radio_uart, RADIO_BUFFER
    if gps_uart.read():
        RADIO_BUFFER = pollMessages()
        for data in RADIO_BUFFER:
            if data != b'':
                radio_uart.write(data)
            else:
                return False
    print("Successfully written to radio uart")


while True:
    # print(pollMessages())
    writeToRadio()
    time.sleep_ms(1000)
    print(radio_uart.read())
#     writeToRadio()
