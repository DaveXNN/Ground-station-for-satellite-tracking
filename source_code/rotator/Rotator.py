###########################################################################################################################
#                                                                                                                         #
#    Author:         D. Nenicka                                                                                           #
#    Created:        3. 11. 2023                                                                                          #
#    Modified:       25. 8. 2024                                                                                          #
#    Description:    The main script, initializes all modules and subscribes topics from station computer via MQTT        #
#                                                                                                                         #
###########################################################################################################################


import os
import paho.mqtt.client as paho
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

from PolarizationSwitcher import PolarizationSwitcher
from Publisher import Publisher
from Stepper import Stepper


az_st = Stepper(10, 9, 11, 1.8, 4, 11, azimuth_mode=True)
el_st = Stepper(17, 27, 22, 1.8, 4, 11)
pol_sw = PolarizationSwitcher()
pub = Publisher(az_st, el_st) 
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
            el_st.reset_position()
            tracking = False
        if msg == 'shutdown' and not tracking:
            az_st.disable_motor()
            az_st.disable_motor()
            os.system('sudo shutdown now')
    if topic == 'start_azimuth' and tracking:
        az_st.move_to_direction(float(msg))
        el_st.reset_position()
    if topic == 'delta_time' and tracking:
        delta_t = float(msg)
    if topic == 'delta_azimuth' and tracking:
        az_st.set_speed(delta_t, float(msg))
    if topic == 'delta_elevation' and tracking:
        el_st.set_speed(delta_t, float(msg))
    if topic == 'polarization':
        pol_sw.set(msg)
    if topic == 'az_offset' and not tracking:
        az_st.set_offset(float(msg))
    if topic == 'el_offset' and not tracking:
        el_st.set_offset(float(msg))


client = paho.Client()
client.username_pw_set(<username>, password=<password>)
client.on_connect = on_connect
client.on_message = on_message
client.connect(<hostname>, port=<port>)
client.subscribe('action')
client.subscribe('start_azimuth')
client.subscribe('delta_time')
client.subscribe('delta_azimuth')
client.subscribe('delta_elevation')
client.subscribe('polarization')
client.subscribe('az_offset')
client.subscribe('el_offset')
client.loop_forever()
