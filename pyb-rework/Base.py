import Device

class Base(Device):
    def __init__(self, device_ID):
        super().__init__(device_ID)
        self.rover_rec = [False,False,False] # DENOTES WHICH ROVERS HAVE ALREADY BEEN COMMUNICATED WITH
        self.current_rover_ID = None # DENOTES CURRENT ROVER BEING COMMUNICATED WITH

    def receive_rover_data(self):
        NMEA_correct = False
        print("RECEIVING ROVER DATA")

        # Repeat until all rovers have sent their data
        while all(self.rover_rec) == False:

            self.rec_RTS()
            self.send_ACK()
            self.rec_CTS()

            while  NMEA_correct == ERROR_CODE:
                self.send_RTCM3()
                NMEA_correct = self.rec_NMEA()

            self.send_ACK()

            # Set data sent flag for current rover to True
            self.rover_rec[self.current_rover_ID] = True

