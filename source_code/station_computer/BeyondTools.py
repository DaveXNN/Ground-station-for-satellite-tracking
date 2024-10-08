########################################################################################################################
#                                                                                                                      #
#    Author:         D. Nenicka                                                                                        #
#    Created:        3. 11. 2023                                                                                       #
#    Modified:       30. 8. 2024                                                                                       #
#    Description:    Module for predicting satellite visibility                                                        #
#                                                                                                                      #
########################################################################################################################


from beyond.dates import Date                                       # module with Date object from beyond library
from beyond.io.tle import Tle                                       # module with Tle object from beyond library
from beyond.frames import create_station                            # module with station object from beyond library
from datetime import datetime, timedelta                            # module for operations with date and time
from math import degrees                                            # conversion from radians to degrees


class BeyondTools:
    def __init__(self, conf):
        self.tle_file = conf['tle_file']                        # text file with TLE data
        self.station_latitude = conf['station_latitude']        # station latitude
        self.station_longitude = conf['station_longitude']      # station longitude
        self.station_altitude = conf['station_altitude']        # station altitude
        self.min_max_elevation = conf['min_max']                # minimal MAX elevation of a satellite pass
        self.station = create_station('My station',(self.station_latitude, self.station_longitude, self.station_altitude))
        with open(self.tle_file, 'r') as file:
            self.satellites = sorted(list(map(str.strip, file.readlines()[::3])))
        self.satellites_count = len(self.satellites)

    def get_tle(self, satellite):                                   # return TLE object for a satellite
        with open(self.tle_file, 'r') as file:                      # open TLE text file
            lines = file.readlines()
            for line in lines:
                if satellite in line:
                    line_number = lines.index(line)
                    return Tle(lines[line_number + 1] + lines[line_number + 2])

    def predict_first_pass(self, satellite):
        aos_time = None
        max_time = None
        aos_az = 0
        max_az = 0
        max_el = 0
        ok = False
        tle = self.get_tle(satellite)
        for orb in self.station.visibility(tle.orbit(), start=Date.now(), stop=timedelta(days=7), step=timedelta(seconds=50), events=True):
            if orb.event and orb.event.info.startswith('AOS'):
                aos_time = datetime.strptime(''.join([str(orb.date)[:-4], '+00:00']), '%Y-%m-%dT%H:%M:%S.%f%z')
                aos_az = degrees(-orb.theta) % 360
                ok = True
            if orb.event and orb.event.info.startswith('MAX'):
                max_time = datetime.strptime(''.join([str(orb.date)[:-4], '+00:00']), '%Y-%m-%dT%H:%M:%S.%f%z')
                max_az = degrees(-orb.theta) % 360
                max_el = degrees(orb.phi)
            if orb.event and orb.event.info.startswith('LOS'):
                los_time = datetime.strptime(''.join([str(orb.date)[:-4], '+00:00']), '%Y-%m-%dT%H:%M:%S.%f%z')
                los_az = degrees(-orb.theta) % 360
                if ok:
                    return aos_time, max_time, los_time, aos_az, max_az, los_az, max_el

    def create_data(self, satellite, init_delay=0):
        aos_time = None
        max_time = None
        aos_az = 0
        max_az = 0
        max_el = 0
        times = []
        azims = []
        elevs = []
        ok = False
        ok2 = False
        tle = self.get_tle(satellite)
        for orb in self.station.visibility(tle.orbit(), start=Date.now() + timedelta(hours=init_delay), stop=timedelta(days=7), step=timedelta(seconds=10), events=True):
            orb_date = datetime.strptime(''.join([str(orb.date)[:-4], '+00:00']), '%Y-%m-%dT%H:%M:%S.%f%z')
            azimuth = degrees(-orb.theta) % 360
            elevation = degrees(orb.phi)
            times.append(orb_date)
            azims.append(azimuth)
            elevs.append(elevation)
            if orb.event and orb.event.info.startswith('AOS'):
                aos_time = orb_date
                aos_az = azimuth
                ok = True
            if orb.event and orb.event.info.startswith('MAX'):
                max_time = orb_date
                max_az = azimuth
                max_el = elevation
                if max_el > self.min_max_elevation:
                    ok2 = True
                else:
                    ok = False
                    ok2 = False
            if orb.event and orb.event.info.startswith('LOS'):
                los_time = orb_date
                los_az = azimuth
                if ok and ok2:
                    return times, azims, elevs, aos_time, max_time, los_time, aos_az, max_az, los_az, max_el
