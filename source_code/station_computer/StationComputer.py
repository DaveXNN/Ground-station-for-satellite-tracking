########################################################################################################################
#                                                                                                                      #
#    Author:         D. Nenicka                                                                                        #
#    Created:        3. 11. 2023                                                                                       #
#    Modified:       30. 8. 2024                                                                                       #
#    Description:    The main script of Satellite Tracking Software                                                    #
#                                                                                                                      #
########################################################################################################################


from JsonTools import JsonTools                                 # module for operations with json files
from TleUpdator import TleUpdator                               # module for downloading TLE data
from TrackingTool import TrackingTool                           # Satellite Tracking Software GUI


if __name__ == '__main__':
    json_tool = JsonTools('configuration.json')                 # module for working with json configuration file
    tle_updator = TleUpdator(json_tool)                         # module for regular TLE data updating
    app = TrackingTool(json_tool, tle_updator)                  # GUI initialization
    app.mainloop()