GLOBAL_FAILSAFE_TIMEOUT = 600
'''If this amount of seconds passes program should abort and base should send whatever it has'''
TIME_BETWEEN_WAKEUP = 180
'''Amount of seconds RTC should wait before setting off the alarm again (waking up the system in the process)'''
DEVICE_ID = 1
'''ID of this device (Will become base station if is 0)'''

DEBUG =  {
    "LOGGING": True, #Turns on debug print() statements
    "FAKE_DATA": False #Ignores actual GPS data and just uses fake static data instead
}

SECRETS = {
    "apn": "TM",
    "apn_username": "",
    "apn_password": "",
}