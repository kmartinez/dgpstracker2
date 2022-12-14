GLOBAL_FAILSAFE_TIMEOUT = 600
'''If this amount of seconds passes program should abort and base should send whatever it has'''
TIME_BETWEEN_WAKEUP = 180
'''Amount of seconds RTC should wait before setting off the alarm again (waking up the system in the process)'''
DEVICE_ID = 0
'''ID of this device (Will become base station if is 0)'''
ROVER_COUNT = 3

DEBUG =  {
    "LOGGING": {
        "BASE": True,
        "DEVICE": True,
        "ROVER": True,
        "ASYNC_UART": True,
        "RADIO": True,
        "MAIN_FILE": True,
        "GPS": True
    }, #Turns on debug print() statements
    "EXTENDED_LOGGING": {
        "GPS": True,
        "ASYNC_UART": False,
        "RADIO": False,
        "GPS_DATA": False
    },
    "FAKE_DATA": False #Ignores actual GPS data and just uses fake static data instead
}

SECRETS = { #I would put this on its own file untracked by git if you ever put any actual sensitive info here
    "apn": "TM",
    "apn_username": "",
    "apn_password": "",
}