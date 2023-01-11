"""Configuration file for the device.
"""

import adafruit_logging as logging

GLOBAL_FAILSAFE_TIMEOUT = 600
'''If this amount of seconds passes program should abort and base should send whatever it has'''
TIME_BETWEEN_WAKEUP = 180
'''Amount of seconds RTC should wait before setting off the alarm again (waking up the system in the process)'''
DEVICE_ID = 0
'''ID of this device (Device will become a base station if this is 0)'''
ROVER_COUNT = 1
'''Number of rovers total (not including base stations)'''

DEBUG =  {
    "FAKE_DATA": False, #Ignores actual GPS data and just uses fake static data instead
    "WATCHDOG_DISABLE": False #Disables watchdog resets so you can debug things
}
'''Debugging configuration. See actual module file for details'''

#Set log levels of individual loggers here
logging.getLogger("BASE").setLevel(logging.INFO)
logging.getLogger("DEVICE").setLevel(logging.INFO)
logging.getLogger("ROVER").setLevel(logging.INFO)
logging.getLogger("ASYNC_UART").setLevel(logging.INFO)
logging.getLogger("RADIO").setLevel(logging.INFO)
logging.getLogger("MAIN_FILE").setLevel(logging.INFO)
logging.getLogger("GPS").setLevel(logging.INFO)


SECRETS = { #I would put this on its own file untracked by git if you ever put any actual sensitive info here
    "apn": "TM",
    "apn_username": "",
    "apn_password": "",
}