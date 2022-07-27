# Title: rover_test.py
# brief: validate that rover can received forwarded messages from base
# author: Sherif Attia (sua2g16)
from pyb import UART
from pyb import RTC
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

PACKET_MANAGER = bytearray()

print("Pyboard Black - Rover")
# create a poll i.e. wait for incoming messages
print("Waiting for incoming messages...")
message = "Message Received - Incoming Payload\n"
while True:
    if radio_uart.any() > 0:
        print("Incoming...")
        print(radio_uart.readline())
        # need to decode incoming byte formatted data
        # need to send back a message to confirm that we got a fix.
        # send back data to base.
        radio_uart.write(message)
        if gps_uart.any() > 0:
            PACKET_MANAGER = bytearray(gps_uart.read())
            #         radio_uart.write("Message Received - Incoming Payload")
            radio_uart.write(PACKET_MANAGER)
    pyb.delay(500)

