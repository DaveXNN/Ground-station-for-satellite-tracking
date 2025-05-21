########################################################################################################################
#                                                                                                                      #
#    Author:         D. Nenicka                                                                                        #
#    Created:        3. 11. 2023                                                                                       #
#    Modified:       19. 10. 2024                                                                                      #
#    Description:    Module for operations with json files                                                             #
#                                                                                                                      #
########################################################################################################################


import json                                                         # module for working with json files


class JsonTools:                                                    # module for operations with json files
    def __init__(self, conf_file: str) -> None:
        self.configuration_file = conf_file                         # configuration file path
        with open(self.configuration_file, 'r') as json_file:            # open configuration file
            self.content = json.load(json_file)                     # load content from configuration file

    def overwrite_variable(self, variable, value) -> None:          # overwrite a variable in json configuration file
        self.content[variable] = value
        with open(self.configuration_file, 'w') as json_file:
            json_string = json.dumps(self.content, indent=4)
            json_file.write(json_string)
