
# from machine import deepsleep
# from machine import RTC
# from machine import UART
# import machine
import pyb
import time
import lcd160cr 
import logging
# from ina219 import INA219
# from ina219 import DeviceRangeError
from machine import I2C
#import lcd160cr_test

# I2C_INTERFACE_NO = 2
# SHUNT_OHMS = 0.1  # Check value of shunt used with your INA219
# MAX_EXPECTED_AMPS = 0.3

# voltage1 = 0.0
# current1 = 0.0

sleep_time = 7
work_time = 5

def callback(arg):
    print("Called back")
    return 

#ina = INA219(SHUNT_OHMS, I2C(I2C_INTERFACE_NO))
#ina.configure()
# ina.configure(ina.RANGE_16V)
# ina = INA219(SHUNT_OHMS, I2C(2), MAX_EXPECTED_AMPS, address=0x44)

# def read():
    # global voltage1, current1
    # ina = INA219(SHUNT_OHMS,I2C(I2C_INTERFACE_NO), address=0x44)
    # ina.configure(ina.RANGE_16V)
    # #print("Hi")

    # try:
        # #voltage1 = ina.voltage()+ina.shunt_voltage()
        # voltage1 = ina.voltage()#+ina.shunt_voltage()
        # current1 = ina.current()
        # print('Device input voltage: {0:.2f}\n'.format(voltage1))
        # print('Device input current: {0:.2f}\n\n'.format(current1))
        # #return voltage, current
        # # print("Bus Current: %.3f mA" % ina.current())
# #         print("Power: %.3f mW" % ina.power())
# #         print("Shunt voltage: %.3f mV" % ina.shunt_voltage())
    # except DeviceRangeError as e:
        # # Current out of device range with specified shunt resister
        # print (e)
    
lcd = lcd160cr.LCD160CR('X')
#lcd = lcd160cr.LCD160CR('X')
buf = ""
lcd.set_font(1)
lcd.set_pos(90, 0)
#lcd.screen_dump(buf, x=0, y=0, w=None, h=None)

rtc = pyb.RTC()
rtc.datetime((2014, 5, 1, 4, 13, 0, 0, 0))
counter1 = work_time
counter2 = sleep_time
while True:
    #read()
    lcd.erase()
    for counter1 in range(work_time,0,-1):
        lcd.erase()
        lcd.write("Waiting for {0} seconds".format(counter1))
        py.delay(1000)
    
    #pyb.delay(5000)
    lcd.set_pos(0,0)
    lcd.write("Going to sleep for {0} seconds".format(sleep_time))
    rtc.wakeup(sleep_time*1000,callback)
    pyb.stop()
    # lcd.write('voltage: {0:.2f}\n'.format(voltage1))
    # lcd.set_pos(0,100)
    # lcd.write('current: {0:.2f}\n'.format(current1))
    
    
if __name__ == "__main__":
    read()

# lcd.write('Hello world!\n')
# lcd.set_pen(lcd.rgb(255, 0, 0), lcd.rgb(64, 64, 128))
# lcd.set_text_color(lcd.rgb(255, 0, 0), lcd.rgb(0, 0, 0))
# lcd.erase()
#lcd.line(10, 10, 50, 80)
# lcd.write('Hello world!\n')

#test_all('X')
#lcd.test_all('X')

# led = pyb.LED(2)
# while True:
#     led.toggle()
#     pyb.delay(1000)
    
