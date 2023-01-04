"""Contains all code relating to PSU controls (enabling devices, etc.)
"""

# Import packages
from config import *
from mpy_decimal import *
import adafruit_logging as logging
from Drivers.RTC import RTC_DEVICE
from digitalio import DigitalInOut
import board

logger = logging.getLogger("DEVICE")

# Gloabls
GSM_ENABLE_PIN: DigitalInOut = DigitalInOut(board.A0)
GSM_ENABLE_PIN.switch_to_output()
GSM_ENABLE_PIN = False

def enable_fona():
    """Turns on the power for the connected adafruit FONA module
    """
    GSM_ENABLE_PIN.value = True

def shutdown():
    """Resets timer, causing shutdown of device
    """
    logger.info("Device shutting down!")
    RTC_DEVICE.alarm2_status = False
    RTC_DEVICE.alarm1_status = False

#ACTUAL MAIN CODE THAT RUNS ON IMPORT
# Initialise the device
#except we did that up top so :shrug: