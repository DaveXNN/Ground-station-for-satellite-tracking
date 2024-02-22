import RPi.GPIO as GPIO
import time

from threading import Timer

from Publisher import publisher as pub


class ElevationStepper:
    def __init__(self):
        self.sd = 0.00001
        self.dbs = 0.001
        self.rat = 11
        self.ms = 4
        self.a1 = 1.8 / (self.ms * self.rat)
        self.el = 0
        self.rem = 0
        self.i = 0
        self.ENABLE = 17
        self.DIR = 27
        self.STEP = 22
        GPIO.setup(self.ENABLE, GPIO.OUT)
        GPIO.setup(self.DIR, GPIO.OUT)
        GPIO.setup(self.STEP, GPIO.OUT)
        self.disable_motor()
        self.set_positive_direction()

    def enable_motor(self):
        GPIO.output(self.ENABLE, GPIO.HIGH)
        GPIO.output(self.STEP, GPIO.HIGH)

    def disable_motor(self):
        GPIO.output(self.ENABLE, GPIO.LOW)
        GPIO.output(self.STEP, GPIO.HIGH)

    def set_positive_direction(self):
        GPIO.output(self.DIR, GPIO.HIGH)

    def set_negative_direction(self):
        GPIO.output(self.DIR, GPIO.LOW)

    def step(self):
        GPIO.output(self.STEP, GPIO.LOW)
        time.sleep(self.sd)
        GPIO.output(self.STEP, GPIO.HIGH)

    def start(self):
        self.enable_motor()

    def stop(self):
        self.disable_motor()
        print('Final elevation:', self.elevation)

    def increase_elevation(self):
        self.el += self.a1
        self.rem -= self.a1
        pub.el = self.el

    def decrease_elevation(self):
        self.el -= self.a1
        self.rem += self.a1
        pub.el = self.el

    def set_speed(self, dur, a):
        self.st = time.time()
        self.dur = dur
        self.rem += a
        self.i = (self.a1 * self.dur) / abs(self.rem)
        if (time.time() - self.st) < (self.dur - self.i - self.sd):
            if self.rem > self.a1:
                self.set_positive_direction()
                Timer(self.i, self.step_forward).start()
            if self.rem < -self.a1:
                self.set_negative_direction()
                Timer(self.i, self.step_backward).start()

    def step_forward(self):
        self.step()
        self.increase_elevation()
        if (time.time() - self.st) < (self.dur - self.i - self.sd - 0.1):
            Timer(self.i, self.step_forward).start()

    def step_backward(self):
        self.step()
        self.decrease_elevation()
        if (time.time() - self.st) < (self.dur - self.i - self.sd - 0.1):
            Timer(self.i, self.step_backward).start()

    def move_to_elevation(self, el):
        self.el1 = el
        self.d_el = self.el1 - self.el
        self.rem += self.d_el
        if self.d_el > self.a1:
            self.set_positive_direction()
            Timer(self.dbs, self.step_forward2).start()
        if self.d_el < -(self.a1):
            self.set_negative_direction()
            Timer(self.dbs, self.step_backward2).start()

    def step_forward2(self):
        self.step()
        self.increase_elevation()
        if abs(self.el1 - self.el) > self.a1:
            Timer(self.dbs, self.step_forward2).start()

    def step_backward2(self):
        self.step()
        self.decrease_elevation()
        if abs(self.el1 - self.el) > self.a1:
            Timer(self.dbs, self.step_backward2).start()

 
elevation_stepper = ElevationStepper()
