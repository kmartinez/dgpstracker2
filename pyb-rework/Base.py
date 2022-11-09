'''
Base, inheriting from Device, is an object to represent base stations. This contains 
'''

import time
from Device import * #EVERYTHING FROM THIS IS READONLY (you can use write functions, but cannot actually modify a variable)
import Device #USE THIS TO MODIFY VARIABLES (e.g. Device.device_ID = 1, not device_ID = 1)
# import Drivers.Radio as radio
# from Drivers.Radio import PacketType
import asyncio
from debug import *
from config import *

ROVER_COUNT = 3

GSM_UART: busio.UART = busio.UART(board.A5, board.D6, baudrate=9600)

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

async def get_corrections():
    '''Returns the corrections from the GPS as a bytearray'''
    # Read UART for newline terminated data - produces bytestr
    debug("GETTING_RTCM3")
    RTCM3_UART.reset_input_buffer()
    await RTCM3_UART.async_readline() #Garbled maybe
    data = bytearray()
    for i in range(5):
        data += await RTCM3_UART.async_readline()
    debug("RTCM3_RECEIVED")
    return bytes(data)

async def rtcm3_loop():
    '''Runs continuously but in parallel. Attempts to send GPS uart readings every second (approx.)'''
    debug("Beginning rtcm3_loop")
    while None in rover_data.values(): #Finish running when rover data is done
        debug("ROVER_LOOP_START")
        gps_data = await get_corrections()
        debug("GPS_RAW_BYTES:", gps_data)
        radio.broadcast_data(PacketType.RTCM3, gps_data)
        debug("RTCM3_RADIO_BROADCAST_COMPLETE")
        #await asyncio.sleep(1)
    debug("End RTCM3 Loop")

async def rover_data_loop():
    debug("Beginning rover_data_loop")
    while not None in rover_data:
        packet = await radio.receive_packet()
        if packet.type == PacketType.NMEA:
            debug("Received NMEA...")
            if not rover_data[packet.sender]:
                debug("Received NMEA from a new rover,", packet.sender)
                raw = validate_NMEA(packet.payload)
                if raw != None:
                    rover_data[packet.sender] = GPSData(GPS.latitude, GPS.longitude, 0, GPS.timestamp_utc)
            
            if rover_data[packet.sender]:
                debug("Sending ACK to rover", packet.sender)
                radio.send_ack(packet.sender)
                

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    #Base needs to:
    #Get RTCM3 correction.
    #Send RTCM3 data
    #Receive packet
    #If GPS data received:
    # If rover not already received, store GPS data.
    # Send ACK to rover
    #end
    try:
        debug("Begin ASYNC...")
        loop.run_until_complete(asyncio.wait_for_ms(asyncio.gather(rover_data_loop(), rtcm3_loop()), GLOBAL_FAILSAFE_TIMEOUT * 1000))
        debug("Finished ASYNC...")
    except TimeoutError:
        debug("Timeout!")
        pass #Don't care, we have data, just send what we got

    # debug("Begin ASYNC...")
    # loop.create_task(rover_data_loop())
    # loop.create_task(rtcm3_loop())
    # loop.run_forever()
    # debug("Finished ASYNC...")