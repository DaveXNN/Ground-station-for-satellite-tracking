####################################################################################################
#                                                                                                  #
#                                          ROTATOR MODULE                                          #
#                                                                                                  #
#          Module for subscribing data from MQTT server and controlling the whole rotator          #
#                                                                                                  #
#                                           David Nenicka                                          #
#                                                                                                  #
####################################################################################################


import paho.mqtt.client as paho
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

from AzimuthStepper import azimuth_stepper
from ElevationStepper import elevation_stepper
from Publisher import publisher


delta_t = 0
prev_satellite = ''


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print('Rotator.py is connected to MQTT broker')
    else:
        print('MQTT client is not connected')


def on_message(client, userdata, message):
    global delta_t
    global prev_satellite
    topic = str(message.topic)
    msg = str(message.payload.decode('utf-8'))
    if topic == 'action':
        if msg == 'start':
            publisher.status = 'tracking'
            print('Tracking started')
            azimuth_stepper.start()
            elevation_stepper.start()
        if msg == 'stop':
            publisher.status = 'sleeping'
            print('Tracking ended')
            azimuth_stepper.stop()
            elevation_stepper.stop()
    if topic == 'satellite':
        satellite = msg
        publisher.satellite = satellite
        if prev_satellite != satellite:
            prev_satellite = satellite
            if satellite != '':
                print('Tracked satellite:', satellite)
     if topic == 'start_azimuth':
        azimuth_stepper.turn_to_azimuth(float(msg))
    if topic == 'delta_time':
        delta_t = float(msg)
    if topic == 'delta_azimuth':
        azimuth_stepper.set_speed(delta_t, float(msg))
    if topic == 'delta_elevation':
        elevation_stepper.set_speed(delta_t, float(msg))


client = paho.Client()
client.username_pw_set('rotator', password='rotator')
client.on_connect = on_connect
client.on_message = on_message
client.connect('raspberrypi', port=1883)
client.subscribe('action')
client.subscribe('satellite')
client.subscribe('start_azimuth')
client.subscribe('delta_time')
client.subscribe('delta_azimuth')
client.subscribe('delta_elevation')
client.loop_forever()
