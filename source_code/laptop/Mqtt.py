import paho.mqtt.client as paho                                     # for subscribing data from MQTT broker

from datetime import datetime
from threading import Thread, Timer


def print_info(msg):
    print('{0} UTC, {1}'.format(datetime.utcnow(), msg))


class Mqtt:
    def __init__(self):
        self.client = paho.Client()                                 # create mqtt client
        self.client.username_pw_set('laptop', password='laptop')    # mqtt server authorization
        self.azimuth = '0.00'
        self.elevation = '0.00'
        Thread(target=self.try_connect).start()

    def try_connect(self):
        try:
            self.client.connect('raspberrypi', port=1883)
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.subscribe('azimuth')
            self.client.subscribe('elevation')
            self.client.loop_start()
        except:
            print_info('laptop could not connect to MQTT Broker')
            Timer(60, self.try_connect).start()

    @staticmethod
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print_info('laptop connected to MQTT broker')
        else:
            print_info('laptop could not connect to MQTT broker' + str(rc))

    def on_message(self, client, userdata, message):
        topic = str(message.topic)
        msg = str(round(float(str(message.payload.decode('utf-8'))), 2))
        if topic == 'azimuth':
            self.azimuth = msg
        if topic == 'elevation':
            self.elevation = msg

    def publish_data(self, d_time, d_azimuth, d_elevation):
        self.client.publish('delta_time', str(d_time), 0)
        self.client.publish('delta_azimuth', str(d_azimuth), 0)
        self.client.publish('delta_elevation', str(d_elevation), 0)

    def publish_start_azimuth(self, start_azimuth):
        self.client.publish('start_azimuth', str(start_azimuth), 0)

    def publish_action(self, action):
        self.client.publish('action', action, 0)
        print_info('published action: {0}'.format(action))

    def publish_polarization(self, pol):
        self.client.publish('polarization', pol, 0)
        print_info('polarization changed to: {0}'.format(pol))


mqtt = Mqtt()
