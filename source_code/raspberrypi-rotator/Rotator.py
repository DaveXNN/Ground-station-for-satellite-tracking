import paho.mqtt.client as paho
import RPi.GPIO as GPIO

from AzimuthStepper import AzimuthStepper
from ElevationStepper import ElevationStepper


GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
az = AzimuthStepper()
el = ElevationStepper()
delta_t = 0
state = 'sleep'


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print('MQTT client is connected')
    else:
        print('MQTT client is not connected')


def on_message(client, userdata, message):
    global delta_t
    global state
    if str(message.topic) == 'state':
        state = str(message.payload.decode('utf-8'))
        if state == 'tracking':
            az.start()
            el.start()
        if state == 'sleep':
            az.stop()
            el.stop()
    if str(message.topic) == 'satellite':
        print('Tracked satellite:', str(message.payload.decode('utf-8')))
    if str(message.topic) == 'start_azimuth':
        print('Start azimuth:', str(message.payload.decode('utf-8')))
        az.turn_to_azimuth(float(str(message.payload.decode('utf-8'))))
    if str(message.topic) == 'delta_time' and state == 'tracking':
        delta_t = float(str(message.payload.decode('utf-8')))
        print('Delta time:', delta_t)
    if str(message.topic) == 'delta_azimuth' and state == 'tracking':
        print('Delta azimuth:', str(message.payload.decode('utf-8')))
        az.set_speed(delta_t, float(str(message.payload.decode('utf-8'))))
    if str(message.topic) == 'delta_elevation' and state == 'tracking':
        print('Delta elevation:', str(message.payload.decode('utf-8')))
        el.set_speed(delta_t, float(str(message.payload.decode('utf-8'))))


client = paho.Client()
client.username_pw_set('rotator', password='rotator')
client.on_connect = on_connect
client.on_message = on_message
client.connect('raspberrypi', port=1883)
client.subscribe('state')
client.subscribe('satellite')
client.subscribe('start_azimuth')
client.subscribe('delta_time')
client.subscribe('delta_azimuth')
client.subscribe('delta_elevation')
client.loop_forever()
