from Device import *
# import Drivers.Radio as radio
# from Drivers.Radio import PacketType
import struct
from config import *

def get_nmea(self):
    GPS_UART.readline()

def get_nmea_using_rtcm3(rtcm3):
    '''If rtcm3 data is received, send it to the GPS and wait for an NMEA response. If no NMEA response if found, `pass` \n
    If NMEA data is found, send it to the base station and look for an ACK in return. If not ACK then repeat this loop until timeout.'''
    RTCM3_UART.send(rtcm3)

    raw = GPS_UART.readline()

    #nmea = pynmea2.parse(raw)
    return validate_NMEA(raw)

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
            raw = get_nmea_using_rtcm3(packet.payload)
            if raw != None:
                debug("Sending NMEA data to base station...")
                radio.broadcast_data(PacketType.NMEA, raw)

        # If incoming message is tagged as an ACK
        elif packet.type == PacketType.ACK and struct.unpack(radio.FormatStrings.PACKET_DEVICE_ID, packet.payload) == DEVICE_ID:
            print ("ACK received. Stopping...")
            break

if __name__ == "__main__":
    asyncio.run(asyncio.wait_for_ms(rover_loop(), GLOBAL_FAILSAFE_TIMEOUT * 1000))