####################################################################################################
#                                                                                                  #
#                                     ELEVATION STEPPER MODULE                                     #
#                                                                                                  #
#                          Module for controlling elevation stepper motor                          #
#                                                                                                  #
#                                           David Nenicka                                          #
#                                                                                                  #
####################################################################################################


import RPi.GPIO as GPIO
import threading
import time

from Publisher import publisher


class ElevationStepper:
    def __init__(self):
        self.step_duration = 0.00001
        self.remain = 0
        self.ratio = 11
        self.microstepping = 4
        self.angle1 = 1.8 / (self.microstepping * self.ratio)
        self.increment = 0
        self.elevation = 0
        self.real_steps = 0
        self.setting = False
        self.tracking = False
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
        self.disable_motor()
        GPIO.output(self.DIR, GPIO.LOW)
        GPIO.output(self.STEP, GPIO.HIGH)
#       GPIO.add_event_detect(self.SW, GPIO.RISING, callback=self.set, bouncetime=500)

    def enable_motor(self):
        GPIO.output(self.ENABLE, GPIO.HIGH)

    def disable_motor(self):
        GPIO.output(self.ENABLE, GPIO.LOW)

    def step(self):
        GPIO.output(self.STEP, GPIO.LOW)
        time.sleep(self.step_duration)
        GPIO.output(self.STEP, GPIO.HIGH)

     def start(self):
        self.tracking = True
        self.enable_motor()
        self.remain = 0

    def stop(self):
        self.tracking = False
        self.disable_motor()
        print('Final elevation:', self.elevation)

    def increase_elevation(self):
        self.elevation += self.angle1
        self.remain -= self.angle1
        self.real_steps += 1

    def decrease_elevation(self):
        self.elevation -= self.angle1
        self.remain += self.angle1
        self.real_steps -= 1

    def set_speed(self, duration, angle):
        self.real_steps = 0
        self.start_time = time.time()
        self.duration = duration
        self.remain += angle
        self.increment = (self.angle1 * self.duration) / abs(self.remain)
        print('EL Duration:', self.duration, 'Remain:', self.remain, 'Increment:', self.increment, 'Expected steps:', int(self.remain/self.angle1))
        if (time.time() - self.start_time) < (self.duration - self.increment):
            if self.remain > self.angle1:
                GPIO.output(self.DIR, GPIO.HIGH)
                threading.Timer(self.increment, self.create_step).start()
            if self.remain < -self.angle1:
                GPIO.output(self.DIR, GPIO.LOW)
                threading.Timer(self.increment, self.create_step).start()

    def create_step(self):
        self.step()
        if self.remain > 0:
            self.increase_elevation()
        else:
            self.decrease_elevation()
        publisher.elevation = self.elevation
        if (time.time() - self.start_time) < (self.duration - self.increment):
            threading.Timer(self.increment, self.create_step).start()
        else:
            print('EL real steps:', self.real_steps)

    def set(self, channel):
        self.setting = not self.setting
        if self.setting and (not self.tracking):
            self.enable_motor()
            print("Elevation setting")
            change = 0
            prev = False
            while GPIO.input(self.SW):
                encoder_a = GPIO.input(self.A)
                encoder_b = GPIO.input(self.B)
                if (not encoder_a) and prev:
                    if encoder_a == encoder_b:
                        self.increase_elevation()
                        change += self.angle1
                        GPIO.output(self.DIR, GPIO.HIGH)
                    else:
                        self.decrease_elevation()
                        change -= self.angle1
                        GPIO.output(self.DIR, GPIO.LOW)
                    time.sleep(0.00005)
                    self.step()
                    time.sleep(0.00005)
                    publisher.elevation = self.elevation
                prev = encoder_a
            print("Elevation change: " + str(round(change, 2)) + "*\n")
            self.disable_motor()


elevation_stepper = ElevationStepper()
