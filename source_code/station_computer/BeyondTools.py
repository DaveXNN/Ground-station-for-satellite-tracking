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
    prediction_step = timedelta(seconds=5)
    def __init__(self, conf: dict) -> None:
        self.station_latitude = conf['station_latitude']            # station latitude
        self.station_longitude = conf['station_longitude']          # station longitude
        self.station_altitude = conf['station_altitude']            # station altitude
        self.min_max_elevation = conf['min_max']                    # minimal MAX elevation of a satellite pass
        self.station = create_station('My station',(self.station_latitude, self.station_longitude, self.station_altitude))
        self.max_pred_time = timedelta(days=3)

    @staticmethod
    def dt_set_utc_timezone(dt: datetime) -> datetime:              # return datetime format with UTC timezone
        return datetime.strptime(f'{dt}+00:00', '%Y-%m-%dT%H:%M:%S.%f UTC%z')

    def predict_first_pass(self, tle1: str) -> dict:                # return data about the first pass of a satellite
        data = dict()
        ok = False
        ok2 = False
        tle = Tle(tle1)
        for orb in self.station.visibility(tle.orbit(), start=Date.now(), stop=self.max_pred_time, step=timedelta(seconds=10), events=True):
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
        return {}

    def create_data(self, tle1: str, delay: float) -> tuple:                       # create data for satellite tracking
        data = list()
        prediction = dict()
        ok = False
        ok2 = False
        tle = Tle(tle1)
        for orb in self.station.visibility(tle.orbit(), start=Date.now() + timedelta(hours=delay), stop=self.max_pred_time, step=self.prediction_step, events=True):
            orb_date = self.dt_set_utc_timezone(orb.date)
            azimuth = degrees(-orb.theta) % 360
            elevation = degrees(orb.phi)
            data.append((orb_date, azimuth, elevation, orb.r))
            if orb.event and orb.event.info.startswith('AOS'):
                prediction['aos_time'] = orb_date
                prediction['aos_az'] = azimuth
                ok = True
            if orb.event and orb.event.info.startswith('MAX'):
                if elevation > self.min_max_elevation:
                    ok2 = True
                    prediction['max_time'] = orb_date
                    prediction['max_az'] = azimuth
                    prediction['max_el'] = elevation
                else:
                    ok = False
                    ok2 = False
            if orb.event and orb.event.info.startswith('LOS'):
                if ok and ok2:
                    prediction['los_az'] = azimuth
                    prediction['los_time'] = orb_date
                    return data, prediction
                else:
                    data.clear()
        return [], {}
