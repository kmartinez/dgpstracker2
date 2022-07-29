# Title: rover_test.py
# brief: validate that rover can received forwarded messages from base
# author: Sherif Attia (sua2g16)
#
from pyb import UART
from pyb import RTC
from gps import *
import time
import pyb

ROVER_ID = str(1)

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

PACKET_MANAGER = bytearray()

print("Pyboard Black - Rover")
# create a poll i.e. wait for incoming messages
print("Waiting for incoming messages...")
while True:
    if radio_uart.any() > 0:
        #         print("Incoming...")
        data = radio_uart.readline()
        # TODO: Forward incoming Radio Data from radio_uart to gps_uart
        # Forwarding incoming radio data stored in data variable and storing in PACKET_MANAGER
        # This will be written to the gps_uart.
        PACKET_MANAGER = bytearray(data)
        # what happens when you write incoming messages from the base gps_uart to the rover gps_uart?
        # What kind of messages is it expecting?
        # What kind of messages should it pass back to the base.
        gps_uart.write(PACKET_MANAGER)

        data = str(data.decode())
        #         print(data)
        #         print(processGPS(data))

        if gpsFormatOutput(ROVER_ID, data) is None:
            continue
        if gpsFormatOutput(ROVER_ID, data)[0] == 'p':
            radio_uart.write("3D/DGNSS/FIXED")
        if gpsFormatOutput(ROVER_ID, data) is not None:
            print(gpsFormatOutput(ROVER_ID, data))
            #             position, location = gpsFormatOutput(ROVER_ID, data)
            #             if position.startswith('p'):
            radio_uart.write("Message Received - Incoming Payload\n")
            #             radio_uart.write(bytearray(gpsFormatOutput(ROVER_ID,data)))
            if gps_uart.any() > 0:
                PACKET_MANAGER = bytearray(gps_uart.read())
                #         radio_uart.write("Message Received - Incoming Payload")
                radio_uart.write(PACKET_MANAGER)

        # process incoming nmea messages - split them up and define them separately to get an nmea fix.
    #         print(data)
    #         print(radio_uart.readline())
    # need to decode incoming byte formatted data
    # need to send back a message to confirm that we got a fix.

    # send back data to base.
    pyb.delay(500)

#TODO: Need to write a function that can split and parse nmea messages
# General behaviour - check for incoming nmea messages
#

