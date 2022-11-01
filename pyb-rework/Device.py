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
import asyncio

from Radio import *
from pyrtcm import RTCMReader
import pynmeagps
import io


# Initialise constants
RETRY_LIMIT = 3

#Properties
device_ID: int = None
'''Unique ID for the device. -1 = Base; 0,1,2 = Rover'''

GPS_UART_NMEA: busio.UART = busio.UART(board.D0, board.D1, baudrate=9600)
'''GPS UART1 for NMEA communications'''

GPS_UART_RTCM3: busio.UART = busio.UART(board.D4, board.D5, baudrate=9600)
'''GPS UART2 for rtcm3 communication (unidirectional towards GPS)'''

RADIO_UART: busio.UART = busio.UART(board.D24, board.D23, baudrate=9600, timeout=0.01)
'''UART bus for radio module'''

I2C: busio.I2C = board.I2C()
'''I2C bus (for RTC module)'''

RTC: adafruit_ds3231.DS3231 = adafruit_ds3231.DS3231(I2C)
'''RTC timer'''
#Immediately set alarm for 3 hrs away
RTC.alarm1 = (time.localtime(time.mktime(RTC.alarm1)+10800))

GPS: adafruit_gps.GPS = None

async def readline_uart_async(uart: busio.UART):
    '''Magic readline wrapper that makes it async. Not thread-safe for the *same* uart'''
    timeout = uart.timeout
    uart.timeout = 0.01
    data = None
    while data is None:
        data = uart.readline()
        if data is None:
            await asyncio.sleep(0)
    uart.timeout = timeout
    return data

def radio_broadcast(type: PacketType, payload: bytes):
    '''Send payload over radio'''
    RADIO_UART.write(RadioPacket(type, payload, device_ID))

def send_ack(recipient: int):
    '''Send ACK intended for given device ID'''
    radio_broadcast(PacketType.ACK, struct.pack('h', recipient))

def radio_receive():
    ''' Gets data from the radio `` \n
    Returns `RadioPacket` or `None`'''    
    # Read UART buffer until EOL
    raw = RADIO_UART.readline()
    if raw == None: raise TimeoutError

    try:
        return RadioPacket.deserialize(raw)
    except ChecksumError:
        return None

async def async_radio_receive():
    raw = await readline_uart_async(RADIO_UART)
    try:
        return RadioPacket.deserialize(raw)
    except ChecksumError:
        pass

def shutdown():
    # SHUTDOWN SCRIPT USING RTC I2C STUFF
    RTC.alarm2_status = False
    RTC.alarm1_status = False

def latch_on():
    pass

#ACTUAL MAIN CODE THAT RUNS ON IMPORT
# Initialise the device
#except we did that up top so :shrug:
