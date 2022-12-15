'''Alternative main file for calibrating the RTC and setting it's first alarm time'''
import board
import adafruit_ds3231
from time import struct_time
from config import *

I2C = board.I2C()
RTC = adafruit_ds3231.DS3231(I2C)

#Set current date and time here
#(year, month, day, hour, minute, second)
RTC.datetime = struct_time((2022,11,8,23,59,59,-1,-1,-1))