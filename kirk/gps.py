# GPS functions
#$GPGGA,hhmmss.ss,llll.ll,a,yyyyy.yy,a,x,xx,x.x,x.x,M,x.x,M,x.x,xxxx*hh
#1    = UTC of Position
#2    = Latitude
#3    = N or S
#4    = Longitude
#5    = E or W (negate if W)
#6    = GPS quality indicator (0=invalid; 1=GPS fix; 2=Diff. GPS fix)
#7    = Number of satellites in use [not those in view]
#8    = Horizontal dilution of position
#9    = Antenna altitude above/below mean sea level (geoid)
#10   = Meters  (Antenna height unit)
#11   = Geoidal separation (Diff. between WGS-84 earth ellipsoid and
#       mean sea level.  -=geoid is below WGS-84 ellipsoid)
#12   = Meters  (Units of geoidal separation)
#13   = Age in seconds since last update from diff. reference station
#14   = Diff. reference station ID#
#15   = Checksum
from common import d
def nmealon2lon( l):
    # convert text NMEA lon to degrees.decimalplaces
    degrees = float(l[0:3])
    decimals = float(l[3:])/60
    lon = degrees + decimals
    return(lon)

def nmealat2lat( nl):
    # convert text NMEA lat to degrees.decimalplaces
    degrees = float(nl[0:2])
    decimals = float(nl[2:])/60.0
    return(degrees + decimals)

f = None

#$GPGGA,171505.00,5057.22111,N,00138.48355,W,1,11,0.98,85.1,M,47.3,M,,*77\r\n
def processGPS(data):
    if data.startswith( '$GPGGA' ) :
        d("position")
        d(data)
        global f
        f =  data.split(',')            
        if( f[6] == '0' or f[2] == None or f[5] == None or f[7] == None or f[9] == None):
            d('...')
            return None, None
        lat = nmealat2lat(f[2])
        lon = nmealon2lon(f[4])
        E = f[5]
        if( E == 'W'):
            lon = -lon
        sats = f[7].lstrip('0')
        alt = float(f[9])
        location = (lat,lon, alt, sats )
        return 'p', location
           
    elif data.startswith( '$GPZDA' ) or data.startswith('$GNZDA') :
        # It's timing data
        # $GPZDA,hhmmss.ss,dd,mm,yyyy,xx,yy*CC
        # ignore decimals seconds, keep 20xx year for our rtc
        data = str(data)    
        fields = data.split(",")
        hms = fields[1]
        #    YYYY    MM    DD    hh     mm    ss
        tod = (fields[4], fields[3], fields[2], hms[0:2], hms[2:4], hms[4:6])    
        return "t", tod

    else:
        #No known string detected == probably timeout
        return None, None
