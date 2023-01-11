'''Alternative main file for setting the RTC's first alarm time.
Use after setting up config.py. Easiest method is to changed the datetime below and copy + paste the code into an active REPL'''
import board
import adafruit_ds3231
import time
from time import struct_time
from config import *

I2C = board.I2C()
RTC = adafruit_ds3231.DS3231(I2C)

#Set first alarm date and time here (year and month are ignored)
first_alarm_time = struct_time([2022,12,15,16,20,0,-1,-1,-1])

RTC.alarm1 = (first_alarm_time, "monthly")
RTC.alarm1_status = False