"""All code relating to the radio module itself
"""

# Consts
import struct
import binascii
import Drivers.AsyncUART as AsyncUART
import board
from config import *
import adafruit_logging as logging

logger = logging.getLogger("RADIO")

UART: AsyncUART.AsyncUART = AsyncUART.AsyncUART(board.D11, board.D10, baudrate=9600, receiver_buffer_size=2048)

class ChecksumError(Exception):
    """Error representing a failure to verify a checksum of a packet
    (Checksum either could not be verified for some reason or was just incorrect)
    """
    pass

class FormatStrings():
    """pseudo-enum of the various format characters for different parts of packets
    """
    PACKET_TYPE = 'b'
    PACKET_DEVICE_ID = 'b'
    PACKET_CHECKSUM = 'I'
    PACKET_LENGTH = 'I'
    PACKET_MARKER = 'B'

class PacketType():
    """pseudo-enum of different packet type numbers (used for serializing packets)
    """
    RTS = 1
    CTS = 2
    ACK = 3
    NMEA = 4
    RTCM3 = 5
    # RETRANSMIT = 6
    # FINISHED_TRANSMIT = 7
    FIN = 8

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
        logger.debug(f"""SERIALIZE_PACKET:
        PAYLOAD: {binascii.hexlify(self.payload)}
        TYPE_INT: {self.type}
        SENDER_INT: {self.sender}""")

        serialized = struct.pack(FormatStrings.PACKET_TYPE + FormatStrings.PACKET_DEVICE_ID, self.type, self.sender)
        serialized += self.payload
        checksum = binascii.crc32(serialized)
        output = serialized + struct.pack(FormatStrings.PACKET_CHECKSUM, checksum)

        logger.debug(f"SERIALIZED_PACKET_NO_CHECKSUM: {binascii.hexlify(serialized)}")
        logger.debug(f"SERIALIZE_PACKET_CHECKSUM_INT: {checksum}")
        logger.debug(f"FULL_SERIALIZED_PACKET: {binascii.hexlify(output)}")
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
        logger.debug(f"DESERIALIZE_PACKET_RAW_BYTES: {binascii.hexlify(data)}")
        checksum = struct.unpack(FormatStrings.PACKET_CHECKSUM, data[-4:])[0]
        payload = data[:-4]
        logger.debug(f"DESERIALIZE_PACKET_CHECKSUM_INT: {checksum}")
        logger.debug(f"DESERIALIZE_PACKET_NO_CHECKSUM: {binascii.hexlify(payload)}")
        logger.debug(f"DESERIALIZE_PACKET_CALCULATED_CHECKSUM: {binascii.crc32(payload)}")
        if binascii.crc32(payload) != checksum:
            raise ChecksumError
        
        header = payload[:2]
        payload = payload[2:]
        logger.debug(f"DESERIALIZE_PACKET_HEADER_RAW: {binascii.hexlify(header)}")
        logger.debug(f"DESERIALIZE_PACKET_DATA: {binascii.hexlify(payload)}")


        packetType, sender = struct.unpack(FormatStrings.PACKET_TYPE + FormatStrings.PACKET_DEVICE_ID, header)
        logger.debug(f"""HEADER_INFO:
        PACKET_TYPE_INT: {packetType}
        SENDER_INT: {sender}""")

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
        logger.info("Radio waiting for packet marker")
        await UART.async_read_until_forever(bytes([0x80,0x80]))
        logger.info("Packet marker received")
        size = await UART.async_read_forever(4)
        logger.debug(f"PACKET_SIZE: {binascii.hexlify(size)}")
        size = struct.unpack('I', size)[0]
        if size == 0 or size > 1000:
            logger.warning("Radio received invalid packet size!")
            continue
        data = await UART.async_read(size)
        #debug("RAWDATA:", data)
        if data is None or len(data) < size:
            logger.warning("Received packet size did not match actual packet size!")
            continue #Packet is garbage, start again
        packet = RadioPacket.deserialize(data)
    
    #If we get here, packet was deserialized successfully
    logger.info("Radio packet received!")
    return packet

def broadcast_packet(packet: RadioPacket):
    """Broadcasts a RadioPacket over the serial connected radio

    :param packet: Packet to send
    :type packet: RadioPacket
    """
    logger.info("Sending packet!")
    packetRaw = packet.serialize()

    size = len(packetRaw)
    sizeRaw = struct.pack(FormatStrings.PACKET_LENGTH, size)

    marker = struct.pack(FormatStrings.PACKET_MARKER, 0x80)

    UART.write(marker + marker + sizeRaw + packetRaw)
    logger.info("Packet send complete!")

def broadcast_data(type: PacketType, payload: bytes):
    """Creates a packet for you and send it over radio

    :param type: Type of data
    :type type: PacketType
    :param payload: Serialized data (serialized to bytes)
    :type payload: bytes
    """
    broadcast_packet(RadioPacket(type, payload, DEVICE_ID))

def send_response(type: PacketType, sender: int):
    """Sends an ACK packet to a specified sender (0-255)

    :param type: Type of response packet
    :type type: PacketType
    :param sender: ID of device ACK is aimed for (original sender)
    :type sender: int
    """
    broadcast_data(type, struct.pack(FormatStrings.PACKET_DEVICE_ID, sender))
