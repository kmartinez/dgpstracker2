"""This module is executed by circuitpython upon startup.
It first checks if the module was reset abnormally, and then if so shuts down gracefully.
Otherwise, the module determines if it is configured as a base or a rover, where it will then execute the respective module
"""

from config import *
import os
import Drivers.PSU as PSU
from Drivers.RTC import RTC_DEVICE
import traceback
from microcontroller import watchdog
from watchdog import WatchDogMode
import adafruit_logging as logging
from time import localtime, mktime
import rtc

logger = logging.getLogger("MAIN_FILE")
rtc.set_time_source(RTC_DEVICE)

if __name__ == "__main__":
   if RTC_DEVICE.alarm1_status:
      if RTC_DEVICE.alarm_is_in_future():
         logger.critical("Abnormal reset detected!!! Shutting device down")
         PSU.shutdown()
      else:
         RTC_DEVICE.alarm1 = (localtime(mktime(RTC_DEVICE.alarm1[0])+300), "monthly")
   RTC_DEVICE.alarm1_interrupt = True

   if not DEBUG["WATCHDOG_DISABLE"]:
      watchdog.timeout = 16
      watchdog.mode = WatchDogMode.RESET
      watchdog.feed()
   try:
      if "data_entries" not in os.listdir("/"):
         os.mkdir("/data_entries")
      if "sent_data" not in os.listdir("/"):
         os.mkdir("/sent_data")
      #input()
      if DEVICE_ID == 0:
         logger.info("Device is a base station!")
         exec(open('./Base.py').read())
      else:
         logger.info("Device is a rover!")
         exec(open('./Rover.py').read())
   except BaseException as error:
      logger.critical(traceback.format_exception(type(error), error, error.__traceback__, None, False))
   finally:
      PSU.shutdown()