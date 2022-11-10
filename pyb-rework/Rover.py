from Device import *
# import Drivers.Radio as radio
# from Drivers.Radio import PacketType
import struct
from config import *

SD_MAX = 1e-5 
'''Maximum acceptible standard deviation [m]'''
AVERAGING_SAMPLE_SIZE = 5
'''number of samples to take a rolling standard deviation and average of'''
NMEA_lats = []
NMEA_longs = []
NMEA_alts = []
lat_sd = 0
long_sd = 0

def mean(list: list[float]):
    '''Returns the mean of a given list'''
    return sum(list)/len(list)

def sd(list: list[float]):
    '''Returns standard deviation given a list'''
    length = len(list)
    li_mean = mean(list)
    list = [(list[i] - li_mean) for i in range(length)]
    var = 1/length * sum([i ** 2 for i in list])
    return var**0.5

async def update_gps_with_rtcm3(rtcm3):
    '''If rtcm3 data is received, send it to the GPS and wait for an NMEA response. If no NMEA response if found, `pass` \n
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
            sentence = await update_gps_with_rtcm3(packet.payload)
            #debug("GPS SENTENCE", GPS.nmea_sentence)
            if sentence != None:
                NMEA_lats.append(GPS.latitude_degrees)
                NMEA_longs.append(GPS.longitude_degrees)
                NMEA_alts.append(GPS.altitude_m)

                if len(NMEA_lats) > AVERAGING_SAMPLE_SIZE:
                    del(NMEA_lats[0])
                    del(NMEA_longs[0])
                    del(NMEA_alts[0])
                
                long_sd = sd(NMEA_longs)
                lat_sd = sd(NMEA_longs)
                alt_sd = sd(NMEA_alts)

                if long_sd < SD_MAX and lat_sd < SD_MAX and alt_sd < SD_MAX:
                    debug("Sending NMEA data to base station...")
                    transmit_str = "lat:" + str(mean(NMEA_lats))
                    transmit_str += ",long:" + str(mean(NMEA_longs))
                    transmit_str += ",alt:," + str(mean(NMEA_alts))
                    transmit_str += ",time:" + str(GPS.timestamp_utc)
                    radio.broadcast_data(PacketType.NMEA, sentence)

        # If incoming message is tagged as an ACK
        elif packet.type == PacketType.ACK and struct.unpack(radio.FormatStrings.PACKET_DEVICE_ID, packet.payload) == DEVICE_ID:
            print ("ACK received. Stopping...")
            break

if __name__ == "__main__":
    asyncio.run(asyncio.wait_for_ms(rover_loop(), GLOBAL_FAILSAFE_TIMEOUT * 1000))