# Write your code here :-)
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


print("Pyboard Black - Rover Board")
# create a poll i.e. wait for incoming messages
print("Waiting for incoming messages...")
while True:
    if radio_uart.any() > 0:
        #         print("Incoming...")
        data = radio_uart.readline()
        #         data = str(data.decode()) - can't be decode if receiving rtcm messages
        #         print(data)
        #         print(processGPS(data))
        print("Receiving RTCM Corrections")
        # storing corrections into a byte array buffer
        PACKET_MANAGER = bytearray(data)
        # forwarding corrections to rover to gps
        gps_uart.write(PACKET_MANAGER)

        print("Reading Messages")
        gps_rover_data = gps_uart.readline()
        if gps_rover_data is None:
            continue
        #             print(gps_rover_data)
        # need to ignore the contents / skip this message and force the loop to continue
        gps_rover_data = str(gps_rover_data.decode())

        if gps_rover_data.count("$") > 1:
            continue
        #         print(gps_rover_data)
        #         print(data)

        if gpsFormatOutput(ROVER_ID, gps_rover_data) is None:
            continue
        if gpsFormatOutput(ROVER_ID, gps_rover_data)[0] == "p":
            radio_uart.write("3D/DGNSS/FIXED\n")
            fixed_message = gpsFormatOutput(ROVER_ID, gps_rover_data)[1]
            final_message = (
                str(fixed_message[0])
                + ", "
                + str(fixed_message[1])
                + ", "
                + str(fixed_message[2])
                + ", "
                + str(fixed_message[3])
                + ", "
                + str(fixed_message[4])
                + ", "
                + str(fixed_message[5])
                + ", "
                + str(fixed_message[6])
                + ", "
                + str(fixed_message[7])
                + "\n"
            )

            radio_uart.write(final_message)
            # might complain, thus might have to put it in a BUFFER
            processed_data = gpsFormatOutput(ROVER_ID, gps_rover_data)
            print(processed_data)
        #             PACKET_MANAGER = bytearray(processed_data.decode())
        #             radio_uart.write(PACKET_MANAGER)
        if gpsFormatOutput(ROVER_ID, gps_rover_data) is not None:
            print(gpsFormatOutput(ROVER_ID, gps_rover_data))
            radio_uart.write("Message Received - Incoming Payload\n")

    #            if gps_uart.any() > 0:
    #                 PACKET_MANAGER = bytearray(gps_uart.read())

    #                 radio_uart.write(PACKET_MANAGER)

    # process incoming nmea messages - split them up and define them separately to get an nmea fix.
    #         print(data)
    #         print(radio_uart.readline())
    # need to decode incoming byte formatted data
    # need to send back a message to confirm that we got a fix.

    # send back data to base.
    pyb.delay(500)
