# Write your code here :-)
from pyb import UART
from pyb import RTC
from gps import *
from Formats import *
import time
import pyb

# Flag to check if rover has achieved a fix of 3D/DGNSS/FIXED
fixed = False
# List of Fix Modes - goes through each one to assess fix type
# if fix_type[4] achieved, then proceed with remaining functions
# reference: https://www.ardusimple.com/question/3d-dgnss-float-fixed-what-meaning-exactly/
fix_type = ['3D', '3D/FLOAT, 3D/DGNSS', '3D/FIXED', '3D/DGNSS/FIXED']

rtc = pyb.RTC()

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


def saveCFG():
    bs = bytearray()
    bs.append(0xB5)
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
        #         print("Receiving RTCM Corrections")
        # storing corrections into a byte array buffer
        PACKET_MANAGER = bytearray(data)
        # forwarding corrections to rover to gps
        gps_uart.write(PACKET_MANAGER)

        #         print("Reading Messages")
        gps_rover_data = gps_uart.readline()
        if gps_rover_data is None:
            continue
        #             print(gps_rover_data)
        # need to ignore the contents / skip this message and force the loop to continue
        gps_rover_data = str(gps_rover_data.decode())

        if gps_rover_data.count("$") > 1 or (len(gps_rover_data) < 82):
            continue
        #         print(gps_rover_data)
        #         print(data)

        if gpsFormatOutput(ROVER_ID, gps_rover_data) is None:
            continue
        # TODO:
        #   Check the fix type - use an isFixed Flag
        #   If it it has a fix, then send back the data to the rover.
        #   need to figure out fix type - check with fix_type to progress with operations.

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

        # TODO: retrieve incoming Time Of Day information.
        #   Feed that information back to the RTC
        #   Check whether the information matches that of the available time slots.

        if gpsFormatOutput(ROVER_ID, gps_rover_data)[0] == "t":
            time_message = gpsFormatOutput(ROVER_ID, gps_rover_data)[1]
            # reference: programcreek.com/python/example/99858/pyb.RTC
            t = time.mktime((int(time_message[1]),
                         int(time_message[2]),
                         int(time_message[3]),
                         int(time_message[4]),
                         int(time_message[5]),
                         int(time_message[6]),
                         0, 0))
            # NOT TESTED YET
            rtc.datetime((int(time_message[1]),  # year
                         int(time_message[2]),   # month
                         int(time_message[3]),   # day
                          0,                     # weekday
                         int(time_message[4]),   # hours
                         int(time_message[5]),   # minutes
                         int(time_message[6]),   # seconds
                          0))

            final_message = (
                str(time_message[0])
                + ", "
                + str(time_message[1])
                + ", "
                + str(time_message[2])
                + ", "
                + str(time_message[3])
                + ", "
                + str(time_message[4])
                + ", "
                + str(time_message[5])
                + ", "
                + str(time_message[6])
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
