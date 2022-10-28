from time import time
from Device import *
from Radio import *

class Base(Device):
    '''
    Base, inheriting from Device, is an object to represent base stations. This contains 
    '''
    def __init__(self, device_ID, lib_mode):
        super().__init__(device_ID)
        self.rover_rec_count = 0
        '''Denotes which rovers have already been communicated with'''
        self.rover_NMEA = []
        '''Contains rover NMEA responses'''
        self.sent_IDs = []
        '''Contains all rovers whihc have finished communications'''


    def get_corrections(self):
        '''Returns the corrections from the GPS as a bytearray'''
        # Read UART for newline terminated data - produces bytestr
        return self.gps_uart_rtcm3.readline()
        # TODO: add timeout

    def send_acks(self):
        '''Send acknowledgements to rovers which are still sending NMEA data'''
        for recipient in self.ack_list:
            self.radio_broadcast(recipient, ACK_CODE)

    def received_nmea(self,data,sender):
        '''If NMEA data is received,, save the data and check if the sender is in the list of senders requiring ACKs'''
        # TODO: CHECK NMEA
        self.rover_NMEA.append(data)
        if sender not in self.ack_queue:
            self.ack_list.append(sender)

    def get_rover_data(self):
        '''Loop for communicating with rover'''
        t_start = time.time()
        count += 1

        # While all rovers are unreceived and timeout is not acheived...
        while len(self.sent_IDs) < 3 and time.time()-t_start < ROVER_COMMS_TIMEOUT:
            # Send corrections
            self.radio_broadcast(self.get_corrections(), RTCM3_CODE)
            # Listen for returning communications
            try:
                # Check for incoming NMEA for 1s (1s is the timeout configured for the radio UART)
                data_type, data, sender = self.radio_receive()

                # If sender has already finished sending
                if sender in self.sent_IDs:
                    self.radio_broadcast(sender, ACK_CODE)
                # If incoming message is tagged as NMEA
                elif data_type == NMEA_CODE:
                    self.received_nmea(data)
                else:
                    pass

            # If checksum fails
            except Device.ChecksumError:
                pass # Rover will keep sending until ACK received anyway...
                #self.radio.broadcast(None, RETRANSMIT_CODE)

            # If timeout occurred waiting for data
            except TimeoutError:
                pass

        if count >= 3:
            self.send_acks()
            count = 0