# Title: gps.py
# brief: forked code from picogps which was modified to read and format nmea messages.
# author: Sherif Attia (sua2g16)
# convert longitude nmea to lon degrees.decimalplaces

def nmealon2lon(l):
    # convert text NMEA lon to degrees.decimalplaces
    if len(l.split('.')[0]) == 4:
        degrees = float(l[0:3])
        decimals = float(l[3:]) / 60
    else:
        degrees = float(l[0:2])
        decimals = float(l[2:]) / 60

    lon = degrees + decimals
    # if f[3] == 'W':
    # 	lon = -lon
    return (lon)


def nmealat2lat(nl):
    # convert text NMEA lat to degrees.decimalplaces
    degrees = float(nl[0:2])
    decimals = float(nl[2:]) / 60.0
    return (degrees + decimals)


def gpsFormatOutput(device_id, data):
    if data.startswith('$GNGGA'):
        # It's positional data
        data = str(data)
        # Why?
        global f
        f = data.split(',')
        gpstime = f[1].split(".")[0]
        lat = f[2]
        lon = f[4]
        E = f[5]
        qual = f[6]
        sats = f[7].lstrip("0")
        hdop = str(int(round(float(f[8]), 0)))
        alt = f[9]
        nmeafix = device_id + "," + lat + "," + lon.strip('0') + "," + alt + "," + sats
        location = (nmealat2lat(lat), nmealon2lon(lon), alt, qual, hdop, sats, nmeafix)
        final_location = (device_id, nmealat2lat(lat), nmealon2lon(lon), alt, qual, hdop, sats, nmeafix)
        #         return 'p', location, nmeafix
        return 'p', final_location


#         return nmeafix


def processGPS(data):
    #     data = data.decode()
    if data.startswith('$GPGGA') or data.startswith('$GNGGA'):
        # It's positional data
        data = str(data)
        # Why?
        global f
        f = data.split(',')
        gpstime = f[1].split(".")[0]
        lat = f[2]
        lon = f[4]
        E = f[5]
        qual = f[6]
        sats = f[7].lstrip("0")
        hdop = str(int(round(float(f[8]), 0)))
        alt = f[9]
        nmeafix = lat + "," + lon.strip('0') + "," + alt + "," + sats
        location = (nmealat2lat(lat), nmealon2lon(lon), alt, qual, hdop, sats, nmeafix)
        return 'p', location

    elif data.startswith('$GPZDA') or data.startswith('$GNZDA'):
        # It's timing data
        # $GPZDA,hhmmss.ss,dd,mm,yyyy,xx,yy*CC
        # ignore decimals seconds, keep 20xx year for our rtc
        data = str(data)
        fields = data.split(",")
        hms = fields[1]
        #	YYYY	MM	DD	hh 	mm	ss
        tod = (fields[4], fields[3], fields[2], hms[0:2], hms[2:4], hms[4:6])
        return "t", tod

    else:
        # No known string detected == probably timeout
        return None, None
