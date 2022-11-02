'''
Base, inheriting from Device, is an object to represent base stations. This contains 
'''

import time
from Device import * #EVERYTHING FROM THIS IS READONLY (you can use write functions, but cannot actually modify a variable)
import Device #USE THIS TO MODIFY VARIABLES (e.g. Device.device_ID = 1, not device_ID = 1)
from Radio import *
from enum import Enum
from asyncio.timeouts import Timeout

import pynmea2

ROVER_COUNT = 3

GSM_UART: busio.UART = busio.UART(board.A2, board.A1, baudrate=9600)

class GPSData:
    lat: float
    long: float
    temperature: int
    timestamp: int

    def __init__(self, lat, long, temperature, timestamp):
        self.lat = lat
        self.long = long
        self.temperature = temperature
        self.timestamp = timestamp

#this is a global variable so i can still get the data even if the rover loop times out
rover_data: dict[int, GPSData] = {}
for i in range(ROVER_COUNT):
        rover_data[i] = None

def get_corrections():
    '''Returns the corrections from the GPS as a bytearray'''
    # Read UART for newline terminated data - produces bytestr
    return GPS_UART.readline()
    # TODO: add timeout

async def rtcm3_loop():
    '''Runs continuously but in parallel. Attempts to send GPS uart readings every second (approx.)'''
    while not None in rover_data.values: #Finish running when rover data is done
        print("Getting RTCM3 and broadcasting...\r\n")
        radio_broadcast(PacketType.RTCM3, GPS_UART.readline()) #pls no break TODO: timeout for hw failure
        print("Corrections sent \r\n")
        asyncio.sleep(1)

async def rover_data_loop():
    while not None in rover_data:
        packet = await async_radio_receive()
        if packet.type == PacketType.NMEA:
            print("Received NMEA...\r\n")
            if not rover_data[packet.sender]:
                print("Received NMEA from a new rover,", packet.sender, "\r\n")
                gps = pynmea2.parse(packet.payload)
                if gps.gps_qual == '4':
                    print("NMEA data quality 4, saving data...\r\n")
                    rover_data[packet.sender] = GPSData(gps.lat, gps.long, 0, time.time())
            
            if rover_data[packet.sender]:
                print("Sending ACK to rover", packet.sender, "\r\n")
                send_ack(packet.sender)


        
if __name__ == "__main__":
    #Base needs to:
    #Get RTCM3 correction.
    #Send RTCM3 data
    #Receive packet
    #If GPS data received:
    # If rover not already received, store GPS data.
    # Send ACK to rover
    #end
    try:
        asyncio.wait_for(asyncio.gather(rover_data_loop(), rtcm3_loop()), ROVER_COMMS_TIMEOUT)
    except TimeoutError:
        pass #Don't care, we have data, just send what we got

    
    
    #We have as much data as we're gonna get, ship it off now
    #TODO: Send data