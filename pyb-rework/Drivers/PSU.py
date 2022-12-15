'''Generic object for devices intended to be inherited.
Contains all require methods and variables for a generic device to be setup.

Use init_hardware to setup IO
Use radio_send(data) to send data
Use gps_receive to get GPS readout
Use radio_receive to receive data'''

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
GSM_ENABLE_PIN.switch_to_output(value=False)

def enable_fona():
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