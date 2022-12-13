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
from Drivers.FileFuncs import *

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

def update_gps_with_rtcm3(rtcm3: bytes) -> str | None:
    """Sends RTCM3 data to GPS then updates GPS object with any new serial data

    :param rtcm3: RTCM3 bytes
    :type rtcm3: bytes
    :return: Last GPS Sentence or None if no update occured
    :rtype: str | None
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
    while True:
        debug("WAITING_FOR_RTCM3")
        try:
            packet = await radio.receive_packet()
        except radio.ChecksumError:
            continue
        
        # If incoming message is tagged as RTCM3
        if packet.type == PacketType.RTCM3:
            debug("RTCM3_SUCCESS, WAITING_FOR_NMEA")
            sentence = update_gps_with_rtcm3(packet.payload)
            if sentence is not None:
                GPS_SAMPLES["lats"].append(GPS.latitude)
                GPS_SAMPLES["longs"].append(GPS.longitude)

                # Make sure standard deviation is only taken once a certain number of readings has been raken in
                if (len(GPS_SAMPLES["longs"].circularBuffer) < AVERAGING_SAMPLE_SIZE): continue

                debug("VAR_LONG:", util.var(GPS_SAMPLES["longs"].circularBuffer))

                if util.var(GPS_SAMPLES["longs"].circularBuffer) < VAR_MAX and util.var(GPS_SAMPLES["lats"].circularBuffer) < VAR_MAX:
                    debug("NMEA_SENDING")
                    payload = GPSData(
                        datetime.fromtimestamp(time.mktime(GPS.timestamp_utc)),
                        util.mean(GPS_SAMPLES["lats"].circularBuffer),
                        util.mean(GPS_SAMPLES["longs"].circularBuffer),
                        GPS.altitude_m,
                        GPS.fix_quality,
                        float(GPS.horizontal_dilution),
                        int(GPS.satellites)
                        )

                    # Serialise payload
                    serialised_payload = payload.serialize()

                    # Save data
                    store_data(serialised_payload)

                    # Broadcast all unsent NMEA messages
                    while data := read_data(UNSENT):
                        serialised_payload += FILE_DELIMITER + data
                    
                    radio.broadcast_data(PacketType.NMEA, serialised_payload)
                    # Set RTC datetime to GPS time
                    RTC.datetime = GPS.timestamp_utc

        # If incoming message is tagged as an ACK
        elif packet.type == PacketType.ACK and struct.unpack(radio.FormatStrings.PACKET_DEVICE_ID, packet.payload)[0] == DEVICE_ID:
            print ("ACK received. Stopping...")
            break

if __name__ == "__main__":
    asyncio.run(asyncio.wait_for_ms(rover_loop(), GLOBAL_FAILSAFE_TIMEOUT * 1000))
    shutdown()