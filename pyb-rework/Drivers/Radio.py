# Consts
import struct
import binascii
import Drivers.AsyncUART as AsyncUART
import board
from config import *
from debug import *

UART: AsyncUART.AsyncUART = AsyncUART.AsyncUART(board.D11, board.D10, baudrate=9600, timeout=5)

class ChecksumError(Exception):
    pass

class FormatStrings():
    PACKET_TYPE = 'b'
    PACKET_DEVICE_ID = 'b'
    PACKET_CHECKSUM = 'I'
    PACKET_LENGTH = 'I'
    PACKET_MARKER = 'B'

class PacketType():
    # RTS = 1
    # CTS = 2
    ACK = 3
    NMEA = 4
    RTCM3 = 5
    # RETRANSMIT = 6
    # FINISHED_TRANSMIT = 7

class RadioPacket:
    '''Helper class for packing data into a nice format'''
    type: PacketType
    payload: bytes
    sender: int

    def __init__(self, type: PacketType, payload: bytes, sender_ID: int):
        self.type = type
        self.payload = bytes(payload) #for many resiliency
        self.sender = sender_ID
    
    def serialize(self):
        '''Serializes a data packet into a byte array ready for sending over radio.
        Includes checksum.'''
        #debug("PAYLOAD_AFTER_CONSTRUCTOR:", self.payload)
        payload = struct.pack(FormatStrings.PACKET_TYPE + FormatStrings.PACKET_DEVICE_ID, self.type, self.sender)
        payload += self.payload
        #debug("SERIALIZED_PAYLORD_NO_CHECKSUM:", payload)
        checksum = binascii.crc32(payload)
        output = payload + struct.pack(FormatStrings.PACKET_CHECKSUM, checksum)
        #debug("FULL_SERIALIZED_PACKET:", output)
        return output
    
    def deserialize(data: bytes):
        '''Deserializes a received byte array into a Packet class.
        Includes checksum validation (can error)'''
        #debug("RAW:", data)
        checksum = struct.unpack(FormatStrings.PACKET_CHECKSUM, data[-4:])[0]
        debug("CHECKSUM:", checksum)
        payload = data[:-4]
        if binascii.crc32(payload) != checksum:
            raise ChecksumError
        
        header = payload[:2]
        payload = payload[2:]

        packetType, sender = struct.unpack(FormatStrings.PACKET_TYPE + FormatStrings.PACKET_DEVICE_ID, header)

        return RadioPacket(packetType, payload, sender)

async def receive_packet():
    '''Receives a single valid radio packet asynchronously.
    (async waits until one is received, that is)'''
    packet = None
    while packet is None:
        marker = None
        while marker != 0x80:
            marker = await UART.__async_get_byte_forever()
        size = await UART.async_read_forever(4)
        debug("RAWSIZE:", size)
        size = struct.unpack('I', size)[0]
        if size == 0:
            continue
        data = await UART.async_read(size)
        #debug("RAWDATA:", data)
        if data is None or len(data) < size:
            continue #Packet is garbage, start again
        try:
            packet = RadioPacket.deserialize(data)
        except ChecksumError:
            debug("CHECKSUM_FAIL")
            continue #Packet failed checksum check, it's garbage, start again
    
    #If we get here, packet was deserialized successfully
    return packet

def broadcast_packet(packet: RadioPacket):
    '''Serializes and sends a `RadioPacket` over the radio'''
    packetRaw = packet.serialize()
    size = len(packetRaw)
    sizeRaw = struct.pack(FormatStrings.PACKET_LENGTH, size)
    marker = struct.pack(FormatStrings.PACKET_MARKER, 0x80)
    UART.write(marker + sizeRaw + packetRaw)

def broadcast_data(type: PacketType, payload: bytes):
    '''Creates a packet and broadcasts it over radio'''
    broadcast_packet(RadioPacket(type, payload, DEVICE_ID))

def send_ack(sender: int):
    '''Broadcasts an ACK intended for `sender`'''
    broadcast_data(PacketType.ACK, struct.pack(FormatStrings.PACKET_DEVICE_ID, sender))
