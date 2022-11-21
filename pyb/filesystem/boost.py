#boot.py - filesystem handler to be used with data_logger
#Author: Sherif Attia
#Date: 22/12/2021

import board, digitalio, time, storage
from adafruit_debouncer import Debouncer


button_record = digitalio.DigitalInOut(board.D13)
button_record.switch_to_input(pull=digitalio.Pull.UP)   #switch_to_input will wait until it detects an input from the button


# Debouncer function
# def debouncable(pin):
#     switch_io = digitalio.DigitalInOut(pin)
#     switch_io.direction = digitalio.Direction.INPUT
#     switch_io.pull = digitalio.Pull.UP
#     return switch_io

# button_b = Debouncer(debouncable(board.D21))  #IO38

#create flag variables


#if switch pin is connected to ground CircuitPython can write to the drive
storage.remount("/", not(button_record.value))
