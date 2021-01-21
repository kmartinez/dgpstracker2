from pyb import *
from pym.Formats import U2
import datetime
import struct

from pym.Radio import *

radio = RadioConn(b'\x00\x00', uartAddr=6, baudrate=9600, timeout=2000)
rConn = radio.radioConn

dt=datetime.datetime # use RTC class?

def getTimeStr():
    h = str(dt.hour)
    m = str(dt.minute)
    s = str(dt.second)
    n = str(dt.microsecond)
    return h+m+s+n

def constructPacket(length):
    bs = bytearray()
    for i in range(length):
        bs.extend(b'\xAB')

    return radio.getPacket(b'\x56\x78', getTimeStr()).extend(bs)

# write packet
for i in range(1, 256):
    rConn.write(constructPacket(i))
    pyb.delay(500)

# read packet
while True:
    # loop until start delim found
    inp = rConn.read(1)
    while inp != b'7E' and inp != b'~':
        inp = rConn.read(1)

    length = U2(rConn.read(2))
    pl = rConn.read(length)

    if pl is not None:
        print(datetime.datetime.now(), "->", pl[3:-1][])


# from pyb import RTC
# while True:
#     print(rtc.datetime())
#     pyb.delay(250)