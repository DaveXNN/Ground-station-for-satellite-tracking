import datetime
import math
import numpy as np
import time
import RPi.GPIO as GPIO
import sched
import signal
import smbus
import sys
import threading
from beyond.dates import Date, timedelta
from beyond.io.tle import Tle
from beyond.frames import create_station
from beyond.config import config

from rotator.rotator import AzimuthStepper, ElevationStepper, Magnetometer   # import tools for stepper motor control and magnetometer compass

station = create_station('TLS', (49.4862398, 18.0405796, 364.0))               # define a ground station
s = sched.scheduler(time.time)

def gpio_init():                                                               # initalization of digital pins
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

def print_notification(notification):
    print(datetime.datetime.utcnow().strftime('%d.%m.%Y   %H:%M:%S UTC'))
    print(notification + "\n")

def utc_epoch_time():                                                          # current epoch utc
    return float(datetime.datetime.utcnow().strftime('%s'))

def epoch_to_datetime(epoch):                                                  # convert epoch time to datetime
    return time.strftime('%H:%M:%S', time.localtime(epoch))

class Satellite():
    def __init__(self, name):
        self.name = name
        self.delay_before_tracking = 60
        self.create_data(wait_for = 0)
        
    def create_data(self, wait_for):                                            # create data for the next pass of the satellite
        self.data = []
        self.wait = wait_for
        self.azims, self.elevs = [], []
        self.rowcount = 0
        with open('tle_hamsat') as file:
            lines = file.readlines()
            for line in lines:
                if line.find(self.name) != -1:
                    line_number = lines.index(line)
                    self.tle = Tle(str(lines[line_number + 1] + lines[line_number + 2])).orbit()
                    file.close()
        for orb in station.visibility(self.tle, start = Date.now() + timedelta(seconds = self.wait), stop = timedelta(hours = 24), step = timedelta(seconds = 10), events = True):
            self.epoch = float(str(datetime.datetime(int("{orb.date:%Y}".format(orb=orb)), int("{orb.date:%m}".format(orb=orb)), int("{orb.date:%d}".format(orb=orb)), int("{orb.date:%H}".format(orb=orb)), int("{orb.date:%M}".format(orb=orb)), int("{orb.date:%S}".format(orb=orb))).strftime('%s')))
            self.elev = np.degrees(orb.phi)
            self.azim = np.degrees(-orb.theta) % 360
            self.azim1 =  float("{azim:7f}".format(azim = self.azim))
            self.elev1 =  float("{elev:7f}".format(elev = self.elev))
            self.data.append([self.epoch, self.azim1, self.elev1])
            self.rowcount = self.rowcount + 1
            if orb.event and orb.event.info.startswith("LOS"):
                break
            if orb.event and orb.event.info.startswith("MAX"):
                self.max_elev = self.elev1
        print_notification("Created data for " + self.name + ".\nNext pass of " + self.name + " will be in " + str(int(self.data[0][0] - utc_epoch_time())) + " seconds (at " + epoch_to_datetime(self.data[0][0]) + " UTC).")
        s.enter(self.data[0][0] - utc_epoch_time() - self.delay_before_tracking, 1, self.track)

    def track(self):                                                            # track satellite when it is visible
        self.start_time = self.data[0][0]
        self.start_azimuth = self.data[0][1]
        self.row_number = 1
        if(self.start_time > utc_epoch_time()):
            print_notification("In " + str(self.delay_before_tracking) + " seconds satellite " + self.name + " will fly over your head.\nHere are some information about the pass:")
            print(self.name.upper() + "\n")
            print("Time start:         " + epoch_to_datetime(self.start_time) + " UTC")
            print("Time end:           " + epoch_to_datetime(self.data[self.rowcount - 1][0]) + " UTC")
            print("Duration:           " + str(int(self.data[self.rowcount - 1][0] -  self.start_time)) + " seconds")
            print("Azimuth start:      " + str(round(self.start_azimuth, 2)) + "*")
            print("Azimuth end:        " + str(round(self.data[self.rowcount - 1][1], 2)) + "*")
            print("Max elevation:      " + str(round(self.max_elev, 2)) + "*\n")
            for x in range(10):
                az.turn_to_azimuth(self.start_azimuth)
            print("Azimuth: " + str(magnetometer.read_azimuth(measurements = 100)) + "*\n")
            if (self.start_time > utc_epoch_time()):
                time.sleep(self.start_time - utc_epoch_time())
            print_notification("Tracking of " + self.name + " just started.")
            while(self.rowcount > self.row_number):
                delta_t = self.data[self.row_number][0] - self.data[self.row_number - 1][0]
                delta_az = self.data[self.row_number][1] - self.data[self.row_number - 1][1]
                delta_el = self.data[self.row_number][2] - self.data[self.row_number - 1][2]
                az.set_speed(duration = delta_t, angle = delta_az)
                el.set_speed(duration = delta_t, angle = delta_el)
                time.sleep(delta_t)
                self.row_number = self.row_number + 1
            print("Azimuth: " + str(magnetometer.read_azimuth(measurements = 100)) + "*\n")
            print_notification("Tracking of "+ self.name + " just ended.")
            self.create_data(wait_for = 10)
        else:
            print_notification("Tracking of " + self.name + " passed.")
            self.create_data(wait_for = 2000) 
        
def track_hamsats():
    with open('tle_hamsat',"r") as file:
        lines = file.readlines()              
        for line in lines[::3]:
            a = Satellite((str(lines[lines.index(line)])).strip())
    file.close()
    s.run()

gpio_init()                             # inicialization of digital pins
magnetometer = Magnetometer()           # inicialization of magnetometer
az = AzimuthStepper()                   # inicialization of azimuth stepper motor
el = ElevationStepper()                 # inicialization of elevation stepper motor             
track_hamsats()
