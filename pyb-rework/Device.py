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
import adafruit_logging as logging

logger = logging.getLogger("DEVICE")

# Gloabls
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
    logger.info("Device shutting down!")
    RTC.alarm2_status = False
    RTC.alarm1_status = False


# Reset clock and handle watchdog wakeup state
RTC.alarm1_interrupt = True
if RTC.alarm1_status:
    dt_after_alarm = False
    alarm_time: time.struct_time = RTC.alarm1[0]
    alarm_time_tuple = list(alarm_time)
    if RTC.alarm1[1] == "monthly":
        alarm_time_tuple[0] = RTC.datetime.tm_year
        alarm_time_tuple[1] = RTC.datetime.tm_month
    elif RTC.alarm1[1] == "daily":
        alarm_time_tuple[0] = RTC.datetime.tm_year
        alarm_time_tuple[1] = RTC.datetime.tm_month
        alarm_time_tuple[2] = RTC.datetime.tm_mday
    elif RTC.alarm1[1] == "hourly":
        alarm_time_tuple[0] = RTC.datetime.tm_year
        alarm_time_tuple[1] = RTC.datetime.tm_mon
        alarm_time_tuple[2] = RTC.datetime.tm_mday
        alarm_time_tuple[3] = RTC.datetime.tm_hour
    elif RTC.alarm1[1] == "minutely":
        alarm_time_tuple[0] = RTC.datetime.tm_year
        alarm_time_tuple[1] = RTC.datetime.tm_mon
        alarm_time_tuple[2] = RTC.datetime.tm_mday
        alarm_time_tuple[3] = RTC.datetime.tm_hour
        alarm_time_tuple[4] = RTC.datetime.tm_min

    alarm_time = time.struct_time(alarm_time_tuple)

    if time.mktime(alarm_time) > time.mktime(RTC.datetime):
        #WATCHDOG_HAS_RESET
        shutdown()

    RTC.alarm1 = (time.localtime(time.mktime(RTC.alarm1[0])+300), "hourly")

'''GPS parser'''
GPS: glactracker_gps.GPS = glactracker_gps.GPS(GPS_UART, debug=DEBUG["LOGGING"]["GPS"])


def update_GPS() -> bool:
    """Validates NMEA and checks for quality 4.
     To access the data call `GPS.<ATTRIBUTE>`

    :return: Returns whether an accurate update has occurred
    :rtype: bool
    """
    # May need timeout

    logger.info("Updating GPS!")
    logger.debug("GPS_BUFFER_SIZE_BEFORE_UPDATE:", GPS_UART.in_waiting)
    GPS.update() #Potentially garbage line so we continue anyway even if it doesn't actually work

    while GPS.update():
        pass #Performs as many GPS updates as there are NMEA strings available in UART
    if (DEBUG["FAKE_DATA"]):
        #Fake data
        logger.warning("Fake data mode is on! No real GPS data will be used on this device!!!!")
        GPS.latitude = DecimalNumber("59.3")
        GPS.longitude = DecimalNumber("-1.2")
        GPS.altitude_m = 5002.3
        GPS.timestamp_utc = time.localtime(time.time())
        GPS.fix_quality = 4
        GPS.hdop = "0.01"
        GPS.satellites = "9"
    
    debug_data = {
        "LAT": GPS.latitude,
        "LONG": GPS.longitude,
        "ALTITUDE": GPS.altitude_m,
        "TIMESTAMP": GPS.timestamp_utc,
        "QUALITY": GPS.fix_quality,
        "HDOP_STR": GPS.horizontal_dilution,
        "SATELLITES_STR": GPS.satellites,
        "REMAINING_BUFFER_SIZE": GPS_UART.in_waiting
    }
    logger.debug(debug_data)


    # If NMEA received back
    if GPS.fix_quality == 4 or GPS.fix_quality == 5:
        logger.info("GPS has a high quality fix!")
        return True
    else:
        logger.info("GPS quality is currently insufficient")
    return False

#ACTUAL MAIN CODE THAT RUNS ON IMPORT
# Initialise the device
#except we did that up top so :shrug: