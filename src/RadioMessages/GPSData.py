"""Helper module for dealing with GPS coordinate information
"""

import json
from adafruit_datetime import datetime
from mpy_decimal import DecimalNumber
from config import *
import adafruit_logging as logging

logger = logging.getLogger("GPS")

class GPSData:
    """Class representing all the data that the GPS can return
    (in regards to coordinate information)
    """
    timestamp: datetime
    latitude: str
    longitude: str
    altitude: float
    quality: int
    hdop: float
    sats: int

    def __init__(
        self,
        timestamp: datetime,
        latitude: DecimalNumber,
        longitude: DecimalNumber,
        altitude: float,
        quality: int,
        hdop: float,
        sats: int
        ):
        self.timestamp = timestamp
        self.latitude = str(latitude)
        self.longitude = str(longitude)
        self.altitude = altitude
        self.quality = quality
        self.hdop = hdop
        self.sats = sats

    def to_json(self) -> str:
        """Serializes self to json and then to bytes ready to send over radio

        :return: self as JSON string
        :rtype: str
        """
        data = {
            "timestamp": self.timestamp.isoformat(),
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude": self.altitude,
            "quality": self.quality,
            "hdop": self.hdop,
            "sats": self.sats
        }
        output = json.dumps(data)

        logger.debug(f"SERIALIZE_GPSDATA_JSON_DUMP_DICTIONARY: {data}")
        return output

    def from_json(json_str: str) -> dict:
        """Deserializes a byte array to a dict, *NOT A GPSDATA OBJECT*

        :param byte_arr: Bytes to deserialize
        :type byte_arr: bytes
        :return: Dict representing a GPSData object (ready to send over json)
        :rtype: dict
        """
        logger.debug(f"INPUT_STRING: {json_str}")

        output = json.loads(json_str)

        logger.debug(f"DESERIALIZE_GPSDATA_DICT_OUTPUT: {output}")
        return output
