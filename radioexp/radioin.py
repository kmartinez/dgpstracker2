from pyb import UART

radio = UART(6, 9600)
radio.init(9600, bits=8, parity=None, stop=1, read_buf_len=512)
i = 0

source=5678
msg = b'\x7E\x00\x08\x01\x01\x00\x00\x00\x12\xAB\x12\x2E'

while True:
    print("5678", i, radio.any(), radio.read())
    i = 1 - i
    radio.write(msg)
    pyb.delay(750)
