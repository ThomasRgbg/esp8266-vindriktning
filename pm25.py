import time

 
class PM25:
    def __init__(self, uart):
        self.uart=uart
        self.pm25 = 0
    
    def get_pm25(self):
        return self.pm25
    
    def poll(self):
        raw_data = self.uart.read(16)
#        print(raw_data)
        # time.sleep(0.5)
        # Empty buffer
        # self.uart.read(40)
        if len(raw_data) == 15 and raw_data[0] == 0x16 and raw_data[1] == 0x11:
            pm25 = 256 * raw_data[5] + raw_data[6]
            print("Particles pm25 {0} ug/m^3".format(pm25))
#            pm1 = 256 * raw_data[9] + raw_data[10]
#            print("Particles pm1.0 {0} ug/m^3".format(pm1))
#            pm10 = 256 * raw_data[9] + raw_data[10]
#            print("Particles pm10 {0} ug/m^3".format(pm10))


            self.pm25 = pm25
