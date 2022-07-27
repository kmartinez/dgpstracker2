# Title: base_test.py
# brief: Send High Precision NMEA message that are forwarded through the radio uart to the rover.
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

print("Pyboard Green - Base")
# create a poll i.e. wait for incoming messages
print("Checking For Messages")
print("Forwarding to Radio UART")
PACKET_BUFFER_MESSAGE = bytearray()
while True:
    if gps_uart.any() == 0:
        print("Nothing Yet...")
        pyb.delay(500)
    elif gps_uart.any() > 0:
        PACKET_BUFFER_MESSAGE = bytearray(gps_uart.read())
        radio_uart.write(PACKET_BUFFER_MESSAGE)
        pyb.delay(500)
        # need to decode incoming byte formatted data
        if radio_uart.any() > 0:
            print(radio_uart.readline())
            pyb.delay(500)

