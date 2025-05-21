########################################################################################################################
#                                                                                                                      #
#    Author:         D. Nenicka                                                                                        #
#    Created:        3. 11. 2023                                                                                       #
#    Modified:       19. 10. 2024                                                                                      #
#    Description:    Module for communicating with MQTT broker                                                         #
#                                                                                                                      #
########################################################################################################################


import paho.mqtt.client as paho                                     # module for subscribing data from MQTT broker
from threading import Thread                                        # module for running more processes in parallel


class Mqtt:                                                         # module for communicating with MQTT broker
    def __init__(self) -> None:
        self.client = paho.Client()                                 # create mqtt client
        self.client.username_pw_set('station_computer', password='station_computer')    # mqtt broker authorization
        self.connected = False                                      # connection indicator
        self.az = '0.00'                                            # rotator azimuth
        self.el = '0.00'                                            # rotator elevation
        self.connect_thread = Thread(target=self.try_connect, args=(lambda: self.stop_thread, ))
        self.connect_thread.start()
        self.stop_thread = False

    def try_connect(self, stop_thread) -> None:                                  # try to establish a connection with MQTT broker
        while not self.client.is_connected():
            try:
                self.client.connect('192.168.15.119', port=1883, keepalive=5)
                self.client.on_connect = self.on_connect
                self.client.on_message = self.on_message
                self.client.subscribe('azimuth')
                self.client.subscribe('elevation')
                self.client.loop_start()
            except (TimeoutError, OSError):
                pass
            if stop_thread:
                break

    def on_connect(self, client, userdata, flags, rc) -> None:      # executed when connection is established
        if rc == 0:
            print('connected to MQTT broker')
            self.connected = True
        else:
            print(f'could not connect to MQTT broker, code {rc}')
            self.connected = False

    def on_message(self, client, userdata, message) -> None:        # executed when a message is sent
        topic = str(message.topic)
        msg = str(message.payload.decode('utf-8'))
        if topic == 'azimuth':
            self.az = f'{float(msg):.2f}'
        if topic == 'elevation':
            self.el = f'{float(msg):.2f}'

    def publish_position(self, time: float, azimuth: float, elevation: float) -> None:    # publish data for satellite tracking
        data_string = f'{time} {azimuth} {elevation}'
        self.client.publish('position', data_string, 2)

    def publish_aos_data(self, start_azimuth: float) -> None:    # publish AOS azimuth
        self.client.publish('aos_data', str(start_azimuth), 2)

    def publish_offset(self, offset_name: str, offset: float) -> None:  # publish offset
        self.client.publish(offset_name, str(offset), 2)

    def publish_polarization(self, pol: str) -> None:               # publish antenna polarization
        self.client.publish('polarization', pol, 2)

    def publish_action(self, action: str) -> None:                  # publish action
        self.client.publish('action', action, 2)
