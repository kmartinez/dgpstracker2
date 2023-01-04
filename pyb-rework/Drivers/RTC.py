"""Contains code to extend the RTC module functionality
"""

import board
import busio
import adafruit_ds3231
from time import struct_time, mktime

class RTC(adafruit_ds3231.DS3231):
    def alarm_is_in_future(self) -> bool:
        alarm_time: struct_time = self.alarm1[0]
        alarm_time_tuple = list(alarm_time)
        if self.alarm1[1] == "monthly":
            alarm_time_tuple[0] = self.datetime.tm_year
            alarm_time_tuple[1] = self.datetime.tm_mon
        elif self.alarm1[1] == "daily":
            alarm_time_tuple[0] = self.datetime.tm_year
            alarm_time_tuple[1] = self.datetime.tm_mon
            alarm_time_tuple[2] = self.datetime.tm_mday
        elif self.alarm1[1] == "hourly":
            alarm_time_tuple[0] = self.datetime.tm_year
            alarm_time_tuple[1] = self.datetime.tm_mon
            alarm_time_tuple[2] = self.datetime.tm_mday
            alarm_time_tuple[3] = self.datetime.tm_hour
        elif self.alarm1[1] == "minutely":
            alarm_time_tuple[0] = self.datetime.tm_year
            alarm_time_tuple[1] = self.datetime.tm_mon
            alarm_time_tuple[2] = self.datetime.tm_mday
            alarm_time_tuple[3] = self.datetime.tm_hour
            alarm_time_tuple[4] = self.datetime.tm_min

        alarm_time = struct_time(alarm_time_tuple)
        return mktime(alarm_time) > mktime(self.datetime)

I2C: busio.I2C = board.I2C()
'''I2C bus (for RTC module)'''

RTC_DEVICE: RTC = RTC(I2C)
'''RTC timer'''