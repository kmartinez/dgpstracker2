import Device

class Rover(Device):
    def __init__(self, device_ID):
        super().__init__(device_ID)
        self.rtcm3 = None
        self.NMEA = None
        self.parsed_NMEA = None

    def send_rover_data(self):
        RTCM3_correct = False
        print("RECEIVING ROVER DATA")

        self.send_RTS()
        self.rec_ACK()
        self.send_CTS()
        self.rec_RTCM3()
        self.GPS_set_RTCM3()
        self.GPS_get_NMEA()
        self.send_NMEA()
        self.rec_ACK()