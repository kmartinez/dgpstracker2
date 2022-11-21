from Device import *
# import Drivers.Radio as radio
# from Drivers.Radio import PacketType
import struct
from config import *
from Math.RollingAverage import RollingAverage

SD_MAX = 1e-5 
'''Maximum acceptible standard deviation [m]'''
AVERAGING_SAMPLE_SIZE = 5
'''number of samples to take a rolling standard deviation and average of'''

GPS_SAMPLES: dict[str, RollingAverage] = {
    "lats": RollingAverage(AVERAGING_SAMPLE_SIZE),
    "longs": RollingAverage(AVERAGING_SAMPLE_SIZE),
    "alts": RollingAverage(AVERAGING_SAMPLE_SIZE)
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

                if GPS_SAMPLES["longs"].sd() < SD_MAX and GPS_SAMPLES["lats"].sd() < SD_MAX and GPS_SAMPLES["alts"].sd() < SD_MAX:
                    debug("Sending NMEA data to base station...")
                    #TODO: Proper serialization maybe
                    transmit_str = "lat:" + str(GPS_SAMPLES["lats"].mean())
                    transmit_str += ",long:" + str(GPS_SAMPLES["longs"].mean())
                    transmit_str += ",alt:," + str(GPS_SAMPLES["alts"].mean())
                    transmit_str += ",time:" + str(GPS.timestamp_utc)
                    radio.broadcast_data(PacketType.NMEA, sentence)

        # If incoming message is tagged as an ACK
        elif packet.type == PacketType.ACK and struct.unpack(radio.FormatStrings.PACKET_DEVICE_ID, packet.payload) == DEVICE_ID:
            print ("ACK received. Stopping...")
            break

if __name__ == "__main__":
    asyncio.run(asyncio.wait_for_ms(rover_loop(), GLOBAL_FAILSAFE_TIMEOUT * 1000))