from Device import *
from Radio import *
#import pynmea2
#from pynmea2.nmea import NMEASentence

import io

def get_nmea(self):
    GPS_UART.readline()

def process_rtcm3(self, rtcm3):
    '''If rtcm3 data is received, send it to the GPS and wait for an NMEA response. If no NMEA response if found, `pass` \n
    If NMEA data is found, send it to the base station and look for an ACK in return. If not ACK then repeat this loop until timeout.'''
    GPS_UART.send(rtcm3)

    raw = GPS_UART.readline()

    #nmea = pynmea2.parse(raw)
    return validate_NMEA(raw)


if __name__ == "__main__":
    # Rover needs to:
    # Receive packet
    # If RTCM3 received, get NMEA and send it
    # If ACK received, shutdown
    while True:
        print("I'm a rover!\r\n")
    while True:
    # Wait for rtcm3 data
        try:
            # Check for incoming RTCM for 1s (1s is the timeout configured for the radio UART)
            print("Waiting for incoming RTCM3...\r\n")
            packet = radio_receive()

            # If incoming message is tagged as RTCM3
            if packet.type == PacketType.RTCM3:
                print("RTCM3 received, waiting for NMEA response\r\n")
                raw, nmea = process_rtcm3(packet.payload)
                if raw != None:
                    print("Sending NMEA data to base station...\r\n")
                    radio_broadcast(PacketType.NMEA, raw)

            # If incoming message is tagged as an ACK
            elif packet.type == PacketType.ACK and struct.unpack('h', packet.payload) == device_ID:
                print ("ACK received. Stopping... \r\n")
                break

        # If checksum fails
        except ChecksumError:
            pass # if rtcm3 bad, who cares. If ACK bad, a new one will be sent soon anyway
            # self.radio.broadcast(None, RETRANSMIT_CODE)