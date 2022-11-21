# Title: code.py
# Author: Sherif Attia
# Date: 28/10/2022

# TODO: Import libraries
# import adafruit_ds3231 - throws error - might need an external RTC
import time
import alarm
import board
import digitalio
import time
import busio

# External Libs
from adafruit_debouncer import Debouncer
from adafruit_ds3231 import DS3231


# TODO: Create Global Variables
# TODO: Test the ability of writing to a file on flash - using old code
RETRY = 3
FILE_PATH = "Readings/incoming_data.txt"
is_logging = False
LED = digitalio.DigitalInOut(board.D13)
LED.direction = digitalio.Direction.OUTPUT
# Note Time is in seconds!

uart = busio.UART(board.TX, board.RX, baudrate=115200, timeout=10)
i2c = board.I2C()
message = bytearray("acknowledge")

# message = "Counter: "
count = 0
print("Transmitting")
while True:
    #TODO: send an ACK Packet - confirm that it's been received by the feather, then start counter.
    # uart.write(message)
    # print(len(message))
    # time.sleep(1)

    # count += 1
    # final_message = str(count) 
    # data = bytearray(final_message)
    # print(len(data))
    # print(data)

    # LED.value = True

    # uart.write(data)
    # # print("Successfully sent")
    # print("sent")
    # time.sleep(1)

    # LED.value = False


    #Check to see if if you received an ACK
    if uart.read(10) is None:
        print("nothing")
        # time.sleep(1)
        continue
    else:
        print(uart.read(10))
        # time.sleep(1)


