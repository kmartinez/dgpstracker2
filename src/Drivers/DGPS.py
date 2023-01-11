"""All code relating to the GPS extensions and GPS module communications
"""

import glactracker_gps
from busio import UART
import adafruit_logging as logging
from config import *
from mpy_decimal import DecimalNumber
from time import localtime,time
import board
from Drivers.AsyncUART import AsyncUART
import binascii

logger = logging.getLogger("GPS")

class DGPS(glactracker_gps.GPS):
    """Extended GPS class that allows use of Differential GPS information
    """
    def __init__(self, uart: UART, rtcm_uart: AsyncUART, debug: bool = False) -> None:
        super().__init__(uart, debug)
        self.rtcm_uart = rtcm_uart
    
    def rtk_calibrate(self, rtcm3_data: bytes):
        """Calibrates the GPS module using RTCM3 messages

        :param rtcm3_data: RTCM3 messages to be sent
        :type rtcm3_data: bytes
        """
        logger.debug(f"CALIBRATING_RTCM3_BYTES: {binascii.hexlify(rtcm3_data)}")
        self.rtcm_uart.write(rtcm3_data)

    def to_dict(self):
        """Returns a dictionary of relevant GPS attributes

        :return: GPS info dictionary (can be converted to JSON)
        :rtype: dict
        """
        return {
            "LAT": self.latitude,
            "LONG": self.longitude,
            "ALTITUDE": self.altitude_m,
            "TIMESTAMP": self.timestamp_utc,
            "QUALITY": self.fix_quality,
            "HDOP_STR": self.horizontal_dilution,
            "SATELLITES_STR": self.satellites,
            "REMAINING_BUFFER_SIZE": self.in_waiting
        }
    
    def update_with_all_available(self):
        """Updates GPS from UART until it runs out of data to update with

        :return: Update success state
        :rtype: bool
        """
        logger.info("Updating GPS!")

        device_updated: bool = self.update() #Potentially garbage line so we continue anyway even if it doesn't actually work
        while self.update():
            device_updated = True #Performs as many GPS updates as there are NMEA strings available in UART

        if (DEBUG["FAKE_DATA"]):
            #Fake data
            logger.warning("Fake data mode is on! No real GPS data will be used on this device!!!!")
            self.latitude = DecimalNumber("59.3")
            self.longitude = DecimalNumber("-1.2")
            self.altitude_m = 5002.3
            self.timestamp_utc = localtime(time())
            self.fix_quality = 4
            self.horizontal_dilution = "0.01"
            self.satellites = "9"
        
        logger.debug(f"GPS_DATA: {self.to_dict()}")

        # If NMEA received back
        if self.fix_quality == 4 or self.fix_quality == 5:
            logger.info("GPS has a high quality fix!")
            return device_updated
        else:
            logger.info("GPS quality is currently insufficient")
            return False
    
    async def get_rtcm3_message(self):
        """Gets RTCM3 correction messages from the GPS module on the provided RTCM3 UART

        :return: Bytes object of the 5 RTCM3 messages (they are different messages but we don't know why exactly)
        :rtype: bytes
        """
        # Read UART for newline terminated data - produces bytestr
        logger.info("Retrieving RTCM3 from UART")
        RTCM3_UART.reset_input_buffer()
        await RTCM3_UART.aysnc_read_RTCM3_packet_forever() #Garbled maybe
        data = bytearray()
        for i in range(5):
            d = await RTCM3_UART.aysnc_read_RTCM3_packet_forever()
            data += d
        logger.debug(f"RTCM3_BYTES: {binascii.hexlify(bytes(data))}")
        logger.info("RTCM3 obtained from UART")
        return bytes(data)

GPS_UART: UART = UART(board.A1, board.A2, baudrate=115200, receiver_buffer_size=2048)
'''GPS NMEA UART for communications'''

RTCM3_UART: AsyncUART = AsyncUART(board.D1, board.D0, baudrate=115200, receiver_buffer_size=2048)
'''GPS RTCM3 UART'''

GPS_DEVICE: DGPS = DGPS(GPS_UART, RTCM3_UART)