########################################################################################################################
#                                                                                                                      #
#    Author:         D. Nenicka                                                                                        #
#    Created:        3. 11. 2023                                                                                       #
#    Modified:       30. 8. 2024                                                                                       #
#    Description:    Module for downloading TLE data                                                                   #
#                                                                                                                      #
########################################################################################################################


from datetime import datetime, timedelta, timezone                  # module for operations with date and time
from threading import Timer                                         # module for running more processes in parallel

import json                                                         # module for working with json files
import requests                                                     # module for downloading


class TleUpdator:
    def __init__(self, configuration_file):
        self.configuration_file = configuration_file
        with open(self.configuration_file) as json_file:            # open configuration file
            conf = json.load(json_file)                             # load content of configuration file
            self.tle_file = conf['tle_file']                        # text file with TLE data
            self.tle_source = conf['tle_source']                    # source of TLE data
            self.last_update = datetime.strptime(conf['last_tle_update'], '%Y-%m-%d %H:%M:%S.%f%z')  # TLE update
            self.update_period = timedelta(hours=conf['tle_update_period'])     # TLE data update period
        update_time = datetime.now(timezone.utc) - self.last_update
        if update_time > self.update_period:
            self.update_tle()
        else:
            self.update_thread = Timer(update_time.total_seconds(), self.update_tle)
            self.update_thread.start()

    def update_tle(self):                                           # update tle data (if it is older than 2 hours)
        try:
            response = requests.get(self.tle_source)
            if response.ok:
                self.last_update = datetime.now(timezone.utc)
                with open(self.tle_file, 'wb') as f:
                    f.write(response.content)
                with open(self.configuration_file, 'r') as g:
                    content = json.load(g)
                    content['last_tle_update'] = str(self.last_update)
                with open(self.configuration_file, 'w') as h:
                    json.dump(content, h, indent=4)
        except requests.exceptions.ConnectionError:
            pass
        self.update_thread = Timer(self.update_period.total_seconds(), self.update_tle)
        self.update_thread.start()
