########################################################################################################################
#                                                                                                                      #
#    Author:         D. Nenicka                                                                                        #
#    Created:        3. 11. 2023                                                                                       #
#    Modified:       30. 8. 2024                                                                                       #
#    Description:    The main script of Satellite Tracking Software                                                    #
#                                                                                                                      #
########################################################################################################################


from BeyondTools import BeyondTools                             # module for predicting satellite visibility
from JsonTools import JsonTools                                 # module for operations with json files
from Mqtt import Mqtt                                           # module for MQTT communication
from TleUpdator import TleUpdator                               # module for downloading TLE data
from TrackingTool import TrackingTool                           # Satellite Tracking Software GUI


configuration_file = 'configuration.json'                       # configuration json file


if __name__ == '__main__':
    configuration = JsonTools(configuration_file)
    tle_updator = TleUpdator(configuration)
    beyond_tools = BeyondTools(configuration.content)
    mqtt = Mqtt()
    app = TrackingTool(configuration, beyond_tools, mqtt, tle_updator)
    app.mainloop()