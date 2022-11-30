import json
from datetime import datetime
from mpy_decimal import DecimalNumber

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

    def serialize(self):
        return bytes(json.dumps(self))

    def deserialize(byte_arr: bytes):
        return json.loads(str(byte_arr))
