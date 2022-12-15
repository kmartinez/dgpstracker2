from config import *
import os
import Device
import traceback
from microcontroller import watchdog
from watchdog import WatchDogMode

def debug(
    *values: object,
) -> None:
   if DEBUG["LOGGING"]["MAIN_FILE"]:
      print(*values)

if __name__ == "__main__":
   watchdog.timeout = 16
   watchdog.mode = WatchDogMode.RESET
   watchdog.feed()
   try:
      if "data_entries" not in os.listdir("/"):
         os.mkdir("/data_entries")
      #input()
      if DEVICE_ID == 0:
         debug("BASE_STATION_MODE")
         exec(open('./Base.py').read())
      else:
         debug("ROVER_MODE")
         exec(open('./Rover.py').read())
   except BaseException as error:
      with open("error_log.txt", 'a') as file:
         traceback.print_exception(type(error), error, error.__traceback__, None, file, False)
      traceback.print_exception(type(error), error, error.__traceback__, None, None, False)
   finally:
      Device.shutdown()