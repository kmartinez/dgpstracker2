import json
from adafruit_datetime import datetime
from mpy_decimal import DecimalNumber
from config import *

def extended_debug(
    *values: object,
) -> None:
    
    if DEBUG["EXTENDED_LOGGING"]["GPS_DATA"]:
        print(*values)

class GPSData:
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

    def serialize(self) -> bytes:
        """Serializes self to json and then to bytes ready to send over radio

        :return: self as bytes
        :rtype: bytes
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
        output = json.dumps(data).encode('utf-8')

        extended_debug("SERIALIZE_GPSDATA_JSON_DUMP_DICTIONARY:", json.dumps(data))
        extended_debug("SERIALIZE_GPSDATA_BYTES_OUTPUT:", output)
        return output

    def deserialize(byte_arr: bytes) -> list(dict):
        """Deserializes a byte array to a list of dicts, *NOT A GPSDATA OBJECT*

        :param byte_arr: Bytes to deserialize
        :type byte_arr: bytes
        :return: Dict representing a GPSData object (ready to send over json)
        :rtype: dict
        """
        output = []
        data = bytes.decode(byte_arr, 'utf-8').split('|||')
        for d in data:
            output.append(json.loads(d))

        extended_debug("DESERIALIZE_GPSDATA_BYTES:", byte_arr)
        extended_debug("DESERIALIZE_GPSDATA_DICT_OUTPUT:", output)
        return output
