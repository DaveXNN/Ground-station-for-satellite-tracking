########################################################################################################################
#                                                                                                                      #
#    Author:         D. Nenicka                                                                                        #
#    Created:        3. 11. 2023                                                                                       #
#    Modified:       14. 4. 2025                                                                                       #
#    Description:    Module for downloading data from Satnogs API                                                      #
#                                                                                                                      #
########################################################################################################################


import json
import os
import requests
from requests.exceptions import ConnectionError


class Satellite:
    def __init__(self, name, norad_id) -> None:
        self.name = name
        self.norad_id = norad_id
        self.prediction = dict()


class SatnogsTools:
    def __init__(self) -> None:
        self.base_url = 'https://db.satnogs.org/api/'
        self.tle_file = 'tle.json'
        self.satellites_file = 'satellites.json'
        self.tle = list()
        self.get_tle()

    def find_tle(self, norad_id: int) -> str:
        for x in self.tle:
            if int(x['tle1'][2:7]) == norad_id:
                return f'{x['tle1']}\n{x['tle2']}'

    def get_satellites(self) -> list:
        url = f'{self.base_url}satellites?format=json&in_orbit=true&status=alive'
        content = self.download_data(url, self.satellites_file)
        satlist = []
        for x in content:
            if x['norad_cat_id'] is not None:
                satlist.append(Satellite(x['name'], x['norad_cat_id']))
        return satlist

    def get_tle(self) -> None:
        url = f'{self.base_url}tle?format=json'
        self.tle = self.download_data(url, self.tle_file)

    def get_transmitters(self, norad_id: int) -> list:
        url = f'{self.base_url}transmitters?satellite__norad_cat_id={norad_id}&alive=true&status=active&format=json'
        return self.download_data(url, f'{norad_id}-transmitters.json')

    def download_data(self, url: str, dest: str) -> list:
        token = '07bc865b3087fd70b6ebd19051ff2a286dc8348f'
        dest2 = os.path.join('downloads', dest)
        try:
            response = requests.get(url, headers={'Authorization': token})
            if response.ok:
                content = json.loads(response.content.decode('utf8'))
                self.save_json(dest2, content)
                return content
            else:
                return self.load_json(dest2)
        except ConnectionError:
            return self.load_json(dest2)

    @staticmethod
    def save_json(filename: str, content) -> None:
        with open(filename, 'w') as json_file:
            json_string = json.dumps(content, indent=4)
            json_file.write(json_string)

    @staticmethod
    def load_json(filename: str):
        if os.path.isfile(filename):
            with open(filename, 'r') as json_file:
                return json.load(json_file)
        else:
            return []
