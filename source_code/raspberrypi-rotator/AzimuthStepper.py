import RPi.GPIO as GPIO
import time

from threading import Timer

from Publisher import publisher as pub


class AzimuthStepper:
    def __init__(self):
        self.sd = 0.00001
        self.dbs = 0.001
        self.rat = 12.22222
        self.ms = 4
        self.a1 = 1.8 / (self.ms * self.rat)
        self.az = 0
        self.rem = 0
        self.i = 0
        self.ENABLE = 10
        self.DIR = 9
        self.STEP = 11
        self.rs = 0
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
        print('Final azimuth:', self.az)

    def increase_azimuth(self): 
        self.az += self.a1
        self.rem -= self.a1
        self.rs += 1
        if self.az > 360:
            self.az -= 360
        pub.az = self.az

    def decrease_azimuth(self):
        self.az -= self.a1
        self.rem += self.a1
        self.rs -= 1
        if self.az < 0:
            self.az += 360
        pub.az = self.az

    def set_speed(self, dur, a):
        self.rs = 0
        self.st = time.time()
        self.dur = dur
        self.rem += a
        self.i = (self.a1 * self.dur) / abs(self.rem)
        print('AZ Duration:', self.dur, 'Remain:', self.rem, 'Expected steps:', int(self.rem/self.a1))
        if (time.time() - self.st) < (self.dur - self.i - self.sd):
            if self.rem > self.a1:
                self.set_positive_direction()
                Timer(self.i, self.step_forward).start()
            if self.rem < -self.a1:
                self.set_negative_direction()
                Timer(self.i, self.step_backward).start()

    def step_forward(self):
        self.step()
        self.increase_azimuth()
        if (time.time() - self.st) < (self.dur - self.i - self.sd - 0.1):
            Timer(self.i, self.step_forward).start()
        else:
            print('AZ real steps:', self.rs)

    def step_backward(self):
        self.step()
        self.decrease_azimuth()
        if (time.time() - self.st) < (self.dur - self.i - self.sd):
            Timer(self.i, self.step_backward).start()
        else:
            print('AZ real steps:', self.rs)

    def move_to_azimuth(self, az):
        self.rs = 0
        self.az1 = az
        self.d_az = self.az1 - self.az
        if self.d_az > 180:
            self.d_az -= 360
        if self.d_az < -180:
            self.d_az += 180
        if self.d_az > self.a1:
            self.set_positive_direction()
            Timer(self.dbs, self.step_forward2).start()
        if self.d_az < -(self.a1):
            self.set_negative_direction()
            Timer(self.dbs, self.step_backward2).start()
        self.rem += self.d_az
        print('Previous azimuth:', self.az, 'azimuth change:', self.d_az)
        print('AZ expected steps:', int(self.d_az/self.a1))

    def step_forward2(self):
        self.step()
        self.increase_azimuth()
        if abs(self.az1 - self.az) > self.a1:
            Timer(self.dbs, self.step_forward2).start()
        else:
            print('AZ real steps:', self.rs, 'new azimuth:', self.az)

    def step_backward2(self):
        self.step()
        self.decrease_azimuth()
        if abs(self.az1 - self.az) > self.a1:
            Timer(self.dbs, self.step_backward2).start()
        else:
            print('AZ real steps:', self.rs, 'new azimuth:', self.az)


azimuth_stepper = AzimuthStepper()
