"""Main code for all rover devices
(Executed directly by main.py)
"""

import Drivers.PSU as PSU
import Drivers.Radio as radio
from Drivers.Radio import PacketType
import struct
from config import *
from Statistics.StatsBuffer import StatsBuffer
import ulab.numpy as np
from Statistics import Util as util
from mpy_decimal import *
from RadioMessages.GPSData import *
from Drivers.Radio import FormatStrings
import os
from microcontroller import watchdog
import adafruit_logging as logging
import time
import asyncio

from Drivers.DGPS import GPS_DEVICE
from Drivers.RTC import RTC_DEVICE

logger = logging.getLogger("ROVER")

DecimalNumber.set_scale(32)
SD_MAX = DecimalNumber("0.0001")
'''Maximum acceptible standard deviation [degrees lat/long]'''
VAR_MAX = SD_MAX ** 2
AVERAGING_SAMPLE_SIZE = 5
'''number of samples to take a rolling standard deviation and average of'''

GPS_SAMPLES: dict[str, StatsBuffer] = {
    "lats": StatsBuffer(AVERAGING_SAMPLE_SIZE),
    "longs": StatsBuffer(AVERAGING_SAMPLE_SIZE)
}

accurate_reading_saved: bool = False
sent_data_start_pos: int = 999999999

async def feed_watchdog():
    """Upon being executed by a scheduler, this task will feed the watchdog then yield.
    Added as a task to the asyncio scheduler by this module's main code.
    """
    while True:
        if not DEBUG["WATCHDOG_DISABLE"]:
            watchdog.feed()
        await asyncio.sleep(0)

async def rover_loop():
    """Main functionality of the rover resides here.
    Waits for radio message and checks its type.
    If it's RTCM3, send back NMEA data.
    If it's an ACK for us, shutdown the system because the base has our stuff.
    Added as a task to the asyncio scheduler upon startup
    """
    # Rover needs to:
    # Receive packet
    # If RTCM3 received, get NMEA and send it
    # If ACK received, shutdown
    global accurate_reading_saved
    global sent_data_start_pos
    while True:
        try:
            logger.info("Waiting for a radio packet")
            packet = await radio.receive_packet()
        except radio.ChecksumError:
            continue
        
        # If incoming message is tagged as RTCM3
        if packet.type == PacketType.RTCM3 and not accurate_reading_saved:
            logger.info("RTCM3 data received and we have not finished obtaining a reading")
            GPS_DEVICE.rtk_calibrate(packet.payload)
            if GPS_DEVICE.update_with_all_available():
                GPS_SAMPLES["lats"].append(GPS_DEVICE.latitude)
                GPS_SAMPLES["longs"].append(GPS_DEVICE.longitude)

                #no do standard dev on 1 sample pls
                if (len(GPS_SAMPLES["longs"].circularBuffer) < AVERAGING_SAMPLE_SIZE): continue
                
                debug_variance = util.var(GPS_SAMPLES["longs"].circularBuffer)
                logger.debug(f"VARIANCE_LONG: {debug_variance}")

                if util.var(GPS_SAMPLES["longs"].circularBuffer) < VAR_MAX and util.var(GPS_SAMPLES["lats"].circularBuffer) < VAR_MAX:
                    logger.info("Accurate reading obtained! Writing data to file")
                    RTC_DEVICE.datetime = GPS_DEVICE.timestamp_utc
                    gps_data = GPSData(
                        datetime.fromtimestamp(time.mktime(GPS_DEVICE.timestamp_utc)),
                        util.mean(GPS_SAMPLES["lats"].circularBuffer),
                        util.mean(GPS_SAMPLES["longs"].circularBuffer),
                        GPS_DEVICE.altitude_m,
                        GPS_DEVICE.fix_quality,
                        float(GPS_DEVICE.horizontal_dilution),
                        int(GPS_DEVICE.satellites)
                        )
                    with open("/data_entries/" + gps_data.timestamp.isoformat().replace(":", "_"), "w") as file:
                        file.write(gps_data.to_json() + "\n")
                    logger.info("File write complete!")
                    accurate_reading_saved = True
                    
        elif packet.type == PacketType.RTCM3:
            #RTCM3 received and we have collected our data for this session
            #Send the oldest data point we have
            #If there aren't any, delete
            logger.info("Radio packet received and accurate reading is obtained!")
            remaining_paths = os.listdir("/data_entries/")
            if (len(remaining_paths) > 0):
                logger.info("Sending reading to base")
                with open("/data_entries/" + remaining_paths[0], "r") as file:
                    data_to_send = file.readline()
                    radio.broadcast_data(PacketType.NMEA, data_to_send.encode('utf-8'))
            else:
                logger.info("Telling base that we're finished!")
                radio.broadcast_data(PacketType.FIN, struct.pack(FormatStrings.PACKET_DEVICE_ID, packet.sender))

        elif packet.type == PacketType.ACK and struct.unpack(radio.FormatStrings.PACKET_DEVICE_ID, packet.payload)[0] == DEVICE_ID:
            #ACK received, which means the base received a data message
            #We can now safely delete said message from the blob
            logger.info("ACK received from base, deleting sent data")
            if len(os.listdir("/data_entries/")) > 0:
                os.remove("/data_entries/" + os.listdir("/data_entries/")[0])
            
        elif packet.type == PacketType.FIN and struct.unpack(FormatStrings.PACKET_DEVICE_ID, packet.payload)[0] == DEVICE_ID:
            logger.info("Base has given OK to shutdown!")
            break

if __name__ == "__main__":
    asyncio.run(asyncio.wait_for_ms(asyncio.gather(rover_loop(), feed_watchdog()), GLOBAL_FAILSAFE_TIMEOUT * 1000))
    PSU.shutdown()