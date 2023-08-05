####################################################################################################
#                                                                                                  #
#                                      AZIMUTH STEPPER MODULE                                      #
#                                                                                                  #
#                           Module for controlling azimuth stepper motor                           #
#                                                                                                  #
#                                           David Nenicka                                          #
#                                                                                                  #
####################################################################################################


import paho.mqtt.client as paho
import RPi.GPIO as GPIO
import threading
import time

from Magnetometer import Magnetometer


class AzimuthStepper:
    def __init__(self):
        self.step_duration = 0.00001
        self.remain = 0
        self.ratio = (110/9)
        self.microstepping = 4
        self.angle1 = 1.8 / (self.microstepping * self.ratio)
        self.increment = 0
        self.next_t = 0
        self.azimuth0 = 0
        self.azimuth = 0
        self.setting_state = False
        self.change = 0
        self.ENABLE = 10
        self.DIR = 9
        self.STEP = 11
        self.A = 0
        self.B = 5
        self.SW = 6
        GPIO.setup(self.ENABLE, GPIO.OUT)
        GPIO.setup(self.DIR, GPIO.OUT)
        GPIO.setup(self.STEP, GPIO.OUT)
        GPIO.setup(self.A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.B, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.SW, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.disable_motor()
        GPIO.output(self.DIR, GPIO.HIGH)
        GPIO.output(self.STEP, GPIO.LOW)
        GPIO.add_event_detect(self.SW, GPIO.RISING, callback=self.set, bouncetime=500)
        self.magnetometer = Magnetometer()
        self.client = paho.Client()  # create mqtt client
        self.client.username_pw_set('azimuthstepper', password='azimuthstepper')  # mqtt server authorization
        self.publish_thread = threading.Timer(1.0, self.publish_azimuth)
        self.publish_thread.start()

    def enable_motor(self):
        GPIO.output(self.ENABLE, GPIO.HIGH)

    def disable_motor(self):
        GPIO.output(self.ENABLE, GPIO.LOW)

    def step(self):
        GPIO.output(self.STEP, GPIO.LOW)
        time.sleep(self.step_duration)
        GPIO.output(self.STEP, GPIO.HIGH)

    def start(self):
        self.enable_motor()
        self.remain = 0

    def stop(self):
        self.disable_motor()
        print('End azimuth:', self.azimuth)
        print('Magnetometer read azimuth:', str(self.magnetometer.read_azimuth()))
        self.client.disconnect()

    def publish_azimuth(self):
        if self.client.connect('raspberrypi', port=1883) == 0:
            if self.azimuth > 360:
                self.azimuth -= 360
            if self.azimuth < 0:
                self.azimuth += 360
            self.client.publish('azimuth', str(round(self.azimuth, 2)), 0)
        self.publish_thread = threading.Timer(1.0, self.publish_azimuth)
        self.publish_thread.start()

    def set_speed(self, duration, angle):
        self.start_time = time.time()
        self.duration = duration
        self.remain += angle
        if self.remain != 0:
            if self.remain < 0:
                GPIO.output(self.DIR, GPIO.LOW)
            else:
                GPIO.output(self.DIR, GPIO.HIGH)
            self.increment = (self.angle1 * self.duration) / abs(self.remain)
            self.next_t = time.time() + self.increment
            if (time.time() - self.start_time) < (self.duration - self.increment):
                threading.Timer(self.next_t - time.time(), self.create_step).start()

    def create_step(self):
        if self.remain > 0:
            self.remain -= self.angle1
            self.azimuth += self.angle1
        else:
            self.remain += self.angle1
            self.azimuth -= self.angle1
        self.step()
        self.next_t += self.increment
        if (time.time() - self.start_time) < (self.duration - self.increment):
            threading.Timer(self.next_t - time.time(), self.create_step).start()

    def turn_to_azimuth(self, azimuth):
        self.azimuth0 = azimuth
        self.azimuth = self.azimuth0
        self.delta_az = self.azimuth - self.magnetometer.read_azimuth()
        if self.delta_az > 180:
            self.delta_az -= 360
        if self.delta_az < -180:
            self.delta_az += 360
        self.set_speed(25, self.delta_az)
        self.azimuth = self.azimuth0
        print(self.azimuth)
        print('Magnetometer read azimuth:', str(self.magnetometer.read_azimuth()))

    def set(self, channel):
        self.setting_state = not self.setting_state
        if self.setting_state:
            self.enable_motor()
            print("Azimuth setting")
            self.prev = False
            while GPIO.input(self.SW):
                self.encoder_A = GPIO.input(self.A)
                self.encoder_B = GPIO.input(self.B)
                if (not self.encoder_A) and self.prev:
                    if self.encoder_A == self.encoder_B:
                        self.change += self.angle1
                        GPIO.output(self.DIR, GPIO.HIGH)
                    else:
                        self.change -= self.angle1
                        GPIO.output(self.DIR, GPIO.LOW)
                    time.sleep(0.00005)
                    self.step()
                self.prev = self.encoder_A
            print("Azimuth change: " + str(round(self.change, 2)) + "*\n")
            self.disable_motor()
            self.change = 0
