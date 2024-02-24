import paho.mqtt.client as paho                                     # for publishing data from MQTT broker

from threading import Timer


class Publisher:
    def __init__(self):
        self.client = paho.Client()                                 # create mqtt client
        self.client.username_pw_set(<username>, password=<password>)  # mqtt server authorization
        if self.client.connect(<hostname>, port=<port>) == 0:
            print('Publisher connected to MQTT Broker', sep=', ')
        else:
            print('Publisher could not connect to MQTT Broker', sep=', ')
        self.az = 0        
        self.el = 0
        self.per = 1
        Timer(self.per, self.reg_pub).start()

    def reg_pub(self):
        self.client.publish('azimuth', str(self.az), 0)
        self.client.publish('elevation', str(self.el), 0)
        Timer(self.per, self.reg_pub).start()


publisher = Publisher()
