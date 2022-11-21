from Device import *
# import Drivers.Radio as radio
# from Drivers.Radio import PacketType
import struct
from config import *
from Statistics.StatsBuffer import StatsBuffer
import ulab.numpy as np

SD_MAX = 1e-5 
'''Maximum acceptible standard deviation [m]'''
AVERAGING_SAMPLE_SIZE = 5
'''number of samples to take a rolling standard deviation and average of'''

GPS_SAMPLES: dict[str, StatsBuffer] = {
    "lats": StatsBuffer(AVERAGING_SAMPLE_SIZE),
    "longs": StatsBuffer(AVERAGING_SAMPLE_SIZE),
    "alts": StatsBuffer(AVERAGING_SAMPLE_SIZE)
}

def update_gps_with_rtcm3(rtcm3):
    '''If rtcm3 data is received, send it to the GPS and wait for an NMEA response. If no NMEA response if found, `pass`.
    If NMEA data is found, send it to the base station and look for an ACK in return. If not ACK then repeat this loop until timeout.'''
    #debug("RTCM3:", rtcm3)
    RTCM3_UART.write(rtcm3)

    #nmea = pynmea2.parse(raw)
    return update_GPS()

async def rover_loop():
    # Rover needs to:
    # Receive packet
    # If RTCM3 received, get NMEA and send it
    # If ACK received, shutdown
    while True:
        debug("Waiting for incoming RTCM3...")
        packet = await radio.receive_packet()

        # If incoming message is tagged as RTCM3
        if packet.type == PacketType.RTCM3:
            debug("RTCM3 received, waiting for NMEA response")
            sentence = update_gps_with_rtcm3(packet.payload)
            #debug("GPS SENTENCE", GPS.nmea_sentence)
            if sentence != None:
                GPS_SAMPLES["lats"].append(GPS.latitude_degrees)
                GPS_SAMPLES["longs"].append(GPS.longitude_degrees)
                GPS_SAMPLES["alts"].append(GPS.altitude_m)

                if np.std(GPS_SAMPLES["longs"]) < SD_MAX and np.std(GPS_SAMPLES["lats"]) < SD_MAX and np.std(GPS_SAMPLES["alts"]) < SD_MAX:
                    debug("Sending NMEA data to base station...")
                    #TODO: Proper serialization maybe
                    #TODO: Check if this works over iterables or if we need to call np.array() first
                    transmit_str = "lat:" + str(np.mean(GPS_SAMPLES["lats"]))
                    transmit_str += ",long:" + str(np.mean(GPS_SAMPLES["longs"]))
                    transmit_str += ",alt:," + str(np.mean(GPS_SAMPLES["alts"]))
                    transmit_str += ",time:" + str(GPS.timestamp_utc)
                    radio.broadcast_data(PacketType.NMEA, sentence)

        # If incoming message is tagged as an ACK
        elif packet.type == PacketType.ACK and struct.unpack(radio.FormatStrings.PACKET_DEVICE_ID, packet.payload) == DEVICE_ID:
            print ("ACK received. Stopping...")
            break

if __name__ == "__main__":
    asyncio.run(asyncio.wait_for_ms(rover_loop(), GLOBAL_FAILSAFE_TIMEOUT * 1000))