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
FILE_PATH = "Readings/incoming_data.txt"
is_logging = False
LED = digitalio.DigitalInOut(board.D13)
LED.direction = digitalio.Direction.OUTPUT
# Note Time is in seconds!

uart = busio.UART(board.TX, board.RX, baudrate=115200, timeout=10)
i2c = board.I2C()
ds3231 = DS3231(i2c)
# ds3231.datetime() returns a struct_time(y,m,d,h,m,s,wd,yd, -1)
# read the incoming timing data and write it into the RTC of this board.
# it takes a tuple anyways
# ds3231.datetime = time.struct_time()  # provide tuple of information

# def radio_init(self):
#     self.uart = busio.UART(board.TX, board.RX, baudrate=115200, timeout=10)

def radio_comms():
    # radio_init()
    if uart.any() > 0:
        uart.readline()
        time.sleep(1)

    
# Debouncer function
def debouncable(pin):
    switch_io = digitalio.DigitalInOut(pin)
    switch_io.direction = digitalio.Direction.INPUT
    switch_io.pull = digitalio.Pull.UP
    return switch_io

# External Button
button_d12 = Debouncer(debouncable(board.D12))
def data_logger(but_flag, is_logging):
    try:
        print("Ready to log")
        while but_flag:
            button_d12.update()
            if button_d12.fell:
                print("Button pressed")
                print(button_d12.fell)
                but_flag = False
        print("Logging...")
        is_logging = True

        with open(FILE_PATH, "w") as fp:
            fp.write("Timestamp     Data")
            initial_time = time.monotonic()
            initial_t = initial_time()
            while is_logging:
                second_time = time.monotonic()
                if (sec_time - initial_time) >= 1:
                    time_stamp = sec_time - initial_t
                    sec_time = 0
                    initial_time = time.monotonic()
                    fp.write("{}".format(time_stamp) + "{}".format(initial_t) )

    except OSError as e:  # Typically when the filesystem isn't writeable...
        delay = 0.5  # ...blink the LED every half second.
        if e.args[0] == 28:  # If the file system is full...
            delay = 0.25  # ...blink the LED faster!
        while True:
            if is_logging:
                LED.value = not LED.value
                time.sleep(delay)


# TODO: try testing deep sleep mode
def deep_sleep_mode():
    ALARM_TIME = 10
    time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + ALARM_TIME)
    # pin_alarm = alarm.pin.PinAlarm(board.D5, False)
    alarm.exit_and_deep_sleep_until_alarms(time_alarm) # Pretending to deep sleep...

def test_led():
    LED.value = True
    time.sleep(0.5)
    LED.value = False
    time.sleep(5)

def onboard_counter():
    count = 0
    while True:
        count += 1
        print(count)
        LED.value = True
        time.sleep(1)
        LED.value = False
        # time.sleep(1)
        button_d12.update()
        if button_d12.fell:
            print("Exited")
            break;

# TODO: Try including this library for the RTC
# TODO: Include Flags

button_flag = True
logging = False

while True:
    """_summary_: Filesystem main loop that effectively needs boot.py to be present to be able to write data into incoming data.txt
                  General Operation currently runs a simple timestamp - not accurate but acts as a template to be fixed
                  Currently relies on a push-button on pin D12 with an LED to interface with - flash once a second and it's working; 0.5s and it's not working
                  NB: To work properly, please make sure that boot.py is present on the board. It will force the board into read-only mode and can only be changed on the REPL.
                  To make changes to the code, please change the name of boot.py to something else like boost.py using os.rename on the REPL.
                  Final Notes: Any changes in your code requires you to reset the board so that it enters Read-Only mode, and vice-versa.
    """
    button_d12.update()
    if button_d12.fell:
        print("Pressed")
        print("Writing to Filesystem")
        # onboard_counter() # internal function callback doesn't work - need to find a solution around this
        count = 0
        try:
            print("Ready to Log...")
            while button_flag:
                button_d12.update()
                if button_d12.fell:
                    print("Button Pressed")     
                    print(button_d12.fell)
                    button_flag = False
            print("Logging...")
            is_logging = True
            with open(FILE_PATH, "w") as fp:
                fp.write("Timestamp\tLongitude\tLatitude\tFix Quality\n")
                initial_time = time.monotonic()
                initial_t = initial_time
                while is_logging:
                    sec_time = time.monotonic()
                    if (sec_time - initial_time) >= 1:
                        time_stamp = sec_time - initial_t
                        sec_time = 0
                        initial_time = time.monotonic()
                        #   Writes time-stamp   \t  Longitude   \t  Latitude    \t  Fix Quality
                        fp.write("{}".format(time_stamp) + "\t"
                         +  "{}".format(initial_t) + "\t"
                         +  "{}".format(initial_t) + "\t"
                         +  "{}".format(initial_t) + "\n" )
                        fp.flush()
                        LED.value = not LED.value
                        print(time_stamp)
                    button_d12.update()
                    if button_d12.fell:
                        is_logging = False
                        print("Stopped Logging")
                    
        except OSError as e:  # Typically when the filesystem isn't writeable...
            delay = 0.5  # ...blink the LED every half second.
            if e.args[0] == 28:  # If the file system is full...
                delay = 0.25  # ...blink the LED faster!
            while True:
                if is_logging:
                    LED.value = not LED.value
                    time.sleep(delay)
        LED.value = True
        time.sleep(0.5)
    else:
        LED.value = False




