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
import digitalio
from RadioMessages.GPSData import *

import adafruit_requests as requests
from adafruit_fona.adafruit_fona import FONA
from adafruit_fona.fona_3g import FONA3G
import adafruit_fona.adafruit_fona_network as network
import adafruit_fona.adafruit_fona_socket as cellular_socket

ROVER_COUNT = 3

GSM_UART: busio.UART = busio.UART(board.A5, board.D6, baudrate=9600)
GSM_RST_PIN: digitalio.DigitalInOut(board.D4) #TODO: Find an actual pin for this

#this is a global variable so i can still get the data even if the rover loop times out
rover_data: dict[int, GPSData] = {}
for i in range(ROVER_COUNT):
        rover_data[i] = None

async def get_corrections():
    """Returns the corrections from the GPS as a bytearray

    :return: Bytes object of the 5 RTCM3 messages
    :rtype: bytes()
    """
    # Read UART for newline terminated data - produces bytestr
    debug("GETTING_RTCM3")
    RTCM3_UART.reset_input_buffer()
    await RTCM3_UART.aysnc_read_RTCM3_packet_forever() #Garbled maybe
    data = bytearray()
    for i in range(5):
        d = await RTCM3_UART.aysnc_read_RTCM3_packet_forever()
        data += d
        debug("SINGLE RTCM3 MESSAGE:", d)
    debug("RTCM3_RECEIVED")
    return bytes(data)

async def rtcm3_loop():
    """Runs continuously but in parallel. Attempts to send GPS uart readings every second (approx.)
    """
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
    """Runs continuously but in parallel. Attempts to receive data from the rovers and proecess that data
    """
    debug("Beginning rover_data_loop")
    while not None in rover_data:
        packet = await radio.receive_packet()
        if packet.type == PacketType.NMEA:
            debug("Received NMEA...")
            if not rover_data[packet.sender]:
                debug("Received NMEA from a new rover,", packet.sender)
                rover_data[packet.sender] = GPSData.deserialize(packet.payload) #TODO: validation maybe?
            
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

    fona = FONA(GSM_UART, GSM_RST_PIN)
    debug("FONA VERSION:", fona.version)

    # Initialize cellular data network
    network = network.CELLULAR(
        fona, (SECRETS["apn"], SECRETS["apn_username"], SECRETS["apn_password"])
    )

    while not network.is_attached:
        debug("Attaching to network...")
        time.sleep(0.5)
    debug("Attached!")

    while not network.is_connected:
        debug("Connecting to network...")
        network.connect()
        time.sleep(0.5)
    debug("Network Connected!")

    print("My Local IP address is:", fona.local_ip)

    # Initialize a requests object with a socket and cellular interface
    requests.set_socket(cellular_socket, fona)

    payload = []
    for k,v in rover_data:
        v.id = k
        v.iemi = fona.iemi
        payload.append(v)

    requests.post("http://MYCOOLAPI.COM/api/ingest", json=payload)