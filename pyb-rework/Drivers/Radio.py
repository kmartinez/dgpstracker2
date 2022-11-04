# Consts
import struct
import binascii
import AsyncUART
import board

UART: AsyncUART.AsyncUART = AsyncUART.AsyncUART(board.D11, board.D10, baudrate=9600)

class ChecksumError(Exception):
    pass

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
        print("PAYLOAD_AFTER_CONSTRUCTOR:", self.payload)
        payload = struct.pack('bb', self.type, self.sender)
        payload += self.payload
        print("SERIALIZED_PAYLORD_NO_CHECKSUM:", payload)
        checksum = binascii.crc32(payload)
        return payload + struct.pack('I', checksum)
    
    def deserialize(data: bytes):
        '''Deserializes a received byte array into a Packet class.
        Includes checksum validation (can error)'''
        print("RAW:", data)
        checksum = struct.unpack('I', data[-4:])
        payload = data[:-4]
        if binascii.crc32(payload) != checksum:
            raise ChecksumError
        
        header = payload[:2]
        payload = payload[2:]

        packetType, sender = struct.unpack('bb', header)

        return RadioPacket(packetType, payload, sender)

async def receive_packet():
    '''Receives a single valid radio packet asynchronously.
    (async waits until one is received, that is)'''
    packet = None
    while packet is None:
        size = await UART.async_read(4)
        size = struct.unpack('I', size)
        data = await UART.async_read_with_timeout(size)
        if data is None or len(data) < size:
            continue #Packet is garbage, start again
        try:
            packet = RadioPacket.deserialize(data)
        except ChecksumError:
            continue #Packet failed checksum check, it's garbage, start again
    
    #If we get here, packet was deserialized successfully
    return packet

def broadcast_packet(packet: RadioPacket):
    '''Serializes and sends a `RadioPacket` over the radio'''
    packetRaw = packet.serialize()
    size = len(packetRaw)
    sizeRaw = struct.pack('I', size)
    UART.write(sizeRaw + packetRaw)