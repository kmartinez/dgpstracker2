
# import time

# def main():
#     count = 0
#     while True:
#         print(count)
#         count += 1
#         time.sleep(1)

# import wifi
# def formatmac(mac):
#     smac = ""
#     for ot in list(mac):
#         h = hex(ot)
#         smac += h[2] + h[3]
#     return(smac)



# def testwifi():
#     # Get wifi secrets
#     try:
#         from secrets import secrets
#         print("connecting to ",secrets["ssid"] )
#         wifi.radio.connect(secrets["ssid"], secrets["password"])
#         print("My IP address is", wifi.radio.ipv4_address)
#     except ImportError:
#         print("WiFi secrets needed in secrets.py, add them there")
#         raise


# def main():
#     mac = wifi.radio.mac_address
#     smac = formatmac(mac)
#     print("MAC: ", smac)

import board
import busio
import digitalio
import time
from adafruit_ina219 import ADCResolution, BusVoltageRange, INA219
from adafruit_ahtx0 import AHTx0

# i2c = board.STEMMA_I2C()
i2c = board.I2C()
ina219 = INA219(i2c,addr=0x40)
aht20 = AHTx0(i2c)

# Additional Readings from MCU apparently
VOLTAGE_DIFF = 2.2


def read_measurements():
    print("Bus Voltage:   {} V".format(ina219.bus_voltage))
    print("Shunt Voltage: {} mV".format(ina219.shunt_voltage / 1000))
    print("Current:       {} mA".format(ina219.current))


def read_current_measurements():
    print("ina219 test")

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

    # measure and display loop
    while True:
        bus_voltage = ina219.bus_voltage - VOLTAGE_DIFF  # voltage on V- (load side)
        shunt_voltage = ina219.shunt_voltage  # voltage between V+ and V- across the shunt
        current = ina219.current  # current in mA
        power = ina219.power  # power in watts
        print("="*40)
        # INA219 measure bus voltage on the load side. So PSU voltage = bus_voltage + shunt_voltage
        print("Voltage (VIN+) : {:6.3f}   V".format((bus_voltage + shunt_voltage)))
        print("Voltage (VIN-) : {:6.3f}   V".format(bus_voltage))
        print("Shunt Voltage  : {:8.5f} V".format(shunt_voltage))
        print("Shunt Current  : {:7.4f}  A".format(current / 1000))
        print("Power Calc.    : {:8.5f} W".format(bus_voltage * (current / 1000)))
        print("Power Register : {:6.3f}   W".format(power))
        print("")

        # Check internal calculations haven't overflowed (doesn't detect ADC overflows)
        if ina219.overflow:
            print("Internal Math Overflow Detected!")
            print("")

        time.sleep(2)


def main():
    while True:
        
        # read_measurements()
        read_current_measurements()
        time.sleep(1)
    # while not i2c.try_lock():
    #     pass

    # try:
    #     while True:
    #         print(
    #             "I2C addresses found:",
    #             [hex(device_address) for device_address in i2c.scan()],
    #         )
    #         time.sleep(2)

    # finally:  # unlock the i2c bus when ctrl-c'ing out of the loop
    #     i2c.unlock()


if __name__ == '__main__':
    main()
    