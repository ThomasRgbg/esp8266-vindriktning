from machine import Pin, I2C, reset, RTC, unique_id, Timer, WDT, UART
import time

time.sleep(10)

import uasyncio
import gc
import micropython

import bme280_float as bme280
from mqtt_handler import MQTTHandler
from pm25 import PM25

#####
# Schematic/Notes
######

# GPIO3 = UART1 RX

# GPIO0 = SCL to BME280
# GPIO2 = SDA to BME280

#####
# UART and sesor
#####

uart = UART(0, baudrate=9600, rx=Pin(3), tx=Pin(1), timeout=1)
pm25 = PM25(uart)

#####
# I2C and BME280
#####

i2c = I2C(scl=Pin(0), sda=Pin(2), freq=10000)
time.sleep(2)
try:
    bme0 = bme280.BME280(i2c=i2c, mode=bme280.BME280_OSAMPLE_1)
except:
    bme0 = None

def bme_debug():
    print(bme0.values)


#####
# Watchdog
#####

class Watchdog:
    def __init__(self, interval):
        self.timer = Timer(-1)
        self.timer.init(period=(interval*1000), mode=Timer.PERIODIC, callback=self.wdtcheck)
        self.feeded = True
        
    def wdtcheck(self, timer):
        if self.feeded:
            print("Watchdog feeded, all fine")
            self.feeded = False
        else:
            print("Watchdog hungry, lets do a reset in 5 sec")
            time.sleep(5)
            reset()
            
    def feed(self):
        self.feeded = True
        print("Feed Watchdog")

wdt = Watchdog(interval = 120)
wdt.feed()

#####
# Housekeeping
#####

count = 1
errcount = 0

def get_count():
    global count
    return count

def get_errcount():
    global errcount
    return errcount

#####
# MQTT setup
#####

# time to connect WLAN, since marginal reception
time.sleep(5)

sc = MQTTHandler(b'pentling/eg_wohnen_air', '192.168.0.13')
sc.register_publisher('pm25', pm25.get_pm25)
sc.register_publisher('errcount', get_errcount)
sc.register_publisher('count', get_count)

#####
# Task definition
#####

async def housekeeping():
    global errcount
    global count
    while True:
        print("housekeeping() - count {0}, errcount {1}".format(count,errcount))
        wdt.feed()
        gc.collect()
        micropython.mem_info()

        # Too many errors, e.g. could not connect to MQTT
        if errcount > 20:
            reset()

        count += 1

        await uasyncio.sleep_ms(60000)

async def handle_mqtt():
    global errcount
    while True:
        # Generic MQTT
        if sc.isconnected():
#        if True:
            print("handle_mqtt() - connected")
    #            for i in range(29):
    #                sc.mqtt.check_msg()
    #                time.sleep(1)
            sc.publish_all()
        else:
            print("MQTT not connected - try to reconnect")
            sc.connect()
            errcount += 1
            await uasyncio.sleep_ms(19000)

        for i in range(45):
            print(i)
            await uasyncio.sleep_ms(1000)

async def handle_bme():
    global errcount
    while True:
        # Handle temperature/pressure
        print("handle_bme()")
        try:
            if bme0 != None:
                t, p, h = bme0.read_compensated_data()
                d = bme0.dew_point
                if sc.isconnected():
                    sc.publish_generic('temperature', t)
                    sc.publish_generic('pressure', (p/100) + 0.5)   # +0.5 calibration
                    sc.publish_generic('humidity', h)
                    sc.publish_generic('dewpoint', d)
        except:
            errcount += 1
        await uasyncio.sleep_ms(60000)


async def handle_pm25():
    global errcount
    while True:
        print("handle_pm25()")
        try:
            pm25.poll()
        except:
            #errcount += 0.666
            errcount += 0
        await uasyncio.sleep_ms(30000)

####
# Main
####


main_loop = uasyncio.get_event_loop()

main_loop.create_task(housekeeping())
main_loop.create_task(handle_mqtt())
main_loop.create_task(handle_pm25())
main_loop.create_task(handle_bme())

main_loop.run_forever()
main_loop.close()



#def mainloop():
    #global count
    #while True:
        #count += 1
##        pm25.poll()
        #handle_mqtt()
##        handle_bme()
        #housekeeping()
        #time.sleep(1)
        
        
#  mainloop()


