# main.py -- put your code here!
import pyb
# from ina219 import DeviceRangeError
# from ina219 import INA219
from pyb import Pin
from machine import I2C
from machine import UART

y1_pin = pyb.Pin.board.Y1
y2_pin = pyb.Pin.board.Y2

g = pyb.Pin(y1_pin, mode=Pin.OUT_PP, pull=Pin.PULL_UP)
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

# g.value(0)
# pyb.delay(2000)
# print(g.value())
g.value(1)
pyb.delay(1000)
print(g.value())



# g = pyb.Pin(y1_pin,Pin.IN,Pin.PULL_UP)


#print(g.value())
# g.value(1)
# pyb.delay(1000)
# print(g.value())

# def send_command(comm):
#     if comm not in command_dict:
#         print('Invalid Command')
#         return
#     if comm in http_set:

#     else:
#         print('Sent {} '.format(command_dict[comm]))
#         uart.write(command_dict[comm])
#         return

#def process_command(*args):

##

## Need to define buf sizes? Timeouts?

def http_send(arg):   #*args):
    
    uart.write('ATE0\r\n')
    print('ATE0')
    pyb.delay(200)
    if(uart.any()):
        resp = uart.read().decode()
        print(resp)
    
    uart.write('AT+CGDCONT= 1,"IP","TM","0.0.0.0",0,0\r\n')
    print('AT+CGDCONT= 1,"IP","TM","0.0.0.0",0,0')
    pyb.delay(1000)
    
    if(uart.any()):
        resp = uart.read().decode()
        print(resp)
    
    uart.write('AT+CGACT = 1\r\n')
    print("AT+CGACT = 1")
    pyb.delay(1000)
    
    if(uart.any()):
        resp = uart.read().decode()
        print(resp)
    
    uart.write('AT+CSTT="TM"\r\n')
    print('AT+CSTT="TM"')
    pyb.delay(1000)
    
    if(uart.any()):
        resp = uart.read().decode()
        print(resp)
        
    uart.write('AT+CIICR\r\n')
    
    print('AT+CIICR')
    pyb.delay(1000)
    
    if(uart.any()):
        resp = uart.read().decode()
        print(resp)
    
    uart.write('AT+CIFSR\r\n')
    print('AT+CIFSR')
    pyb.delay(1000)
    
    if(uart.any()):
        resp = uart.read().decode()
        print(resp)
        
    uart.write('AT+SAPBR=3,1,"CONTYPE","GPRS"\r\n')
    print('AT+SAPBR=3,1,"CONTYPE","GPRS"')
    
    pyb.delay(1000)
    
    if(uart.any()):
        resp = uart.read().decode()
        print(resp)
    
    uart.write('AT+SAPBR=3,1,"APN","TM"\r\n')
    print('AT+SAPBR=3,1,"APN","TM"')
    
    pyb.delay(1000)
    
    if(uart.any()):
        resp = uart.read().decode()
        print(resp)
        
    uart.write('AT+SAPBR=1,1\r\n')
    print('AT+SAPBR=1,1')
    
    pyb.delay(1000)
    if(uart.any()):
        resp = uart.read().decode()
        print(resp)
    
    uart.write('AT+HTTPINIT\r\n')
    print('AT+HTTPINIT')
    pyb.delay(200)
    
    if(uart.any()):
        resp = uart.read().decode()
        print(resp)
        
    uart.write('AT+HTTPPARA = "CID",1\r\n')
    print('AT+HTTPPARA = "CID",1')
    pyb.delay(200)
    
    if(uart.any()):
        resp = uart.read().decode()
        print(resp)
    
    # uart.write('AT+HTTPPARA = "CID",1\r\n')
#     pyb.delay(200)
    
#     if(uart.any()):
#         resp = uart.read().decode()
#         print(resp)
        
    uart.write('AT+HTTPPARA="URL","http://ptsv2.com/t/6qgvg-1661366726/post"\r\n')
    print('AT+HTTPPARA="URL","http://ptsv2.com/t/6qgvg-1661366726/post"')
    pyb.delay(200)
    
    if(uart.any()):
        resp = uart.read().decode()
        print(resp)

    uart.write('AT+HTTPDATA='+str(len(arg))+',20000\r\n')
    print('AT+HTTPDATA='+str(len(arg))+', 20000')
    
    pyb.delay(200)
    
    # if(uart.any()):
        # resp = uart.read()
        # print(resp)
    
    try:
        resp = uart.read().decode()
        print(resp)
    except:
        print('Nothing to read')
        pyb.delay(200)
        resp = uart.read().decode()
        print(resp)
    finally:
        if(resp[:12]=='\r\nDOWNLOAD\r\n'):
            print("Download detected!")
            uart.write(arg+'\r\n')
            pyb.delay(500)
            
    if(uart.any()):
        resp = uart.read().decode()
        print(resp)
        
    uart.write('AT+HTTPACTION=1\r\n')
    print('AT+HTTPACTION=1')
    
    pyb.delay(2000)
    
    if(uart.any()):
        resp = uart.read().decode()
        print(resp)
        
    uart.write('AT+HTTPTERM\r\n')
    print('AT+HTTPTERM')
    pyb.delay(2000)
    
    if(uart.any()):
        resp = uart.read().decode()
        print(resp)
        
    uart.write('AT+SAPBR=0,1\r\n')
    print('AT+SAPBR=0,1')
    pyb.delay(2000)
    
    if(uart.any()):
        resp = uart.read().decode()
        print(resp)
        
    uart.write('AT+CPOWD=1\r\n')
    print('AT+CPOWD=1')
    
    pyb.delay(500)   
    if(uart.any()):
        resp = uart.read().decode()
        print(resp) 
     
    return 
        
# command_dict = {
# "status":"AT",
# "id":"ATI",
# "signal":"AT+CSQ",
# "echo_on":"ATE1",
# "echo_off":"ATE0",
# "re_exec":"A/",
# "set_url":process_command("set_url"),


# }

# http_set = {"set_url"}


uart = UART(2,57600)
uart.init(57600, bits=8, parity=None, stop=1)#, flow = uart.RTS | uart.CTS)
count=0
# uart.write('AT')

#while True:
   #  while(uart.any==0):
#         uart.write('AT')
#         count+=1
#         print(count)
#         pyb.delay(50)

#     if(uart.any()>0):
#         msg = uart.read().decode()
#         print(msg)

uart.write("AT\r\n")
pyb.delay(200)
        
if(uart.any()>0):
    msg = uart.read().decode()
    print(msg)
    # if(msg=="\r\nOK\r\n"):
#         print("hi")
#         http_send("Glacsbay")
        
while True:        
    command = input("Send next AT command\r\n")
    uart.write(command+"\r\n")
    pyb.delay(300)
    if(uart.any()>0):
        msg = uart.read().decode()
        print(msg)
        
        
        
#         command = input("Send next AT command")
#        uart.write(command)
 #    else:
#         uart.write('AT')
#         count+=1
#         print(count)
#         pyb.delay(10000)

    #if(uart.any()==0):
        


#####################################################################
#####################################################################
############## Set up GSM3 Click for HTTP############################
#####################################################################
#
# The PWK pin can be held high by either 3V3 or a GPIO pin
#
#
# Steps:
# 1. ATE0 disables echo
# 2. AT&W
# 3. AT+CGDCONT= 1,"IP","TM","0.0.0.0",0,0
# 4. AT+CGACT = 1
# 5. Set APN to "TM" with AT+CSTT="TM"
##   AT+CSTT="TM"
##   AT+CIICR 
##   AT+CIFSR
# 6. Set bearer to gprs and set its apn to "TM" with:
### AT+SAPBR=3,1,"CONTYPE","GPRS"
### AT+SAPBR=3,1,"APN","TM"
### AT+SAPBR=1,1
# AT+HTTPINIT
# AT+HTTPPARA = "CID",1
# AT+HTTPPARA="URL","https://iotgate.ecs.soton.ac.uk/myapp"
# AT+HTTPDATA=8,20000 8 chars, 20s to type
# input here
# AT+HTTPACTION=1 for POST, 0 for GET
# AT+HTTPTERM
# AT+CPOWD 


# ptsv2.com : toilet is http://ptsv2.com/t/6qgvg-1661366726/post
# AT+HTTPPARA="URL","http://ptsv2.com/t/6qgvg-1661366726/post"
