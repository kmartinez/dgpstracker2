# convert longitude nmea to lon degrees.decimalplaces

FIX_QUALITY = 2
RTK_FIX = 4
RTK_FLOAT = 5
WEEKDAY = 0

def nmealon2lon(l):
    # convert text NMEA lon to degrees.decimalplaces
    if len(l.split('.')[0]) == 5:
        degrees = float(l[0:3])
        decimals = float(l[3:]) / 60
    else:
        degrees = float(l[0:2])
        decimals = float(l[2:]) / 60

    lon = degrees + decimals
    # why was this commented out?
    if f[5] == 'W':
        lon = -lon
#     print('{0:.8f}'.format(lon))
#     return (lon)
    return ('{0:.7f}'.format(lon))


def nmealat2lat(nl):
    # convert text NMEA lat to degrees.decimalplaces
    degrees = float(nl[0:2])
    decimals = float(nl[2:]) / 60.0

    lat = degrees + decimals
    if f[3] == 'S':
        lat = -lat

    return ('{0:.7f}'.format(lat))


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
#         print(qual)   - prints 4!
        # check fix quality is equal to 0, 1 or 2 (or 5 if supported)
#         if qual == FIX_QUALITY:
            # pass
#         print(type(qual))
#         Reference: support.dewesoft.com/en/support/solutoins/articles/14000108531-explanation-of-gps-fix-quality-values
        if int(qual) == RTK_FIX:
#             print("Fix Type: {}", qual)
            print("=" * 40)
            nmeafix = device_id + "," + lat + "," + lon.strip('0') + "," + alt + "," + sats
            location = (nmealat2lat(lat), nmealon2lon(lon), alt, qual, hdop, sats, nmeafix)
            final_location = (device_id, nmealat2lat(lat), nmealon2lon(lon), alt, qual, hdop, sats, nmeafix)
        #         return 'p', location, nmeafix
            return 'p', final_location
    #         return nmeafix
    # Changed elif to 'if' to consider the time mode as well, which returns the format needed to write onto the rtc.
    if data.startswith('$GNZDA'):
        # It's timing data
        # $GPZDA,hhmmss.ss,dd,mm,yyyy,xx,yy*CC
        # ignore decimals seconds, keep 20xx year for our rtc
        data = str(data)
        fields = data.split(",")
        hms = fields[1]
        #   device_ID YYYY  MM  DD WEEKDAY  hh  mm  ss ms
        # Temporary removal of device_ID
        tod = (int(fields[4]), int(fields[3]), int(fields[2]), int(WEEKDAY), int(hms[0:2]), int(hms[2:4]), int(hms[4:6]), int(hms[7:]))
        return "t", tod
    else:
        return None, None


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
        #   YYYY    MM  DD  hh  mm  ss
        # 8-tuple has the following format: year, month, day, weekday, hours, minutes, seconds, subseconds

        tod = (fields[4], fields[3], fields[2], hms[0:2], hms[2:4], hms[4:6])
        return "t", tod

    else:
        # No known string detected == probably timeout
        return None, None


