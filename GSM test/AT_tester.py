# main.py -- put your code here!
import pyb
# from ina219 import DeviceRangeError
# from ina219 import INA219
from pyb import Pin
from machine import I2C
from machine import UART

y1_pin = pyb.Pin.board.Y1
y2_pin = pyb.Pin.board.Y2

g = pyb.Pin(y1_pin, mode=Pin.OUT_PP, pull=Pin.PULL_NONE)
# z = pyb.Pin(y2_pin,mode=Pin.OUT_PP,pull=Pin.PULL_NONE)

# z.value(1)
# pyb.delay(1000)
# print(z.value())
# z.value(0)
# pyb.delay(2000)
# print(z.value())
# z.value(1)
# pyb.delay(1000)
# print(z.value())

g.value(0)
pyb.delay(2000)
print(g.value())
g.value(1)
pyb.delay(1000)
print(g.value())



# g = pyb.Pin(y1_pin,Pin.IN,Pin.PULL_UP)


#print(g.value())
# g.value(1)
# pyb.delay(1000)
# print(g.value())

def send_command(comm):
    if comm not in command_dict:
        print('Invalid Command')
        return
    if comm in http_set:

    else:
        print('Sent {} '.format(command_dict[comm]))
        uart.write(command_dict[comm])
        return

def process_command(*args):



command_dict = {
"status":"AT",
"id":"ATI",
"signal":"AT+CSQ",
"echo_on":"ATE1",
"echo_off":"ATE0",
"re_exec":"A/",
"set_url":process_command("set_url"),


}

http_set = {"set_url"}


uart = UART(2,57600)
uart.init(57600, bits=8, parity=None, stop=1)#, flow = uart.RTS | uart.CTS)
count=0
# uart.write('AT')

while True:
    while(uart.any==0):
        uart.write('AT')
        count+=1
        print(count)
        pyb.delay(50)
    if(uart.any()>0):
        msg = uart.read()
        print(msg)
        command = input("Send next AT command")
        uart.write(command)
 #    else:
#         uart.write('AT')
#         count+=1
#         print(count)
#         pyb.delay(10000)


############################################
############################################
######### Set up GSM3 Click for HTTP########
############################################

# Steps:
# 1. ATE0 disables echo
# 1. AT+CGDCONT= 1,"IP","TM","0.0.0.0",0,0
# 3. AT+CGACT = 1
# 1. Set APN to "TM" with AT+CSTT="TM"
# 2. Set bearer to gprs and set its apn to "TM" with:
# AT+SAPBR=3,1,"CONTYPE","GPRS"
# AT+SAPBR=3,1,"APN","TM"
# AT+SAPBR=1,1
# AT+CSTT="TM", AT+CIICR, AT+CIFSR
# AT+HTTPINIT
# AT+HTTPPARA = "CID",1
# AT+HTTPPARA="URL","https://iotgate.ecs.soton.ac.uk/myapp"
# AT+HTTPDATA=8,20000 8 chars, 20s to type
# input here
# AT+HTTPACTION=1 for POST, 0 for GET
# AT+HTTPTERM


# ptsv2.com : toilet is 
