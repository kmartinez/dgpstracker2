# get our Wifi MAC address (for registering)
# put ssid and pass in your secrets.py
# uncomment the testwifi() to check it works

import wifi
def formatmac(mac):
    smac = ""
    for ot in list(mac):
        h = hex(ot)
        smac += h[2] + h[3]
    return(smac)



def testwifi():
    # Get wifi secrets
    try:
        from secrets import secrets
        print("connecting to ",secrets["ssid"] )
        wifi.radio.connect(secrets["ssid"], secrets["password"])
        print("My IP address is", wifi.radio.ipv4_address)
    except ImportError:
        print("WiFi secrets needed in secrets.py, add them there")
        raise


mac = wifi.radio.mac_address
# print(mac)
smac = formatmac(mac)
print("MAC: ", smac)
# uncomment once you have put things in secrets.py
testwifi()