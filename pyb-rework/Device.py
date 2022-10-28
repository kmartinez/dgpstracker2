'''Generic object for devices intended to be inherited.
Contains all require methods and variables for a generic device to be setup.

Use init_hardware to setup IO
Use radio_send(data) to send data
Use gps_receive to get GPS readout
Use radio_receive to receive data'''

# Import packages
from cgi import test
import adafruit_gps
import board
import busio
import digitalio
import adafruit_ds3231
import time

import Radio
from pyrtcm import RTCMReader
import pynmeagps
import io


# Initialise constants
RETRY_LIMIT = 3

class ChecksumError(Exception):
    pass

class TimeoutError(Exception):
    pass

#Properties
device_ID: int = None
'''Unique ID for the device. -1 = Base; 0,1,2 = Rover'''

GSM_UART: busio.UART = None

GPS_UART_NMEA: busio.UART = None
'''GPS UART1 for NMEA communications'''

GPS_UART_RTCM3: busio.UART = None
'''GPS UART2 for rtcm3 communication (unidirectional towards GPS)'''

RADIO_UART: busio.UART = None
'''UART for radio module'''

RTC: adafruit_ds3231.DS3231 = None

GPS: adafruit_gps.GPS = None

I2C: busio.I2C = None

#Method definitions
def init_hardware():
    '''
    Initialises all hardware I/O. Not the devices themselves.
    '''
    # Initialise hardware UARTS, specifying Tx, Rx, and baudrate
    gsm_UART = busio.UART(board.D0, board.D1, baudrate=9600)
    GPS_UART_NMEA = busio.UART(board.D2, board.D3, baudrate=9600)
    GPS_UART_RTCM3 = busio.UART(board.D4, board.D5, baudrate=9600)
    RADIO_UART = busio.UART(board.D6, board.D7, baudrate=9600, timeout=1)

    # Initialise I2C
    I2C = board.I2C()

    test = 1

def init_RTC():
    '''
    Initialise RTC using adafruit RTC library
    '''
    # Initialise RTC object
    RTC = adafruit_ds3231.DS3231(I2C)
    # Set alarm for 3 hours after the previous alarm: converts time struct to time, adds 3 hrs, converts back
    RTC.alarm1 = (time.localtime(time.mktime(RTC.alarm1)+10800))

def radio_broadcast(data,data_type):
    # Send data over radio
    RADIO_UART.write(Radio.create_msg(data,data_type,ID=device_ID))

def unicast_data(data,data_type):
    pass

def radio_receive():
    ''' Gets data from the radio, and validates the checksum. If checksum is invalid, raise `ChecksumError` \n
    Returns `data_type, data, sender_ID '''
    # Read UART buffer until EOL
    packet = RADIO_UART.readline()

    # If data was found
    if packet != None:
        # Validate checksum
        if sum(packet[:-2]) == int.from_bytes(packet[-2:]):
            # Parse packet
            packet = packet[:-2]
            data_type = packet[0]
            data = packet[1:-1]
            sender_ID = packet[-1]
            return data_type, data, sender_ID
        else:
            raise ChecksumError("Checksum invalid")
    raise TimeoutError("Timeout")

def shutdown():
    # SHUTDOWN SCRIPT USING RTC I2C STUFF
    RTC.alarm2_status = False
    RTC.alarm1_status = False
    pass

def latch_on():
    pass

#ACTUAL MAIN CODE THAT RUNS ON IMPORT
# Initialise the device
init_hardware()
init_RTC()
init_GPS()

