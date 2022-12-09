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
import struct

import adafruit_requests as requests
from adafruit_fona.adafruit_fona import FONA
from adafruit_fona.fona_3g import FONA3G
import adafruit_fona.adafruit_fona_network as network
import adafruit_fona.adafruit_fona_socket as cellular_socket

GSM_UART: busio.UART = busio.UART(board.A5, board.D6, baudrate=9600)
GSM_RST_PIN: digitalio.DigitalInOut = digitalio.DigitalInOut(board.D5) #TODO: Find an actual pin for this

radio_locked = False

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
        #debug("SINGLE RTCM3 MESSAGE:", d)
    debug("RTCM3_RECEIVED")
    return bytes(data)

async def rtcm3_loop():
    """Runs continuously but in parallel. Attempts to send GPS uart readings every second (approx.)
    """
    global radio_locked

    debug("Beginning rtcm3_loop")
    while None in rover_data.values(): #Finish running when rover data is done
        # debug("RTCM_LOOP_START")
        gps_data = await get_corrections()
        # debug("GPS_RAW_BYTES:", gps_data)
        while radio_locked: #wait for unlocked radio
            #debug("RADIO_BUFFER_SIZE:", radio.UART.in_waiting)
            await asyncio.sleep_ms(0)
        radio_locked = True #probably not necessary but here for completeness
        radio.broadcast_data(PacketType.RTCM3, gps_data)
        radio_locked = False
        # debug("RTCM3_RADIO_BROADCAST_COMPLETE")
        #await asyncio.sleep(1)
    debug("End RTCM3 Loop")

async def rover_data_loop():
    """Runs continuously but in parallel. Attempts to receive data from the rovers and proecess that data
    """
    global radio_locked

    debug("Beginning rover_data_loop")
    while None in rover_data.values(): #While there are any Nones in rover_data
        try:
            debug("CONTROL_ROVER_LOOP_WAIT_FOR_PKT")
            packet = await asyncio.wait_for(radio.receive_packet(), 1.5)
            debug("CONTROL_ROVER_LOOP_FINISH_PKT")
        except asyncio.TimeoutError:
            debug("CONTROL_ROVER_LOOP_PKT_TIMEOUT")
            packet = None
            radio_locked = False #no deadlock pls
        except radio.ChecksumError:
            debug("CONTROL_ROVER_LOOP_PKT_CHECKSUM_FAIL")
            packet = None
            radio_locked = False #no deadlock pls
        debug("PACKET_RECEIVED_IN_ROVER_DATA_LOOP")
        if packet is None: continue
        elif packet.type == PacketType.NMEA:
            radio_locked = False
            debug("Received NMEA...")
            debug("FROM_SENDER:", packet.sender)
            if not rover_data[packet.sender]:
                debug("Received NMEA from a new rover,", packet.sender)
                rover_data[packet.sender] = GPSData.deserialize(packet.payload) #TODO: validation maybe?
            
            if rover_data[packet.sender]:
                debug("Sending ACK to rover", packet.sender)
                radio.send_ack(packet.sender)
        elif packet.type == PacketType.RTS:
            if radio_locked: continue
            debug("RECEIVED RTS")
            radio_locked = True
            radio.broadcast_data(PacketType.CTS, struct.pack(radio.FormatStrings.PACKET_DEVICE_ID, packet.sender))

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
    for k in rover_data:
        v = rover_data[k]
        v['id'] = k
        v['imei'] = fona.iemi
        payload.append(v)

    requests.post("http://google.com/api/ingest", json=payload)
    shutdown()