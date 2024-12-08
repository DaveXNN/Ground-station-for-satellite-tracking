########################################################################################################################
#                                                                                                                      #
#    Author:         D. Nenicka                                                                                        #
#    Created:        3. 11. 2023                                                                                       #
#    Modified:       19. 10. 2024                                                                                      #
#    Description:    Module for downloading TLE data                                                                   #
#                                                                                                                      #
########################################################################################################################


from datetime import datetime, timedelta, timezone                  # module for operations with date and time
from threading import Timer                                         # module for running more processes in parallel

import requests                                                     # module for downloading


class TleUpdator:                                                   # module for downloading TLE data
    def __init__(self, conf) -> None:
        self.json_tool = conf
        self.tle_file = conf.content['tle_file']                    # text file with TLE data
        self.tle_source = conf.content['tle_source']                # source of TLE data
        self.last_update = datetime.strptime(conf.content['last_tle_update'], '%Y-%m-%d %H:%M:%S.%f%z')  # time of the last TLE update
        self.update_period = timedelta(hours=conf.content['tle_update_period'])                                 # TLE data update period
        update_time = datetime.now(timezone.utc) - self.last_update # remaining time to TLE update
        self.update_thread = None
        if update_time > self.update_period:                        # update TLE if it is too old
            self.update_tle()
        else:
            self.update_thread = Timer(update_time.total_seconds(), self.update_tle)
            self.update_thread.start()

    def update_tle(self) -> None:                                   # update tle data (when the current version is older than 2 hours)
        try:
            response = requests.get(self.tle_source)
            if response.ok:
                self.last_update = datetime.now(timezone.utc)
                with open(self.tle_file, 'wb') as f:
                    f.write(response.content)
                self.json_tool.overwrite_variable('last_tle_update', str(self.last_update))
        except requests.exceptions.ConnectionError:
            pass
        self.update_thread = Timer(self.update_period.total_seconds(), self.update_tle)
        self.update_thread.start()
