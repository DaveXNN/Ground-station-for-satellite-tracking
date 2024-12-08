########################################################################################################################
#                                                                                                                      #
#    Author:         D. Nenicka                                                                                        #
#    Created:        3. 11. 2023                                                                                       #
#    Modified:       19. 10. 2024                                                                                      #
#    Description:    Module for predicting satellite visibility                                                        #
#                                                                                                                      #
########################################################################################################################


from beyond.dates import Date                                       # module with Date object from beyond library
from beyond.io.tle import Tle                                       # module with Tle object from beyond library
from beyond.frames import create_station                            # module with station object from beyond library
from datetime import datetime, timedelta                            # module for operations with date and time
from math import degrees                                            # conversion from radians to degrees


class BeyondTools:                                                  # module for predicting satellite visibility
    def __init__(self, conf: dict) -> None:
        self.tle_file = conf['tle_file']                            # text file with TLE data
        self.station_latitude = conf['station_latitude']            # station latitude
        self.station_longitude = conf['station_longitude']          # station longitude
        self.station_altitude = conf['station_altitude']            # station altitude
        self.min_max_elevation = conf['min_max']                    # minimal MAX elevation of a satellite pass
        self.station = create_station('My station',(self.station_latitude, self.station_longitude, self.station_altitude))
        with open(self.tle_file, 'r') as file:
            self.satellites = sorted(list(map(str.strip, file.readlines()[::3])))
        self.satellites_count = len(self.satellites)                # list of all active satellites in orbit

    @staticmethod
    def dt_set_utc_timezone(dt: datetime) -> datetime:              # return datetime format with UTC timezone
        return datetime.strptime(''.join([str(dt)[:-4], '+00:00']), '%Y-%m-%dT%H:%M:%S.%f%z')

    def get_tle(self, satellite: str) -> Tle:                       # return TLE object for a satellite
        with open(self.tle_file, 'r') as file:
            lines = file.readlines()
            for line in lines:
                if satellite in line:
                    line_number = lines.index(line)
                    return Tle(lines[line_number + 1] + lines[line_number + 2])

    def predict_first_pass(self, satellite: str) -> dict:           # return data about the first pass of a satellite
        data = {'name': satellite}
        ok = False
        ok2 = False
        tle = self.get_tle(satellite)
        for orb in self.station.visibility(tle.orbit(), start=Date.now(), stop=timedelta(days=7), step=timedelta(seconds=50), events=True):
            if orb.event and orb.event.info.startswith('AOS'):
                data['aos_time'] = self.dt_set_utc_timezone(orb.date)
                data['aos_az'] = degrees(-orb.theta) % 360
                ok = True
            if orb.event and orb.event.info.startswith('MAX'):
                data['max_time'] = self.dt_set_utc_timezone(orb.date)
                data['max_az'] = degrees(-orb.theta) % 360
                data['max_el'] = degrees(orb.phi)
                if data['max_el'] > self.min_max_elevation:
                    ok2 = True
                else:
                    ok = False
                    ok2 = False
            if orb.event and orb.event.info.startswith('LOS'):
                data['los_time'] = self.dt_set_utc_timezone(orb.date)
                data['los_az'] = degrees(-orb.theta) % 360
                if ok and ok2:
                    return data

    def create_data(self, satellite: str) -> list:                  # create data for satellite tracking
        data = [[], [], []]
        ok = False
        ok2 = False
        tle = self.get_tle(satellite)
        for orb in self.station.visibility(tle.orbit(), start=Date.now(), stop=timedelta(days=7), step=timedelta(seconds=10), events=True):
            orb_date = self.dt_set_utc_timezone(orb.date)
            azimuth = degrees(-orb.theta) % 360
            elevation = degrees(orb.phi)
            data[0].append(orb_date)
            data[1].append(azimuth)
            data[2].append(elevation)
            if orb.event and orb.event.info.startswith('AOS'):
                ok = True
            if orb.event and orb.event.info.startswith('MAX'):
                if elevation > self.min_max_elevation:
                    ok2 = True
                else:
                    ok = False
                    ok2 = False
            if orb.event and orb.event.info.startswith('LOS'):
                if ok and ok2:
                    return data
                else:
                    data = [[], [], []]
