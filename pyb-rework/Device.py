'''Generic object for devices intended to be inherited.
Contains all require methods and variables for a generic device to be setup.

Use init_hardware to setup IO
Use radio_send(data) to send data
Use gps_receive to get GPS readout
Use radio_receive to receive data'''

# Import packages
import adafruit_gps
import board
import busio
import adafruit_ds3231
import time
import asyncio
import io
import Drivers.AsyncUART as AsyncUART
import Drivers.Radio as radio
from Drivers.Radio import PacketType
from debug import *
from config import *

GPS_UART: AsyncUART.AsyncUART = AsyncUART.AsyncUART(board.A1, board.A2, baudrate=115200)
'''GPS NMEA UART for communications'''

RTCM3_UART: AsyncUART.AsyncUART = AsyncUART.AsyncUART(board.TX, board.RX, baudrate=115200)
'''GPS RTCM3 UART'''

# GPS configured to operate on a single UART, so not longer necessary
# GPS_UART_RTCM3: busio.UART = busio.UART(board.D4, board.D5, baudrate=115200)
# '''GPS UART2 for rtcm3 communication (unidirectional towards GPS)'''

I2C: busio.I2C = board.I2C()
'''I2C bus (for RTC module)'''

RTC: adafruit_ds3231.DS3231 = adafruit_ds3231.DS3231(I2C)
'''RTC timer'''
#Set alarm for 3 hrs from previous alarm
RTC.alarm1 = (time.localtime(time.mktime(RTC.alarm1[0])+TIME_BETWEEN_WAKEUP), "monthly")

'''GPS parser'''
gps_stream: io.BytesIO = io.BytesIO()
GPS: adafruit_gps.GPS = adafruit_gps.GPS(gps_stream)

def validate_NMEA(raw):
    '''Validates NMEA and checks for quality 4.
    Retutrns raw data. To access the data call GPS.<ATTRIBUTE>'''
    gps_stream.flush()
    gps_stream.write(raw)

    # May need timeout
    if GPS.update():
        debug("No new NMEA data")
        return None
        
    # If NMEA received back
    if GPS.fix_quality == '4':
        debug("Quality 4 NMEA data received from GPS")
        return raw
    else:
        debug("NMEA not quality 4")
    return None

def shutdown():
    # SHUTDOWN SCRIPT USING RTC I2C STUFF
    RTC.alarm2_status = False
    RTC.alarm1_status = False

def latch_on():
    pass

#ACTUAL MAIN CODE THAT RUNS ON IMPORT
# Initialise the device
#except we did that up top so :shrug: