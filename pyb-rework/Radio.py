# Consts
from enum import Enum
import struct

RECEIVE_TIMEOUT = 1
'''Timeout for listening to UART for messages'''

ROVER_COMMS_TIMEOUT = 600
'''Timeout for base station waiting for rovers to finish sending all of their data. Default is 10 mins (600s)'''

class ChecksumError(Exception):
    pass

class PacketType(Enum):
    RTS = 1
    CTS = 2
    ACK = 3
    NMEA = 4
    RTCM3 = 5
    RETRANSMIT = 6
    FINISHED_TRANSMIT = 7

class RadioPacket:
    type: PacketType
    payload: bytearray
    sender: int

    def __init__(self, type: PacketType, payload: bytes, sender_ID: int):
        self.type = type
        self.payload = payload
        self.sender = sender_ID
    
    def serialize(self):
        '''Serializes a data packet into a byte array ready for sending over radio.
        Includes checksum.'''
        payload = struct.pack('csc', self.type, self.payload, self.sender)
        checksum = sum(payload) #TODO: CRC16
        return struct.pack('sh', payload, checksum)
    
    def deserialize(data: bytes):
        '''Deserializes a received byte array into a Packet class.
        Includes checksum validation (can error)'''
        payload, checksum = struct.unpack('sh', data)
        if sum(payload) != checksum: #TODO: CRC16
            raise ChecksumError
        
        return RadioPacket(*struct.unpack('csc', payload))

