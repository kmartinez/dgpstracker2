from random import Random, random
from Device import *
import time
from Radio import *
class Rover(Device):
    def __init__(self, device_ID):
        super().__init__(device_ID)

    def get_nmea(self):
        self.gps_uart_nmea.readline()

    def receive_rtcm3(self,data):
        '''If rtcm3 data is received, send it to the GPS and wait for an NMEA response. If no NMEA response if found, `pass` \n
        If NMEA data is found, send it to the base station and look for an ACK in return. If not ACK then repeat this loop until timeout.'''
        received_ack = False
        self.gps_uart_rtcm3.send(data)

        nmea = self.gps_uart_nmea.readline()

        # If NMEA received back
        if nmea != None:
            # Start watchdog
            t_start = time.time()
            # Until acknowledgement received or timeout
            while received_ack == False and time.time()-t_start < ROVER_COMMS_TIMEOUT:
                # Wait a random amount of time before retransmitting
                time.sleep(Random.random())
                self.radio_broadcast(nmea, NMEA_CODE)

                # Listen for ACK
                try:
                    data_type, data, sender_ID = self.radio_receive()
                    if data_type == ACK_CODE and data == self.device_ID:
                        return True

                except ChecksumError:
                    pass # Don't care! data will be resent anyway!
                    # self.radio_broadcast(None, RETRANSMIT_CODE)
                

    def receive_ack(self):
        self.radio_broacst(None,ACK_CODE)

    def send_rover_data(self):
        # Wait for rtcm3 data
        try:
            # Check for incoming NMEA for 1s (1s is the timeout configured for the radio UART)
            data_type, data, sender = self.radio_receive()

            # If sender has already finished sending
            if sender in self.sent_IDs:
                pass

            # If incoming message is tagged as NMEA
            elif data_type == RTCM3_CODE:
                self.receive_rtcm3(data)

            # If incoming message is tagged as an ACK
            elif data_type == ACK_CODE:
                self.receive_ack()

            else:
                pass

        # If checksum fails
        except ChecksumError:
            pass # if rtcm3 bad, who cares. If ACK bad, a new one will be sent soon anyway
            # self.radio.broadcast(None, RETRANSMIT_CODE)

    