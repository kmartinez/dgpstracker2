from config import *
from debug import *

if __name__ == "__main__":
   #input()
   if DEVICE_ID == 0:
      debug("I'm a base station!")
      exec(open('./Base.py').read())
   else:
      debug("I'm a rover!")
      exec(open('./Rover.py').read())