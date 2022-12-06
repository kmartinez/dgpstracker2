import json
from adafruit_datetime import datetime
from mpy_decimal import DecimalNumber
from debug import *

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
        sats: str
        ):
        self.timestamp = timestamp
        self.latitude = str(latitude)
        self.longitude = str(longitude)
        self.altitude = altitude
        self.quality = quality
        self.hdop = hdop
        self.sats = sats

    def serialize(self):
        debug("JSON DUMP:\n",json.dumps(self))
        data = {
            "timestamp": self.timestamp.isoformat(),
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude": self.altitude,
            "quality": self.quality,
            "hdop": self.hdop,
            "sats": self.sats
        }
        debug("JSON_TIMESTAMP?:", self.timestamp.isoformat())
        debug("JSON_DUMP_2:", json.dumps(data))
        return json.dumps(data).encode('utf-8')

    def deserialize(byte_arr: bytes):
        debug(byte_arr)
        return json.loads(bytes.decode(byte_arr, 'utf-8'))
