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


class SatnogsTools:
    def __init__(self) -> None:
        self.base_url = 'https://db.satnogs.org/api/'
        self.satellites_file = 'satellites.json'
        self.tle_file = 'tle.json'
        self.get_tle()

    def find_tle(self, norad_id: int) -> str:
        with open(self.tle_file, mode='r') as json_file:    # open configuration file
            content = json.load(json_file)                         # load content from configuration file
            for x in content:
                if int(x['tle1'][2:7]) == norad_id:
                    return f'{x['tle1']}\n{x['tle2']}'

    def get_satellites(self) -> dict:
        url = f'{self.base_url}satellites?format=json&in_orbit=true&status=alive'
        dest = self.satellites_file
        if self.download_data(url, dest):
            with open(dest, mode='r') as json_file:  # open configuration file
                content = json.load(json_file)
            for x in content:
                x['tle'] = self.find_tle(x['norad_cat_id'])
            return content

    def get_tle(self) -> None:
        url = f'{self.base_url}tle?format=json'
        dest = self.tle_file
        if self.download_data(url, dest):
            print(f'downloaded TLE data')

    def get_transmitters(self, norad_id: int) -> dict:
        url = f'{self.base_url}transmitters?satellite__norad_cat_id={norad_id}&alive=true&status=active&format=json'
        dest = os.path.join('transmitters', f'{norad_id}-transmitters.json')
        if self.download_data(url, dest):
            with open(dest, mode='r') as json_file:    # open configuration file
                content = json.load(json_file)                         # load content from configuration file
                return content

    @staticmethod
    def download_data(url: str, dest: str) -> bool:
        token = <token>
        if not os.path.dirname(dest) == '':
            os.makedirs(os.path.dirname(dest), exist_ok=True)
        response = requests.get(url, headers={'Authorization': token})
        if response.ok:
            my_json = response.content.decode('utf8')
            data = json.loads(my_json)
            s = json.dumps(data, indent=4)
            with open(dest, 'w') as file:
                file.write(s)
            return True
        else:
            print(f'Cannot download data from {url}: {response.status_code} {response.reason}')
            return False
