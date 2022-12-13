'''
Base, inheriting from Device, is an object to represent base stations. This contains 
'''

import time
from Device import * #EVERYTHING FROM THIS IS READONLY (you can use write functions, but cannot actually modify a variable)
import Device #USE THIS TO MODIFY VARIABLES (e.g. Device.device_ID = 1, not device_ID = 1)
# import Drivers.Radio as radio
# from Drivers.Radio import PacketType
import asyncio
from config import *
import digitalio
from RadioMessages.GPSData import *
import struct

import adafruit_requests as requests
from adafruit_fona.adafruit_fona import FONA
from adafruit_fona.fona_3g import FONA3G
import adafruit_fona.adafruit_fona_network as network
import adafruit_fona.adafruit_fona_socket as cellular_socket
from Drivers.FileFuncs import *

GSM_UART: busio.UART = busio.UART(board.A5, board.D6, baudrate=9600)
GSM_RST_PIN: digitalio.DigitalInOut = digitalio.DigitalInOut(board.D5) #TODO: Find an actual pin for this

def debug(
    *values: object,
) -> None:
    
    if DEBUG["LOGGING"]["BASE"]:
        print(*values)

#this is a global variable so i can still get the data even if the rover loop times out
rover_data: dict[int, GPSData] = {}
for i in range(1, ROVER_COUNT + 1): #ROVER_COUNT is 1 indexed because 0 is the base
    debug("FILLING_NONE_DATA_FOR_ROVER:", i)
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
    debug("RTCM3_RECEIVED")
    return bytes(data)

async def rtcm3_loop():
    """Runs continuously but in parallel. Attempts to send GPS uart readings every second (approx.)
    """
    debug("Beginning rtcm3_loop")
    while None in rover_data.values(): #Finish running when rover data is done
        gps_data = await get_corrections()
        radio.broadcast_data(PacketType.RTCM3, gps_data)
    debug("End RTCM3 Loop")

async def rover_data_loop():
    """Runs continuously but in parallel. Attempts to receive data from the rovers and proecess that data
    """
    debug("BEGIN_ROVER_DATA_LOOP")
    while None in rover_data.values(): #While there are any Nones in rover_data
        try:
            packet = await radio.receive_packet()
            debug("PACKET_RECEIVED_IN_ROVER_DATA_LOOP")
        except radio.ChecksumError:
            debug("ROVER_LOOP_PKT_CHECKSUM_FAIL")
            packet = None
        if packet is None: continue
        elif packet.type == PacketType.NMEA:
            debug("NMEA_RECEIVED")
            debug("FROM_SENDER:", packet.sender)
            if packet.sender < 0 or packet.sender > len(rover_data) - 1:
                raise ValueError(f"Rover has ID, {packet.sender}, is not within the bounds {[0, ROVER_COUNT]}\n"
                                + f"Please check the rover ID and the ROVER_COUNT in config")
            if not rover_data[packet.sender]:
                debug("Received NMEA from a new rover,", packet.sender)
                rover_data[packet.sender] = GPSData.deserialize(packet.payload)
            
            if rover_data[packet.sender]:
                debug("Sending ACK to rover", packet.sender)
                radio.send_ack(packet.sender)

    debug("ROVER_DATA_LOOP_FINISH")
                

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
        loop.run_until_complete(asyncio.wait_for_ms(asyncio.gather(asyncio.create_task(rover_data_loop()), asyncio.create_task(rtcm3_loop())), GLOBAL_FAILSAFE_TIMEOUT * 1000))
        debug("Finished ASYNC...")
    except asyncio.TimeoutError:
        debug("Timeout!")
        pass #Don't care, we have data, just send what we got

    # debug("Begin ASYNC...")
    # loop.create_task(rover_data_loop())
    # loop.create_task(rtcm3_loop())
    # loop.run_forever()
    # debug("Finished ASYNC...")

    fona = FONA(GSM_UART, GSM_RST_PIN, debug=True)
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
    for k in rover_data:
        for d in rover_data[k]:
            v = d
            v['rover_id'] = k
            payload.append(v)

    try:
        requests.post("http://iotgate.ecs.soton.ac.uk/glacsweb/api/ingest", json=payload)
    except:
        store_data(payload, UNSENT)
        shutdown()
    shutdown()