# Import packages
import adafruit_gps
import board
import busio
import digitalio
import adafruit_ds3231
import time
import Radio
from pyrtcm import RTCMReader


# Initialise constants
RETRY_LIMIT = 3

def ChecksumError(Error):
    pass

def TimeoutError(Error):
    pass

class Device:
    '''Generic object for devices intended to be inherited.
    Contains all require methods and variables for a generic device to be setup.
    
    Use init_hardware to setup IO
    Use radio_send(self,data) to send data
    Use gps_receive to get GPS readout
    Use radio_receive to receive data'''

    def __init__(self, device_ID):

        # Initialise variables
        self.device_ID = device_ID # DEVICE ID, -1 = Base, 0,1,2 = Rover
        '''Denotes device ID, -1 = Base, 0,1,2 = Rover '''
        self.GPS_UART1 = busio.UART
        '''GPS UART1 for NMEA communications'''
        self.GPS_UART2 = busio.UART
        '''GPS UART2 for rtcm3 communication (unidirectional towards GPS)'''
        self.RADIO_UART = busio.UART
        self.RTC = adafruit_ds3231.DS3231
        self.GPS = adafruit_gps.GPS


        # Initialise the device
        self.init_hardware()
        self.init_RTC()
        self.init_GPS()

    def init_hardware(self):
        '''
        Initialises all hardware I/O. Not the devices themselves.
        '''
        #TODO: turn into sigleton
        # Initialise hardware UARTS, specifying Tx, Rx, and baudrate
        self.gsm_UART = busio.UART(board.D0, board.D1, baudrate=9600)
        self.gps_uart_nmea = busio.UART(board.D2, board.D3, baudrate=9600)
        self.gps_uart_rtcm3 = busio.UART(board.D4, board.D5, baudrate=9600)
        self.RADIO_UART = busio.UART(board.D6, board.D7, baudrate=9600, timeout=1)

        # Initialise I2C
        self.I2C = board.I2C()

    def init_RTC(self):
        '''
        Initialise RTC using adafruit RTC library
        '''
        # Initialise RTC object
        self.RTC = adafruit_ds3231.DS3231(self.I2C)
        # Set alarm for 3 hours after the previous alarm: converts time struct to time, adds 3 hrs, converts back
        self.RTC.alarm1 = (time.localtime(time.mktime(self.RTC.alarm1)+10800))

    def radio_broadcast(self,data,data_type):
        # Send data over radio
        self.RADIO_UART.write(Radio.create_msg(data,data_type,ID=self.ID))

    def unicast_data(self,data,data_type):
        pass

    def radio_receive(self):
        ''' Gets data from the radio, and validates the checksum. If checksum is invalid, raise `ChecksumError` \n
        Returns `data_type, data, sender_ID '''
        # Read UART buffer until EOL
        packet = self.RADIO_UART.readline()

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

    def shutdown(self):
        # SHUTDOWN SCRIPT USING RTC I2C STUFF
        pass

    def latch_on(self):
        pass



