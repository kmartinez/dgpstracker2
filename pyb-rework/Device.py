ERROR_CODE = False

class Device:
    def __init__(self, device_ID):
        # Device Data
        self.device_ID = device_ID # DEVICE ID, -1 = Base, 0,1,2 = Rover

    # ALL COMMS SPECIFIES WICH DEVICE IS AT THE OTHER END BY INCLUDING DEVICE ID IN THE MESSAGES
    def configure_radio(self):
        print("CONFIGURING RADIO")

    def configure_GPS(self):
        print("CONFIGURING GPS")

    # GET NMEA DATA FROM GPS USING RTCM3 DATA
    def GPS_get_NMEA(self):
        self.NMEA = None
        print("GETTING NMEA DATA")

    # GET THE RTCM3 DATA FROM THE GPS AND STORE
    def GPS_get_rtcm3(self):
        self.rtcm3 = None
        print("GETTING RTCM3 DATA")

    # SET THE RTCM3 OF THE GPS READY TO GET NMEA DATA
    def GPS_set_RTCM3(self,rtcm3_data):
        print("SETTING CORRECTION DATA")
        
    # SEND REQUEST TO SEND
    def send_RTS(self):
        print("SENDING RTS")

    # SEND CLEAR TO SEND
    def send_CTS(self):
        print("SENDING CTS")

    # SEND ACKNOWLEDGEMENT
    def send_ACK(self):
        print("SENDING ACK")

    # SEND RAW RTCM3 DATA
    def send_RTCM3(self):
        print("SENDING RTCM3")

    # SEND RAW NMEA DATA
    def send_NMEA(self):
        print("SENDING NMEA")

    # WAIT FOR A REQUEST TO SEND
    def rec_RTS(self):
        print("RECEIVING RTS")

    # WAIT FOR CLEAR TO SEND
    def rec_CTS(self):
        print("RECEIVING CTS")

    # WAIT FOR ACK TO BE RECEIVED
    def rec_ACK(self):
        print("RECEIVING ACK")

    # WAIT FOR RTCM3 TO BE RECEIVED AND PROCESS IT
    def rec_rtcm3(self):
        print("RECEIVING rtcm3")

    # WAIT FOR NMEA TO BE RECEIVED AND PROCESS IT
    def rec_NMEA(self):
        print("RECEIVING NMEA")
        # Change return value based on if NMEA is valid/correct
        return False

    def shutdown(self):
        # SHUTDOWN SCRIPT USING RTC I2C STUFF



