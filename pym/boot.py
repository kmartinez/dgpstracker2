# boot.py -- run on boot-up
# can run arbitrary Python, but best to keep it minimal

import machine
import pym
pym.country('GB') # ISO 3166-1 Alpha-2 code, eg US, GB, DE, AU
#pym.main('main.py') # main script to run after this one
#pym.usb_mode('VCP+MSC') # act as a serial and a storage device
#pym.usb_mode('VCP+HID') # act as a serial device and a mouse
