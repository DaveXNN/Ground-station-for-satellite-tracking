import paho.mqtt.client as paho
import RPi.GPIO as GPIO
import threading
import time


class ElevationStepper:
    def __init__(self):
        self.step_duration = 0.00001
        self.remain = 0
        self.ratio = 11
        self.microstepping = 4
        self.angle1 = 1.8 / (self.microstepping * self.ratio)
        self.increment = 0
        self.next_t = 0
        self.elevation0 = 0
        self.elevation = 0
        self.setting_state = False
        self.change = 0
        self.ENABLE = 17
        self.DIR = 27
        self.STEP = 22
        self.A = 13
        self.B = 19
        self.SW = 26
        GPIO.setup(self.ENABLE, GPIO.OUT)
        GPIO.setup(self.DIR, GPIO.OUT)
        GPIO.setup(self.STEP, GPIO.OUT)
        GPIO.setup(self.A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.B, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.SW, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.output(self.DIR, GPIO.LOW)
        GPIO.output(self.STEP, GPIO.HIGH)
        GPIO.add_event_detect(self.SW, GPIO.RISING, callback=self.set, bouncetime=500)
        self.disable_motor()
        self.client = paho.Client()  # create mqtt client
        self.client.username_pw_set('elevationstepper', password='elevationstepper')  # mqtt server authorization
        self.publish_thread = threading.Timer(1.0, self.publish_elevation)
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
        self.elevation = self.elevation0

    def stop(self):
        self.disable_motor()
        print('Elevation:', self.elevation)
        self.client.disconnect()

    def publish_elevation(self):
        if self.client.connect('raspberrypi', port=1883) == 0:
            self.client.publish('elevation', str(round(self.elevation, 2)), 0)
        self.publish_thread = threading.Timer(1.0, self.publish_elevation)
        self.publish_thread.start()

    def set_speed(self, duration, angle):
        self.start_time = time.time()
        self.duration = duration
        self.remain += angle
        if self.remain > self.angle1:
            GPIO.output(self.DIR, GPIO.HIGH)
            self.increment = (self.angle1 * self.duration) / abs(self.remain)
            self.next_t = time.time() + self.increment
            if (time.time() - self.start_time) < (self.duration - self.increment):
                threading.Timer(self.next_t - time.time(), self.create_step).start()
        else:
            GPIO.output(self.DIR, GPIO.LOW)
            self.increment = (self.angle1 * self.duration) / abs(self.remain)
            self.next_t = time.time() + self.increment
            if (time.time() - self.start_time) < (self.duration - self.increment):
                threading.Timer(self.next_t - time.time(), self.create_step).start()

    def create_step(self):
        if self.remain > 0:
            self.remain -= self.angle1
            self.elevation += self.angle1
        else:
            self.remain += self.angle1
            self.elevation -= self.angle1
        self.step()
        self.next_t += self.increment
        if (time.time() - self.start_time) < (self.duration - self.increment):
            threading.Timer(self.next_t - time.time(), self.create_step).start()

    def set(self, channel):
        self.setting_state = not self.setting_state
        if self.setting_state:
            self.enable_motor()
            print("Elevation setting")
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
                    self.step()
                    time.sleep(0.00005)
                self.prev = self.encoder_A
            print("Elevation change: " + str(round(self.change, 2)) + "*\n")
            self.disable_motor()
            self.change = 0


