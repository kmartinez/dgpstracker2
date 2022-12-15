'''
Base, inheriting from Device, is an object to represent base stations. This contains 
'''
import time
from Drivers.PSU import * #EVERYTHING FROM THIS IS READONLY (you can use write functions, but cannot actually modify a variable)
# import Drivers.Radio as radio
# from Drivers.Radio import PacketType
from config import *
from RadioMessages.GPSData import *
from Drivers.DGPS import GPS_DEVICE
import Drivers.Radio as radio
from Drivers.Radio import PacketType

import adafruit_requests as requests
from adafruit_fona.adafruit_fona import FONA
from adafruit_fona.fona_3g import FONA3G
import adafruit_fona.adafruit_fona_network as network
import adafruit_fona.adafruit_fona_socket as cellular_socket

import asyncio
import digitalio
import struct
import os
from microcontroller import watchdog
import adafruit_logging as logging
import busio

logger = logging.getLogger("BASE")

GSM_UART: busio.UART = busio.UART(board.A5, board.D6, baudrate=9600)
GSM_RST_PIN: digitalio.DigitalInOut = digitalio.DigitalInOut(board.D5) #TODO: Find an actual pin for this

#this is a global variable so i can still get the data even if the rover loop times out
finished_rovers: dict[int, bool] = {}

async def clock_calibrator():
    """Calibrates the clock from GPS time
    """
    while GPS_DEVICE.timestamp_utc == None:
        while not GPS_DEVICE.update():
            pass
        RTC_DEVICE.datetime = GPS_DEVICE.timestamp_utc

async def feed_watchdog():
    while len(finished_rovers) < ROVER_COUNT:
        if not DEBUG["WATCHDOG_DISABLE"]:
            watchdog.feed()
        await asyncio.sleep(0)

async def rtcm3_loop():
    """Runs continuously but in parallel. Attempts to send GPS uart readings every second (approx.)
    """
    while len(finished_rovers) < ROVER_COUNT: #Finish running when rover data is done
        rtcm3_data = await GPS_DEVICE.get_rtcm3_message()
        radio.broadcast_data(PacketType.RTCM3, rtcm3_data)

async def rover_data_loop():
    """Runs continuously but in parallel. Attempts to receive data from the rovers and proecess that data
    """
    while len(finished_rovers) < ROVER_COUNT: #While there are any Nones in rover_data
        try:
            logger.info("Waiting for a radio packet")
            packet = await radio.receive_packet()
            logger.info(f"Radio packet received from device {packet.sender}")
        except radio.ChecksumError:
            logger.warning("Radio has received an invalid packet")
            continue
        if packet.sender < 0:
            logger.warning("""Packet sender's ID is out of bounds!
            Please check the sending device's ID in its config and change it!""")
            continue

        if packet.type == PacketType.NMEA:
            logger.info("Received radio packet is GPS data",)
            if len(packet.payload) < 0:
                logger.warning("Empty GPS data received!!!")
                continue
            data = GPSData.from_json(packet.payload.decode('utf-8'))
            with open("/data_entries/" + str(packet.sender) + "-" + data["timestamp"].replace(":", "_"), "w") as file:
                data['rover_id'] = packet.sender
                logger.debug(f"WRITING_DATA_TO_FILE: {data}")
                file.write(json.dumps(data) + '\n')
            
            radio.send_response(PacketType.ACK, packet.sender)

        elif packet.type == PacketType.FIN and struct.unpack(radio.FormatStrings.PACKET_DEVICE_ID, packet.payload)[0] == DEVICE_ID:
            finished_rovers[packet.sender] = True
            radio.send_response(PacketType.FIN, packet.sender)
        logger.info("Received radio packet successfully processed")
    logger.info("Loop for receiving rover data has ended")
                

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
        logger.info("Starting async tasks")
        loop.run_until_complete(asyncio.wait_for_ms(asyncio.gather(rover_data_loop(), rtcm3_loop(), clock_calibrator(), feed_watchdog()), GLOBAL_FAILSAFE_TIMEOUT * 1000))
        logger.info("Async tasks have finished running")
    except asyncio.TimeoutError:
        logger.warning("Async tasks timed out! Continuing with any remaining data")
        pass #Don't care, we have data, just send what we got

    enable_fona()
    fona = FONA(GSM_UART, GSM_RST_PIN, debug=True)
    logger.info("FONA initialized")
    logger.debug(f"FONA VERSION: fona.version")

    network = network.CELLULAR(
        fona, (SECRETS["apn"], SECRETS["apn_username"], SECRETS["apn_password"])
    )

    while not network.is_attached:
        logger.info("Attaching to network...")
        time.sleep(0.5)
    logger.info("Attached!")

    while not network.is_connected:
        logger.info("Connecting to network...")
        network.connect()
        time.sleep(0.5)
    logger.info("Network Connected!")

    logger.info(f"My Local IP address is: {fona.local_ip}")

    # Initialize a requests object with a socket and cellular interface
    requests.set_socket(cellular_socket, fona)

    http_payload = []
    data_paths = os.listdir("/data_entries/")
    for path in data_paths:
        with open("/data_entries/" + path, "r") as file:
            try:
                http_payload.append(json.loads(file.readline()))
            except:
                os.remove("/data_entries/" + path)
            #TODO: RAM limit
    logger.debug(f"HTTP_PAYLOAD: {http_payload}")

    try:
        logger.info("Sending HTTP request!")
        response = requests.post("http://iotgate.ecs.soton.ac.uk/glacsweb/api/ingest", json=http_payload)
        print("STATUS CODE:", response.status_code, "\nREASON:", response.reason)
        #requests.post("http://google.com/glacsweb/api/ingest", json=http_payload)
        #TODO: check if response OK
        if str(response.status_code) == "200":
            paths_sent = os.listdir("/data_entries/")
            for path in paths_sent:
                os.rename("/data_entries/" + path, "/sent_data/" + path)
            logger.info("HTTP request successful! Removing all sent data")
        else:
            logger.warning(f"STATUS CODE: {response.status_code}, REASON: {response.reason}")
    finally:
        shutdown()