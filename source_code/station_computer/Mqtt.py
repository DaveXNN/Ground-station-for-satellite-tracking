import paho.mqtt.client as paho                                     # for subscribing data from MQTT broker

from datetime import datetime, timezone
from socket import gaierror
from threading import Timer


class Mqtt:
    def __init__(self):
        self.client = paho.Client()                                 # create mqtt client
        self.client.username_pw_set('laptop', password='laptop')    # mqtt server authorization
        self.connected = False
        self.az = '0.00'
        self.el = '0.00'
        self.enabled = True
        self.try_connect()

    @staticmethod
    def print_info(msg):
        print(f'{datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}, {msg}')

    def try_connect(self):
        try:
            self.client.connect('raspberrypi', port=1883)
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.subscribe('azimuth')
            self.client.subscribe('elevation')
            self.client.loop_start()
        except gaierror:
            self.print_info('laptop could not connect to MQTT Broker')
            if self.enabled:
                self.connect_thread = Timer(30, self.try_connect)
                self.connect_thread.start()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.print_info('laptop connected to MQTT broker')
            self.connected = True
        else:
            self.print_info('laptop could not connect to MQTT broker' + str(rc))
            self.connected = False

    def on_message(self, client, userdata, message):
        topic = str(message.topic)
        msg = float(str(message.payload.decode('utf-8')))
        msg2 = f'{msg:.2f}'
        if topic == 'azimuth':
            self.az = msg2
        if topic == 'elevation':
            self.el = msg2

    def publish_data(self, d_time, d_azimuth, d_elevation):
        self.client.publish('delta_time', str(d_time), 0)
        self.client.publish('delta_azimuth', str(d_azimuth), 0)
        self.client.publish('delta_elevation', str(d_elevation), 0)

    def publish_start_azimuth(self, start_azimuth):
        self.client.publish('start_azimuth', str(start_azimuth), 0)

    def publish_action(self, action):
        self.client.publish('action', action, 0)

    def publish_polarization(self, pol):
        self.client.publish('polarization', pol, 0)
