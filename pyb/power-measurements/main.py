import v_bat
import digitalio
import analogio
import board 
import time

""" external lib modules """
# from adafruit_lc709203f import LC709203F - deprecated
from adafruit_ahtx0 import AHTx0
from adafruit_mcp9808 import MCP9808
from adafruit_ina219 import INA219, ADCResolution, BusVoltageRange


#TODO: identify current sensor to use
#TODO: figure out how to measure VBAT
#TODO: measure and log VBAT
#TODO: Track measurements with a timer too (RTC)
i2c = board.STEMMA_I2C() # TODO: make sure bootloader is updated to the latest version - current version is 7.3.3
# i2c_mcp = board.STEMMA_I2C(18)   
# lc7 = LC709203F(i2c)
aht = AHTx0(i2c)
# mcp = MCP9808(i2c)
ina219 = INA219(i2c)

pin_io12 = digitalio.DigitalInOut(board.IO12)
# pin_io12.pull =digitalio.Pull.UP
pin_io12.direction = digitalio.Direction.INPUT

# DEPRECATED Need to use measure current instead, though for some reason, vs code doesn't recognise the driver, or .mpy files or outdated?
# def measure_voltage():
#     """Measures the voltage reading coming from the FeatherS2 as it is regulated across the 
#        LC709203 module as it
#     """
#     print("Measuring Voltage\n")
#     print("IC Version: ", hex(lc7.ic_version))
#     print("Battery Voltage: %0.3f V" % (lc7.cell_voltage))
#     print("Battery Percentage: %0.1f %% " % (lc7.cell_percent))
#     print("Battery Pack Size: ", (lc7.pack_size))

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

    

    # measure and display loop
    while True:
        bus_voltage = ina219.bus_voltage  # voltage on V- (load side)
        shunt_voltage = ina219.shunt_voltage  # voltage between V+ and V- across the shunt
        current = ina219.current  # current in mA
        power = ina219.power  # power in watts

    
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

def measure_temperature():
    print("Measure Temperature from MCP")
    while True:
        print("\nTemperature: %0.3f C"% mcp.temperature)
        time.sleep(2)
    
def measure_temperature_and_humidity():
    print("Measuring Temperature from AHT")
    while True:
        print("\nTemperature: %0.1f C" % aht.temperature)
        print("\nHumidity: %0.1f %%" % aht.relative_humidity)
        time.sleep(2)


def main():
    print("Testing New System\n")
    
    # pin_io12.direction =digitalio.Direction.OUTPUT
    # pin_io12.pull = digitalio.Pull.UP
    # set a flag 
    print(pin_io12.value)
    # pin_io12.value = True
    while pin_io12.value:
        try:
            measure_current()
            # measure_temperature()
            # # measure_voltage()
            # # measure_temperature_and_humidity()
            
            time.sleep(1)
        except OSError:
            print("retry reads")

if __name__ == '__main__':
    main()
    