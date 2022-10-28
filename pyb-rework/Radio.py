# Consts
RTS_CODE = 1
CTS_CODE = 2
ACK_CODE = 3
NMEA_CODE = 4
RTCM3_CODE = 5
RETRANSMIT_CODE = 6
FINISHED_TRANSMIT_CODE = 7

RECEIVE_TIMEOUT = 1
'''Timeout for listening to UART for messages'''

ROVER_COMMS_TIMEOUT = 600
'''Timeout for base station waiting for rovers to finish sending all of their data. Default is 10 mins (600s)'''

def create_msg(data, msg_type, ID=None):
    '''
    Returns a packet ready for sending as a bytearray.
    \n The data sent is: `bytearray(msg_type + data)'''
    if msg_type == None:
        return None

    message = bytearray()
    message.append(msg_type)

    if data != None:
        message.append(data)

    if ID != None:
        message.append(ID)

    return message

