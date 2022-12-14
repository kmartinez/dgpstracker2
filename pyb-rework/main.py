from config import *
import os

def debug(
    *values: object,
) -> None:
   if DEBUG["LOGGING"]["MAIN_FILE"]:
      print(*values)

if __name__ == "__main__":
   if "data_entries" not in os.listdir("/"):
      os.mkdir("/data_entries")
   #input()
   if DEVICE_ID == 0:
      debug("BASE_STATION_MODE")
      exec(open('./Base.py').read())
   else:
      debug("ROVER_MODE")
      exec(open('./Rover.py').read())