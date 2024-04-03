import os
import paho.mqtt.client as paho
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

from AzimuthStepper import azimuth_stepper as az_st
from ElevationStepper import elevation_stepper as el_st
from PolarizationSwitcher import polarization_switcher as pol_sw
from Publisher import publisher as pub


delta_t = 0
tracking = False


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print('Rotator connected to MQTT broker')
    else:
        print('Rotator not connected to MQTT broker', rc)


def on_message(client, userdata, message):
    global delta_t
    global tracking
    topic = str(message.topic)
    msg = str(message.payload.decode('utf-8'))
    if topic == 'action':
        if msg == 'start':
            tracking = True
        if msg == 'stop':
            az_st.reset_position()
            tracking = False
        if msg == 'shutdown' and not tracking:
            az_st.disable_motor()
            az_st.disable_motor()
            os.system('sudo shutdown now')
    if topic == 'start_azimuth' and tracking:
        az_st.move_to_azimuth(float(msg))
        el_st.move_to_elevation(0)
    if topic == 'delta_time' and tracking:
        delta_t = float(msg)
    if topic == 'delta_azimuth' and tracking:
        az_st.set_speed(delta_t, float(msg))
    if topic == 'delta_elevation' and tracking:
        el_st.set_speed(delta_t, float(msg))
    if topic == 'polarization':
        pol_sw.set(msg)


client = paho.Client()
client.username_pw_set('rotator', password='rotator')
client.on_connect = on_connect
client.on_message = on_message
client.connect('raspberrypi', port=1883)
client.subscribe('action')
client.subscribe('start_azimuth')
client.subscribe('delta_time')
client.subscribe('delta_azimuth')
client.subscribe('delta_elevation')
client.subscribe('polarization')
client.loop_forever()
