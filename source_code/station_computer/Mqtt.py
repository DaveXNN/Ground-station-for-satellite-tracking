########################################################################################################################
#                                                                                                                      #
#    Author:         D. Nenicka                                                                                        #
#    Created:        3. 11. 2023                                                                                       #
#    Modified:       19. 10. 2024                                                                                      #
#    Description:    Module for communicating with MQTT broker                                                         #
#                                                                                                                      #
########################################################################################################################


import paho.mqtt.client as paho                                     # module for subscribing data from MQTT broker

from datetime import datetime, timezone                             # module for operations with date and time
from socket import gaierror                                         # module for avoiding connection errors
from threading import Timer                                         # module for running more processes in parallel


class Mqtt:                                                         # module for communicating with MQTT broker
    def __init__(self) -> None:
        self.client = paho.Client()                                 # create mqtt client
        self.client.username_pw_set('laptop', password='laptop')    # mqtt broker authorization
        self.connected = False                                      # connection indicator
        self.az = '0.00'                                            # rotator azimuth
        self.el = '0.00'                                            # rotator elevation
        self.connect_thread = None                                  # thread for connecting to MQTT broker
        self.try_connect()                                          # function that tries to establish a connection with MQTT broker

    @staticmethod
    def print_info(msg) -> None:                                    # print message with timestamp
        print(f'{datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}, {msg}')

    def try_connect(self) -> None:                                  # try to establish a connection with MQTT broker
        try:
            self.client.connect('raspberrypi', port=1883)
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.subscribe('azimuth')
            self.client.subscribe('elevation')
            self.client.loop_start()
        except gaierror:
            self.connected = False
            self.print_info('laptop could not connect to MQTT Broker')
            self.connect_thread = Timer(30, self.try_connect)
            self.connect_thread.start()

    def on_connect(self, client, userdata, flags, rc) -> None:      # executed when connection is established
        if rc == 0:
            self.print_info('laptop connected to MQTT broker')
            self.connected = True
        else:
            self.print_info(f'laptop could not connect to MQTT broker, code {rc}')
            self.connected = False

    def on_message(self, client, userdata, message) -> None:        # executed when a message is sent
        topic = str(message.topic)
        msg = float(str(message.payload.decode('utf-8')))
        msg2 = f'{msg:.2f}'
        if topic == 'azimuth':
            self.az = msg2
        if topic == 'elevation':
            self.el = msg2

    def publish_data(self, d_time: float, d_azimuth: float, d_elevation: float) -> None:    # publish data for satellite tracking
        self.client.publish('delta_time', str(d_time), 0)
        self.client.publish('delta_azimuth', str(d_azimuth), 0)
        self.client.publish('delta_elevation', str(d_elevation), 0)

    def publish_aos_azimuth(self, start_azimuth: float) -> None:    # publish AOS azimuth
        self.client.publish('start_azimuth', str(start_azimuth), 0)

    def publish_offset(self, offset_name: str, offset: float) -> None:  # publish offset
        self.client.publish(offset_name, str(offset), 0)

    def publish_polarization(self, pol: str) -> None:               # publish antenna polarization
        self.client.publish('polarization', pol, 0)

    def publish_action(self, action: str) -> None:                  # publish action
        self.client.publish('action', action, 0)
