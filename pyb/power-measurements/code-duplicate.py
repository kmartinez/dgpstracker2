# Title: main.py - FEATHER (RECEIVER)
# Author: Sherif Attia
# Date: 08/11/2022


from board import UART
import board
import busio
import time
import digitalio

# Counters
EXPECTED = 0
MISSING = 0

uart = busio.UART(board.TX, board.RX, baudrate=115200, timeout=10)
LED = digitalio.DigitalInOut(board.LED)
LED.direction = digitalio.Direction.OUTPUT


def counter_ACK(self, count):
        # count += 1
    # data = uart.read(10).decode()
    # delimiter = uart.read(1)
    # if delimiter is not None:
    #     if delimiter == b'0x7E':

    data = uart.read(10)

    # print(data)
    LED.value = True
    if data is not None:
        LED.value = True
        time.sleep(1)
        print(data)
        if data == count:
            EXPECTED += 1
            count +=1
        else:
            MISSING += 1

        # convert bytearray to string
        # data_string = int(''.join([chr(b) for b in data]))
        # print(data_string, end="")

        LED.value = False
        time.sleep(1)
        print("EXPECTED: ",EXPECTED, " MISSING: ", MISSING)
    # else:
    #     print("nothing in buffer")
    #     continue
        # if uart.readline() is None:
    #     continue
    # if uart.readline() > 0:
    #     print("Incoming message")
    #     LED.value = True
    #     print(uart.readline().decode())
    #     time.sleep(1)

print("Ready to receive messages")
count = 1

def commChecK():
        if uart.read(11) is not None:
            data = uart.read(64)
        print(type(data))
        # print(data.decode())
        if int(data) % 2 == 0:
            print("receiving")
        # print(data[1])
        # if str(uart.read(10)).decode() == "acknowledge":
        #     print("received")
        # time.sleep(1)

while True:

    # data = uart.read(11)

    # # print(data)
    # LED.value = True
    # if data is not None:
    #     LED.value = True
    #     time.sleep(1)
    #     print(data)
    #     if data == count:
    #     # if data % 2 == 0:
    #         EXPECTED += 1
    #         count +=1
    #     else:
    #         MISSING += 1

    #     LED.value = False
    #     time.sleep(1)
    #     print("EXPECTED: ",EXPECTED, " MISSING: ", MISSING)



    final_message = str(count)
    data = bytearray(final_message + "\n")
    print(data)

    LED.value = True

    uart.write(data)
    # print("Successfully sent")
    print("sent")
#     time.sleep(1)

    LED.value = False
    count += 1
