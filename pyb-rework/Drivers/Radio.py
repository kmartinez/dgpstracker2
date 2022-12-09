# Consts
import struct
import binascii
import Drivers.AsyncUART as AsyncUART
import board
from config import *
from debug import *

UART: AsyncUART.AsyncUART = AsyncUART.AsyncUART(board.D11, board.D10, baudrate=9600, receiver_buffer_size=2048)

class ChecksumError(Exception):
    pass

class FormatStrings():
    PACKET_TYPE = 'b'
    PACKET_DEVICE_ID = 'b'
    PACKET_CHECKSUM = 'I'
    PACKET_LENGTH = 'I'
    PACKET_MARKER = 'B'

class PacketType():
    RTS = 1
    CTS = 2
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
    
    def serialize(self) -> bytes:
        """Serializes a data packet into a byte array ready for sending over radio.
        Includes checksum.

        :return: Serialized byte array
        :rtype: bytes
        """
        #debug("PAYLOAD_AFTER_CONSTRUCTOR:", self.payload)
        payload = struct.pack(FormatStrings.PACKET_TYPE + FormatStrings.PACKET_DEVICE_ID, self.type, self.sender)
        payload += self.payload
        #debug("SERIALIZED_PAYLORD_NO_CHECKSUM:", payload)
        checksum = binascii.crc32(payload)
        debug("CHECKSUM_SEND:", checksum)
        output = payload + struct.pack(FormatStrings.PACKET_CHECKSUM, checksum)
        #debug("FULL_SERIALIZED_PACKET:", output)
        return output
    
    def deserialize(data: bytes):
        """Deserializes a received byte array into a packet class.
        Includes checksum validation (raises exception on incorrect checksum)

        :param data: Bytes to deserialize
        :type data: bytes
        :raises ChecksumError: Error indicating the packet was invalid
        :return: Deserialized packet
        :rtype: RadioPacket
        """
        #debug("RAW:", data)
        checksum = struct.unpack(FormatStrings.PACKET_CHECKSUM, data[-4:])[0]
        payload = data[:-4]
        debug("CHECKSUM:", checksum)
        debug("PAYLOAD:", payload)
        debug("CALCULATED_CHECKSUM:", binascii.crc32(payload))
        if binascii.crc32(payload) != checksum:
            raise ChecksumError
        
        header = payload[:2]
        payload = payload[2:]

        packetType, sender = struct.unpack(FormatStrings.PACKET_TYPE + FormatStrings.PACKET_DEVICE_ID, header)

        return RadioPacket(packetType, payload, sender)

async def receive_packet() -> RadioPacket:
    """Receives a single valid radio packet asynchronously.
    (does not timeout, but can checksum error)

    :return: Received packet
    :rtype: RadioPacket
    """
    packet = None
    while packet is None:
        marker = None
        debug("WAIT_FOR_MARKER")
        await UART.async_read_until_forever(bytes([0x80,0x80]))
        size = await UART.async_read_forever(4)
        debug("RAWSIZE:", size)
        size = struct.unpack('I', size)[0]
        if size == 0 or size > 1000:
            debug("PACKET_SIZE_INVALID")
            continue
        data = await UART.async_read(size)
        #debug("RAWDATA:", data)
        if data is None or len(data) < size:
            debug("PACKET_SIZE_WRONG")
            continue #Packet is garbage, start again
        packet = RadioPacket.deserialize(data)
    
    #If we get here, packet was deserialized successfully
    return packet

def broadcast_packet(packet: RadioPacket):
    """Broadcasts a RadioPacket over the serial connected radio

    :param packet: Packet to send
    :type packet: RadioPacket
    """
    debug("BROADCASTING!!!")
    packetRaw = packet.serialize()
    size = len(packetRaw)
    sizeRaw = struct.pack(FormatStrings.PACKET_LENGTH, size)
    marker = struct.pack(FormatStrings.PACKET_MARKER, 0x80)
    UART.write(marker + marker + sizeRaw + packetRaw)
    #debug("ENTIRE SENT DATA:", (marker + marker + sizeRaw + packetRaw))
    debug(f'\n\nMARKERS: {marker + marker}\n sizeRaw: {sizeRaw}\n packetRaw: {packetRaw}\n\n')

def broadcast_data(type: PacketType, payload: bytes):
    """Creates a packet for you and send it over radio

    :param type: Type of data
    :type type: PacketType
    :param payload: Serialized data (serialized to bytes)
    :type payload: bytes
    """
    broadcast_packet(RadioPacket(type, payload, DEVICE_ID))

def send_ack(sender: int):
    """Sends an ACK packet to a specified sender (0-255)

    :param sender: ID of device ACK is aimed for (original sender)
    :type sender: int
    """
    broadcast_data(PacketType.ACK, struct.pack(FormatStrings.PACKET_DEVICE_ID, sender))
