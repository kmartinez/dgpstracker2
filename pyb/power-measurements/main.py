# simple http get over wifi
# adapted from https://circuitpython.readthedocs.io/projects/imageload/en/latest/examples.html?highlight=requests#requests-test

"""WiFi modules"""
import ssl
import wifi
import socketpool
import adafruit_requests as requests
"""Vanilla modules"""
import time
import board
import digitalio
import analogio

"""External lib modules"""
from adafruit_ahtx0 import AHTx0
from adafruit_debouncer import Debouncer
from adafruit_ina219 import INA219, ADCResolution, BusVoltageRange

# Global variables  
""" Make sure bootloader is updated to the latest version - current version is 7.3.3 """
i2c = board.STEMMA_I2C()
aht = AHTx0(i2c)
ina219 = INA219(i2c)
ina219_2 = INA219(i2c)

# PIN DEFINITION
""" Switch GPIO PIN"""
pin_io12 = digitalio.DigitalInOut(board.IO12)
# pin_io12.pull = digitalio.Pull.UP
pin_io12.direction = digitalio.Direction.INPUT

FILE_PATH = "Readings/incoming_data.txt"

is_logging = False
""" LED GPIO PIN """
LED = digitalio.DigitalInOut(board.LED)
LED.direction = digitalio.Direction.OUTPUT

# Get wifi secrets
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets in secrets.py, add them there!")
    raise

wifi.radio.connect(secrets["ssid"], secrets["password"])

print("My IP address is", wifi.radio.ipv4_address)

socket = socketpool.SocketPool(wifi.radio)
https = requests.Session(socket, ssl.create_default_context())

# pylint: disable=line-too-long
url = "http://iotgate.ecs.soton.ac.uk/test/test.txt"
URL_POST = "http://iotgate.ecs.soton.ac.uk/myapp"


# Debouncer function
def debouncable(pin):
    switch_io = digitalio.DigitalInOut(pin)
    switch_io.direction = digitalio.Direction.INPUT
    switch_io.pull = digitalio.Pull.UP
    return switch_io

# External Button
button_d12 = Debouncer(debouncable(board.D5))

# TODO: read mearuments
# - temperature & humidity
def measure_temperature_and_humidity():
    print("Measuring Temperature from AHT")
    while True:
        print("\nTemperature: %0.1f C" % aht.temperature)
        print("\nHumidity: %0.1f %%" % aht.relative_humidity)
        time.sleep(2)

# - current
def measure_current():
    print("Measuring Current\n")
    # display some of the advanced field (just to test)
    print("Config register:")
    print("  bus_voltage_range:    0x%1X" % ina219.bus_voltage_range)
    print("  gain:                 0x%1X" % ina219.gain)
    print("  bus_adc_resolution:   0x%1X" % ina219.bus_adc_resolution)
    print("  shunt_adc_resolution: 0x%1X" % ina219.shunt_adc_resolution)
    print("  mode:                 0x%1X" % ina219.mode)
    print("")

    # optional : change configuration to use 32 samples averaging for both bus voltage and shunt voltage
    ina219.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
    ina219.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
    # optional : change voltage range to 16V
    ina219.bus_voltage_range = BusVoltageRange.RANGE_16V

    ina219_2.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
    ina219_2.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
    # optional : change voltage range to 16V
    ina219_2.bus_voltage_range = BusVoltageRange.RANGE_16V

    

    # measure and display loop
    while True:
        bus_voltage = ina219.bus_voltage  # voltage on V- (load side)
        shunt_voltage = ina219.shunt_voltage  # voltage between V+ and V- across the shunt
        current = ina219.current  # current in mA
        power = ina219.power  # power in watts
        total_voltage = (ina219_2.shunt_voltage + ina219_2.bus_voltage)

    
        if current <= 0:
            pin_io12.direction = digitalio.Direction.OUTPUT
            # pin_io12.value = False
            break
        # INA219 measure bus voltage on the load side. So PSU voltage = bus_voltage + shunt_voltage
        else:
            print("=" * 40)
            print("Voltage (VIN+) : {:6.3f}   V".format(bus_voltage + shunt_voltage))
            print("Voltage (VIN-) : {:6.3f}   V".format(bus_voltage))
            print("Shunt Voltage  : {:8.5f} V".format(shunt_voltage))
            print("Shunt Current  : {:7.4f}  A".format(current / 1000))
            print("Power Calc.    : {:8.5f} W".format(bus_voltage * (current / 1000)))
            print("Power Register : {:6.3f}   W".format(power))
            print("Voltage: : {:6.3f}   V".format(total_voltage+bus_voltage))
            print("")
            print("=" * 40)
            print("\nMeasuring Temperature from AHT")
            print("\nTemperature: %0.1f C" % aht.temperature)
            print("\nHumidity: %0.1f %%" % aht.relative_humidity)
            print("=" * 60)
    

        # Check internal calculations haven't overflowed (doesn't detect ADC overflows)
        if ina219.overflow:
            print("Internal Math Overflow Detected!")
            print("")

        time.sleep(2)
# - Counter/Timer since the start 


# - Data Logger too
# - replace button D12 with IO12
def data_logger():
    button_flag = True
    logging = False

    while True:
        """ Filesystem main loop that effectively needs boot.py to be present to be able to write data into incoming data.txt
            General Operation currently runs a simple timestamp - not accurate but acts as a template to be fixed
            Currently relies on a push-button on pin D12 with an LED to interface with - flash once a second and it's working; 0.5s and it's not working
            NB: To work properly, please make sure that boot.py is present on the board. It will force the board into read-only mode and can only be changed on the REPL.
            To make changes to the code, please change the name of boot.py to something else like boost.py using os.rename on the REPL.
            Final Notes: Any changes in your code requires you to reset the board so that it enters Read-Only mode, and vice-versa.
        """
        button_d12.update()
        if button_d12.fell:
            print("Pressed")
            print("Writing to Filesystem")
            # onboard_counter() # internal function callback doesn't work - need to find a solution around this
            # count = 0 - redundant
            try:
                print("Ready to Log...")
                while button_flag:
                    button_d12.update()
                    if button_d12.fell:
                        print("Button Pressed")     
                        print(button_d12.fell)
                        button_flag = False
                print("Logging...")
                is_logging = True
                with open(FILE_PATH, "w") as fp:
                    fp.write("Timestamp\tLongitude\tLatitude\tFix Quality\n")
                    # correct timestamp using RTC
                    # timestamp = "{}/{}/{} {:02}:{:02}:{:02}".format(ds3231.datetime.tm_year,ds3231.datetime.tm_mon, ds3231.datetime.tm_mday, ds3231.datetime.tm_hour, ds3231.datetime.tm_min, ds3231.datetime.tm_sec )
                    # print("{}".format(timestamp))
                    # print(timestamp)
                    initial_time = time.monotonic()
                    initial_t = initial_time
                    latitude = 52.3951  # to be read from gps
                    longitude = 1.3452  # to be read from gps
                    quality_fix = 4     # to be read form gps
                    while is_logging:
                        sec_time = time.monotonic()
                        if (sec_time - initial_time) >= 1:
                            time_stamp = sec_time - initial_t   # may want to use datetime from RTC
                            sec_time = 0
                            initial_time = time.monotonic()
                            #   Writes time-stamp   \t  Longitude   \t  Latitude    \t  Fix Quality
                            # fp.write("{}/{}/{} {:02}:{:02}:{:02}".format(ds3231.datetime.tm_year,ds3231.datetime.tm_mon, ds3231.datetime.tm_mday, ds3231.datetime.tm_hour, ds3231.datetime.tm_min, ds3231.datetime.tm_sec ) + "\t"
                            print( "{}".format(longitude) + "\t"
                            +  "{}".format(latitude) + "\t"
                            +  "{}".format(quality_fix) + "\n" )
                            fp.flush()
                            LED.value = not LED.value
                            # print(time_stamp)
                            # print("{}/{}/{} {:02}:{:02}:{:02}".format(ds3231.datetime.tm_year,ds3231.datetime.tm_mon, ds3231.datetime.tm_mday, ds3231.datetime.tm_hour, ds3231.datetime.tm_min, ds3231.datetime.tm_sec ) + "\t" 
                            print("{}".format(longitude) + "\t" 
                            + "{}".format(latitude) + "\t"
                            + "{}".format(quality_fix) + "\n")
                        button_d12.update()
                        if button_d12.fell:
                            is_logging = False
                            print("Stopped Logging")
                        
            except OSError as e:  # Typically when the filesystem isn't writeable...
                delay = 0.5  # ...blink the LED every half second.
                if e.args[0] == 28:  # If the file system is full...
                    delay = 0.25  # ...blink the LED faster!
                while True:
                    if is_logging:
                        LED.value = not LED.value
                        time.sleep(delay)
            LED.value = True
            time.sleep(0.5)
        else:
            LED.value = False



# add try-catch on the request
# deprecated, works if you include json=<insert-content-here>
""" Disabled posting data """
# message = "Content-Sherif"
# json_data = [{"Date": "20/01/2023"},{"Field": "Glacsweb-test"}]
# print("Posting to server")
# message_post =https.post(url=URL_POST, json=message)
# print("POST Complete")
# print(message_post.content)

# message_post.close()


def main():
    print("Testing New System\n")
    pin_io12.pull = digitalio.Pull.UP
    # set a flag 
    print(pin_io12.value)
    # pin_io12.direction =digitalio.Direction.OUTPUT

    """ Check if PIN Valid """
    if pin_io12.value:
        print("Ready to Log data")
        data_logger()
    else:
        print("PIN not active.")
    # data_logger()
    # pin_io12.value = True
    # while pin_io12.value:
    #     try:
    #         measure_current()# - main
    #         # measure_temperature()
    #         # # measure_voltage()
    #         # # measure_temperature_and_humidity()
            
    #         time.sleep(1)
    #     except OSError:
    #         print("retry reads")


if __name__ == '__main__':
    main()
    
