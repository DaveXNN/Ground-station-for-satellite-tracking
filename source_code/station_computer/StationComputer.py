########################################################################################################################
#                                                                                                                      #
#    Author:         D. Nenicka                                                                                        #
#    Created:        3. 11. 2023                                                                                       #
#    Modified:       19. 10. 2024                                                                                      #
#    Description:    The main script of Satellite Tracking Software                                                    #
#                                                                                                                      #
########################################################################################################################


from JsonTools import JsonTools                                     # module for operations with json files
from TleUpdator import TleUpdator                                   # module for downloading TLE data
from TrackingTool import TrackingTool                               # Satellite Tracking Software GUI


def main():
    json_tool = JsonTools('configuration.json')                     # module for working with json configuration file
    tle_updator = TleUpdator(json_tool)                             # module for regular TLE data updating
    TrackingTool(json_tool, tle_updator)                            # GUI initialization


if __name__ == '__main__':
    main()
