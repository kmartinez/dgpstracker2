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
        try:
            packet = await radio.receive_packet()
        except radio.ChecksumError:
            continue
        
        # If incoming message is tagged as RTCM3
        if packet.type == PacketType.RTCM3:
            debug("RTCM3 received, waiting for NMEA response")
            sentence = update_gps_with_rtcm3(packet.payload)
            #debug("GPS SENTENCE", GPS.nmea_sentence)
            if sentence is not None:
                GPS_SAMPLES["lats"].append(GPS.latitude)
                GPS_SAMPLES["longs"].append(GPS.longitude)

                #no do standard dev on 1 sample pls
                if (len(GPS_SAMPLES["longs"].circularBuffer) < AVERAGING_SAMPLE_SIZE): continue

                debug("VAR_LONG:", util.var(GPS_SAMPLES["longs"].circularBuffer))

                if util.var(GPS_SAMPLES["longs"].circularBuffer) < VAR_MAX and util.var(GPS_SAMPLES["lats"].circularBuffer) < VAR_MAX:
                    # send RTS
                    radio.broadcast_data(PacketType.RTS, bytes())

        elif packet.type == PacketType.CTS and struct.unpack(FormatStrings.PACKET_DEVICE_ID, packet.payload)[0] == DEVICE_ID:
            debug("Sending NMEA data to base station...")
            #TODO: Proper serialization maybe
            print("GPS TIME:", GPS.timestamp_utc)
            print("GPS_HDOP:", GPS.sats)
            #if GPS.fix_quality in ["R", "r"]:
            #    GPS.fix_quality = 4 #makes things easier
            payload = GPSData(
                datetime.fromtimestamp(time.mktime(GPS.timestamp_utc)),
                util.mean(GPS_SAMPLES["lats"].circularBuffer),
                util.mean(GPS_SAMPLES["longs"].circularBuffer),
                GPS.altitude_m,
                GPS.fix_quality,
                float(GPS.horizontal_dilution),
                int(GPS.satellites)
                )
            radio.broadcast_data(PacketType.NMEA, payload.serialize())
            # radio.broadcast_data(PacketType.NMEA, payload.serialize())
            # radio.broadcast_data(PacketType.NMEA, payload.serialize())
            # radio.broadcast_data(PacketType.NMEA, payload.serialize())
            # radio.broadcast_data(PacketType.NMEA, payload.serialize())

        # If incoming message is tagged as an ACK
        elif packet.type == PacketType.ACK and struct.unpack(radio.FormatStrings.PACKET_DEVICE_ID, packet.payload)[0] == DEVICE_ID:
            print ("ACK received. Stopping...")
            break

if __name__ == "__main__":
    asyncio.run(asyncio.wait_for_ms(rover_loop(), GLOBAL_FAILSAFE_TIMEOUT * 1000))
    shutdown()