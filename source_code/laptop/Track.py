from beyond.dates import Date                                       # for Date object from beyond library
from beyond.io.tle import Tle                                       # for Tle object from beyond library
from beyond.frames import create_station                            # for station object from beyond library
from datetime import datetime, timedelta                            # for operations with date and time
import numpy as np                                                  # for radian-degree conversion
import paho.mqtt.client as paho                                     # for publishing data on mqtt
import sched                                                        # for scheduling tracking events
import time                                                         # for operations with time (scheduler, sleep...)


class TrackedSatellite:
    def __init__(self, name):
        self.name = name
        self.conf_file = 'configuration.txt'
        self.tle_file = 'tle-active.txt'                            # text file with TLE data
        self.times = []
        self.azims = []
        self.elevs = []
        self.start_time_seconds = 0
        self.delay_before_tracking = timedelta(seconds=30)
        self.print_info('added to tracking')
        self.station = self.create_stat()
        self.tle = self.find_tle()
        self.create_data(delay=0)

    @staticmethod
    def utc():
        return datetime.utcnow()

    @staticmethod
    def read_line_from_txt(filename, line):
        content = open(filename, 'r').readlines()
        return content[line].strip()

    def print_info(self, msg):
        print(self.utc(), 'UTC,', self.name, msg)

    def create_stat(self):                                          # create station object
        return create_station(str(datetime.utcnow()), (float(self.read_line_from_txt(self.conf_file, 0)),
                                                       float(self.read_line_from_txt(self.conf_file, 1)),
                                                       float(self.read_line_from_txt(self.conf_file, 2))))

    def find_tle(self):                                             # create TLE object for a satellite
        with open(self.tle_file, 'r') as file:                      # open TLE text file
            lines = file.readlines()
            for line in lines:
                if line.find(self.name) != -1:
                    line_number = lines.index(line)
                    return Tle(lines[line_number + 1] + lines[line_number + 2])

    def create_data(self, delay):
        self.times.clear()
        self.azims.clear()
        self.elevs.clear()
        for orb in self.station.visibility(self.tle.orbit(), start=Date.now() + timedelta(seconds=delay),
                                           stop=timedelta(hours=24), step=timedelta(seconds=10), events=True):
            self.times.append(datetime.strptime(str(orb.date), '%Y-%m-%dT%H:%M:%S.%f UTC'))
            self.azims.append(float('{azim:7f}'.format(azim=(np.degrees(-orb.theta) % 360))))
            self.elevs.append(float('{elev:7f}'.format(elev=np.degrees(orb.phi))))
            if orb.event and orb.event.info.startswith('LOS'):
                self.start_time = self.times[0]
                self.start_time_seconds = (self.start_time - self.utc() - self.delay_before_tracking).seconds
                if self.start_time_seconds > 0:
                    s.enter(self.start_time_seconds, 1, self.track)
                    self.print_info('created data, AOS: ' + str(self.start_time))
                else:
                    self.create_data(delay=-self.start_time_seconds)
                break

    def track(self):
        if self.start_time > self.utc():
            client = paho.Client()  # create mqtt client
            client.username_pw_set('laptop', password='laptop')  # mqtt server authorization
            if client.connect('raspberrypi', port=1883) == 0:
                print(self.utc(), 'connected to MQTT Broker', sep=', ')
            else:
                print(self.utc(), 'could not connect to MQTT Broker', sep=', ')
            self.print_info('in ' + str((self.start_time - self.utc()).seconds) + ' seconds will fly over your head')
            client.publish('state', 'tracking', 0)
            client.publish('satellite', self.name, 0)
            client.publish('start_azimuth', str(self.azims[0]), 0)
            if self.start_time > self.utc():
                time.sleep((self.start_time - self.utc()).total_seconds())
            self.print_info('tracking started')
            for x in range(len(self.times) - 1):
                delta_t = (self.times[x + 1] - self.times[x]).total_seconds()
                delta_az = self.azims[x + 1] - self.azims[x]
                delta_el = self.elevs[x + 1] - self.elevs[x]
                if delta_az > 180:
                    delta_az -= 360
                if delta_az < -180:
                    delta_az += 360
                client.publish('delta_time', str(delta_t), 0)
                client.publish('delta_azimuth', str(delta_az), 0)
                client.publish('delta_elevation', str(delta_el), 0)
                time.sleep(delta_t)
            client.publish('satellite', '', 0)
            client.publish('state', 'sleep', 0)
            self.print_info('tracking ended')
            client.disconnect()
            print(self.utc(), 'disconnected from MQTT Broker', sep=', ')
            self.create_data(delay=10)
        else:
            self.print_info('tracking passed')
            self.create_data(delay=2000)


if __name__ == '__main__':
    s = sched.scheduler(time.time)                                  # create scheduler object
    f = open('tracked_sats.txt', 'r')
    sats = f.readlines()
    for sat in sats:
        TrackedSatellite(sat.strip())
    s.run()
