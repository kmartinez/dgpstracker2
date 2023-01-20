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
from adafruit_ina219 import INA219, ADCResolution, BusVoltageRange

# Global variables  
""" Make sure bootloader is updated to the latest version - current version is 7.3.3 """
i2c = board.STEMMA_I2C()
aht = AHTx0(i2c)
ina219 = INA219(i2c)
ina219_2 = INA219(i2c)

# PIN DEFINITION
pin_io12 = digitalio.DigitalInOut(board.IO12)
# pin_io12.pull = digitalio.Pull.UP
pin_io12.direction = digitalio.Direction.INPUT


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


# deprecated, works if you include json=<insert-content-here>
message = "Content-Sherif"
json_data = [{"Date": "20/01/2023"},{"Field": "Glacsweb-test"}]
print("Posting to server")
message_post =https.post(url=URL_POST, json=message)
print("POST Complete")
print(message_post.content)

message_post.close()


def main():
    pass


if __name__ == '__main__':
    main()
    
