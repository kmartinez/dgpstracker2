'''
Base, inheriting from Device, is an object to represent base stations. This contains 
'''

import time
from Device import * #EVERYTHING FROM THIS IS READONLY (you can use write functions, but cannot actually modify a variable)
import Device #USE THIS TO MODIFY VARIABLES (e.g. Device.device_ID = 1, not device_ID = 1)
from Radio import *
from enum import Enum

class CommunicationState(Enum):
    WAITING_FOR_GPS: 0
    NMEA_RECEIVED: 1

ROVER_COUNT = 3

rover_comms_states: dict[int, CommunicationState] = {}

rover_NMEA: list[bytearray] = []
'''Contains rover NMEA responses'''

def get_corrections():
    '''Returns the corrections from the GPS as a bytearray'''
    # Read UART for newline terminated data - produces bytestr
    return GPS_UART_RTCM3.readline()
    # TODO: add timeout

def received_nmea(data,sender):
    '''If NMEA data is received,, save the data and check if the sender is in the list of senders requiring ACKs'''
    #TODO: verify NMEA is valid
    if NMEA_IS_VALID:
        if rover_comms_states[sender] == CommunicationState.WAITING_FOR_GPS:
            rover_NMEA.append(data)
        rover_comms_states[sender] = CommunicationState.NMEA_RECEIVED
        radio_broadcast(sender, ACK_CODE)

def get_rover_data():
    '''Loop for communicating with rover'''
    RTC.alarm2 = (time.struct_time(time.mktime(RTC.datetime) + ROVER_COMMS_TIMEOUT), "secondly")

    # While all rovers are unreceived and timeout is not acheived...
    while not RTC.alarm2_status:
        # Send corrections
        radio_broadcast(get_corrections(), RTCM3_CODE)
        # Listen for returning communications
        try:
            # Check for incoming NMEA for 1s (1s is the timeout configured for the radio UART)
            data_type, data, sender = radio_receive()
        
            # If incoming message is tagged as NMEA
            if data_type == NMEA_CODE:
                received_nmea(data)

        # If checksum fails
        except Device.ChecksumError:
            pass # Rover will keep sending until ACK received anyway...
            #radio.broadcast(None, RETRANSMIT_CODE)

        # If timeout occurred waiting for data
        except TimeoutError:
            pass

        if sum(rover_comms_states.values > (ROVER_COUNT * CommunicationState.NMEA_RECEIVED)):
            break
        

Device.device_ID = 1 #TODO: see if i can put this in device somehow