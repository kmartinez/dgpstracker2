from Device import *
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

DecimalNumber.set_scale(32)
SD_MAX = DecimalNumber("0.0001")
VAR_MAX = SD_MAX ** 2
'''Maximum acceptible standard deviation [m]'''
AVERAGING_SAMPLE_SIZE = 5
'''number of samples to take a rolling standard deviation and average of'''

GPS_SAMPLES: dict[str, StatsBuffer] = {
    "lats": StatsBuffer(AVERAGING_SAMPLE_SIZE),
    "longs": StatsBuffer(AVERAGING_SAMPLE_SIZE)
}

def debug(
    *values: object,
) -> None:
    
    if DEBUG["LOGGING"]["ROVER"]:
        print(*values)

accurate_reading_saved: bool = False
sent_data_start_pos: int = 999999999

def update_gps_with_rtcm3(rtcm3: bytes) -> bool:
    """Sends RTCM3 data to GPS then updates GPS object with any new serial data

    :param rtcm3: RTCM3 bytes
    :type rtcm3: bytes
    :return: Last GPS Sentence or None if no update occured
    :rtype: bool
    """
    RTCM3_UART.write(rtcm3)
    return update_GPS()

async def rover_loop():
    """Main loop of each rover.
    Waits for radio message and checks its type.
    If it's RTCM3, send back NMEA data.
    If it's an ACK for us, shutdown the system because the base has our stuff
    """
    # Rover needs to:
    # Receive packet
    # If RTCM3 received, get NMEA and send it
    # If ACK received, shutdown
    global accurate_reading_saved
    global sent_data_start_pos
    while True:
        debug("WAITING_FOR_RTCM3")
        watchdog.feed()
        try:
            packet = await radio.receive_packet()
        except radio.ChecksumError:
            continue
        
        # If incoming message is tagged as RTCM3
        if packet.type == PacketType.RTCM3 and not accurate_reading_saved:
            debug("RTCM3_RECEIVED, UPDATING_GPS")
            if update_gps_with_rtcm3(packet.payload):
                GPS_SAMPLES["lats"].append(GPS.latitude)
                GPS_SAMPLES["longs"].append(GPS.longitude)

                #no do standard dev on 1 sample pls
                if (len(GPS_SAMPLES["longs"].circularBuffer) < AVERAGING_SAMPLE_SIZE): continue

                debug("VAR_LONG:", util.var(GPS_SAMPLES["longs"].circularBuffer))

                if util.var(GPS_SAMPLES["longs"].circularBuffer) < VAR_MAX and util.var(GPS_SAMPLES["lats"].circularBuffer) < VAR_MAX:
                    debug("GPS_DATA_WRITING_TO_FILE")
                    RTC.datetime = GPS.timestamp_utc
                    gps_data = GPSData(
                        datetime.fromtimestamp(time.mktime(GPS.timestamp_utc)),
                        util.mean(GPS_SAMPLES["lats"].circularBuffer),
                        util.mean(GPS_SAMPLES["longs"].circularBuffer),
                        GPS.altitude_m,
                        GPS.fix_quality,
                        float(GPS.horizontal_dilution),
                        int(GPS.satellites)
                        )
                    with open("/data_entries/" + gps_data.timestamp.isoformat().replace(":", "_"), "w") as file:
                        file.write(gps_data.to_json() + "\n")
                    accurate_reading_saved = True
                    
        elif packet.type == PacketType.RTCM3:
            #RTCM3 received and we have collected our data for this session
            #Send the oldest data point we have
            #If there aren't any, delete
            remaining_paths = os.listdir("/data_entries/")
            if (len(remaining_paths) > 0):
                with open("/data_entries/" + remaining_paths[0], "r") as file:
                    data_to_send = file.readline()
                    radio.broadcast_data(PacketType.NMEA, data_to_send.encode('utf-8'))
            else:
                radio.broadcast_data(PacketType.FIN, struct.pack(FormatStrings.PACKET_DEVICE_ID, packet.sender))

        elif packet.type == PacketType.ACK and struct.unpack(radio.FormatStrings.PACKET_DEVICE_ID, packet.payload)[0] == DEVICE_ID:
            #ACK received, which means the base received a data message
            #We can now safely delete said message from the blob
            os.remove("/data_entries/" + os.listdir("/data_entries/")[0])
            pass
            
        elif packet.type == PacketType.FIN and struct.unpack(FormatStrings.PACKET_DEVICE_ID, packet.payload)[0] == DEVICE_ID:
            debug("FINISHED_SENDING_DATA")
            break

if __name__ == "__main__":
    asyncio.run(asyncio.wait_for_ms(rover_loop(), GLOBAL_FAILSAFE_TIMEOUT * 1000))
    shutdown()