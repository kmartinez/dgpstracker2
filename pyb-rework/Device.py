'''Generic object for devices intended to be inherited.
Contains all require methods and variables for a generic device to be setup.

Use init_hardware to setup IO
Use radio_send(data) to send data
Use gps_receive to get GPS readout
Use radio_receive to receive data'''

# Import packages
import glactracker_gps
import board
import busio
import adafruit_ds3231
import time
import asyncio
import io
import Drivers.AsyncUART as AsyncUART
import Drivers.Radio as radio
from Drivers.Radio import PacketType
from config import *
from mpy_decimal import *

GPS_UART: busio.UART = busio.UART(board.A1, board.A2, baudrate=115200, receiver_buffer_size=2048)
'''GPS NMEA UART for communications'''

RTCM3_UART: AsyncUART.AsyncUART = AsyncUART.AsyncUART(board.D1, board.D0, baudrate=115200, receiver_buffer_size=2048)
'''GPS RTCM3 UART'''

# GPS configured to operate on a single UART, so not longer necessary
# GPS_UART_RTCM3: busio.UART = busio.UART(board.D4, board.D5, baudrate=115200)
# '''GPS UART2 for rtcm3 communication (unidirectional towards GPS)'''

I2C: busio.I2C = board.I2C()
'''I2C bus (for RTC module)'''

RTC: adafruit_ds3231.DS3231 = adafruit_ds3231.DS3231(I2C)
'''RTC timer'''
#Set alarm for 3 hrs from previous alarm

def shutdown():
    """Resets timer, causing shutdown of device
    """
    # SHUTDOWN SCRIPT USING RTC I2C STUFF
    debug("SHUTDOWN_INITIATED")
    RTC.alarm2_status = False
    RTC.alarm1_status = False

RTC.alarm1_interrupt = True
if RTC.alarm1_status:
    dt_after_alarm = False
    alarm_time = RTC.alarm1[0]
    alarm_time.year = RTC.datetime.year
    alarm_time.month = RTC.datetime.month
    if time.mktime(alarm_time) > time.mktime(RTC.datetime):
        #WATCHDOG_HAS_RESET
        shutdown()

    RTC.alarm1 = (time.localtime(time.mktime(RTC.datetime)+300), "hourly")

'''GPS parser'''
GPS: glactracker_gps.GPS = glactracker_gps.GPS(GPS_UART, debug=DEBUG["LOGGING"]["GPS"])

def debug(
    *values: object,
) -> None:
    
    if DEBUG["LOGGING"]["DEVICE"]:
        print(*values)

def extended_debug(
    *values: object,
) -> None:
    
    if DEBUG["EXTENDED_LOGGING"]["GPS"]:
        print(*values)

def update_GPS():
    """Validates NMEA and checks for quality 4.
     To access the data call `GPS.<ATTRIBUTE>`

    :return: Retutrns raw data or `None`
    :rtype: `GPS.nmea_sentence`
    """
    # May need timeout

    debug("GPS_UPDATE_STARTED")
    extended_debug("GPS_BUFFER_SIZE_BEFORE_UPDATE:", GPS_UART.in_waiting)
    GPS.update() #Potentially garbage line so we continue anyway even if it doesn't actually work

    while GPS.update():
        pass #Performs as many GPS updates as there are NMEA strings available in UART
    if (DEBUG["FAKE_DATA"]):
        #Fake data
        print("WARNING_FAKE_DATA_MODE_ON")
        GPS.latitude = DecimalNumber("59.3")
        GPS.longitude = DecimalNumber("-1.2")
        GPS.altitude_m = 5002.3
        GPS.timestamp_utc = time.localtime(time.time())
        GPS.fix_quality = 4
        GPS.hdop = "0.01"
        GPS.satellites = "9"
    
    extended_debug("LAT:", GPS.latitude)
    extended_debug("LONG:", GPS.longitude)
    extended_debug("ALTITUDE:", GPS.altitude_m)
    extended_debug("TIMESTAMP:", GPS.timestamp_utc)
    extended_debug("QUALITY:", GPS.fix_quality)
    extended_debug("HDOP_STR:",GPS.horizontal_dilution)
    extended_debug("SATELLITES_STR:", GPS.satellites)
    extended_debug("REMAINING_BUFFER_SIZE:", GPS_UART.in_waiting)


    # If NMEA received back
    if GPS.fix_quality == 4 or GPS.fix_quality == 5:
        debug("NMEA_QUALITY_SUCCESS")
        return GPS.nmea_sentence
    else:
        debug("NMEA_QUALITY_FAIL")
    return None

#ACTUAL MAIN CODE THAT RUNS ON IMPORT
# Initialise the device
#except we did that up top so :shrug: