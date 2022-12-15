from config import *
import os
import Device
import traceback
from microcontroller import watchdog
from watchdog import WatchDogMode
import adafruit_logging as logging

logger = logging.getLogger("MAIN_FILE")

if __name__ == "__main__":
   if not DEBUG["WATCHDOG_DISABLE"]:
      watchdog.timeout = 16
      watchdog.mode = WatchDogMode.RESET
      watchdog.feed()
   try:
      if "data_entries" not in os.listdir("/"):
         os.mkdir("/data_entries")
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
      Device.shutdown()