import json


class JsonTools:
    def __init__(self, json_file):
        self.configuration_file = json_file
        with open(self.configuration_file) as json_file:  # open configuration file
            self.content = json.load(json_file)  # load content of configuration file

    def overwrite_variable(self, variable, value):
        self.content[variable] = value
        with open(self.configuration_file, 'w') as h:
            json_string = json.dumps(self.content, indent=4)
            h.write(json_string)
