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
import os

GSM_UART: busio.UART = busio.UART(board.A5, board.D6, baudrate=9600)
GSM_RST_PIN: digitalio.DigitalInOut = digitalio.DigitalInOut(board.D5) #TODO: Find an actual pin for this

def debug(
    *values: object,
) -> None:
    
    if DEBUG["LOGGING"]["BASE"]:
        print(*values)

#this is a global variable so i can still get the data even if the rover loop times out
finished_rovers: dict[int, bool] = {}

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
    while len(finished_rovers) < ROVER_COUNT: #Finish running when rover data is done
        rtcm3_data = await get_corrections()
        radio.broadcast_data(PacketType.RTCM3, rtcm3_data)
    debug("End RTCM3 Loop")

async def rover_data_loop():
    """Runs continuously but in parallel. Attempts to receive data from the rovers and proecess that data
    """
    debug("BEGIN_ROVER_DATA_LOOP")
    while len(finished_rovers) < ROVER_COUNT: #While there are any Nones in rover_data
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
            if packet.sender < 0:
                raise ValueError(f"Rover has ID, {packet.sender}, is not within bounds (>0)\n"
                                + f"Please check the rover ID and the ROVER_COUNT in config")
            data = GPSData.from_json(packet.payload.decode('utf-8'))
            with open("/data_entries/" + str(packet.sender) + "-" + data["timestamp"].replace(":", "_"), "w") as file:
                data['rover-id'] = packet.sender
                file.write(json.dumps(data) + '\n')
                debug("Sending ACK to rover", packet.sender)
                radio.send_response(PacketType.ACK, packet.sender)

        elif packet.type == PacketType.FIN and struct.unpack(radio.FormatStrings.PACKET_DEVICE_ID, packet.payload)[0] == DEVICE_ID:
            finished_rovers[packet.sender] = True
            radio.send_response(PacketType.FIN, packet.sender)
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

    http_payload = []
    data_paths = os.listdir("/data_entries/")
    for path in data_paths:
        with open("/data_entries/" + path, "r") as file:
            http_payload.append(json.loads(file.readline()))
            #TODO: RAM limit

    try:
        #response = requests.post("http://iotgate.ecs.soton.ac.uk/glacsweb/api/ingest", json=http_payload)
        requests.post("http://google.com/glacsweb/api/ingest", json=http_payload)
        #TODO: check if response OK
        paths_sent = os.listdir("/data_entries/")
        for path in paths_sent:
            os.remove("/data_entries/" + path)
    finally:
        shutdown()