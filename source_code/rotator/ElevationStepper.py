import RPi.GPIO as GPIO

from threading import Timer
from time import sleep


class ElevationStepper:
    def __init__(self):
        self.sd = 0.00001			# duration of 1 step
        self.dbs = 0.001			# min. delay between 2 steps
        self.rat = 11				# ratio of spur gears
        self.ms = 4				# microstepping
        self.a1 = 1.8 / (self.ms * self.rat)	# elementary angle (angle of 1 step)
        self.el = 0				# elevation
        self.rem = 0				# remaining angle
        self.i = 0				# time increment
        self.i2 = 0				# tiem increment of the first step
        self.finished = True			# status False -> moving, True -> moving finished
        self.ENABLE = 17			# number of ENABLE pin
        self.DIR = 27				# number of DIR pin
        self.STEP = 22				# number of STEP pin
        GPIO.setup(self.ENABLE, GPIO.OUT)	# set ENABLE as output
        GPIO.setup(self.DIR, GPIO.OUT)		# set DIR as soutput
        GPIO.setup(self.STEP, GPIO.OUT)		# set STEP as output
        self.enable_motor()			# enable stepper motor
        self.set_positive_direction()		# set positive direction

    def enable_motor(self):			# enable stepper motor
        GPIO.output(self.ENABLE, GPIO.HIGH)
        GPIO.output(self.STEP, GPIO.HIGH)

    def disable_motor(self):			# disable stepper motor
        GPIO.output(self.ENABLE, GPIO.LOW)
        GPIO.output(self.STEP, GPIO.HIGH)

    def set_positive_direction(self):		# set positive direction
        GPIO.output(self.DIR, GPIO.HIGH)

    def set_negative_direction(self):		# set negative direction
        GPIO.output(self.DIR, GPIO.LOW)

    def step(self):				# do 1 step
        GPIO.output(self.STEP, GPIO.LOW)
        sleep(self.sd)
        GPIO.output(self.STEP, GPIO.HIGH)

    def increase_elevation(self):		# increase elevation (values) by 1 elementary angle
        self.el += self.a1
        self.rem -= self.a1

    def decrease_elevation(self):		# decrease elevation (values) by 1 elementary angle
        self.el -= self.a1
        self.rem += self.a1

    def wait_until_finished(self):		# wait until EL process is finished
        while not self.finished:
            pass
        self.finished = False

    def set_speed(self, dur, a):		# set speed (parameters: duration, angle)
        self.wait_until_finished()
        self.rem += a
        self.i = (self.a1 * dur) / abs(self.rem)
        self.i2 = self.i / 2
        if self.rem >= self.a1:
            self.set_positive_direction()
            Timer(self.i2, self.step_forward).start()
        elif self.rem <= -self.a1:
            self.set_negative_direction()
            Timer(self.i2, self.step_backward).start()
        else:
            self.finished = True

    def step_forward(self):			# 1 step in positive direction (usage: set_speed())
        self.step()
        self.increase_elevation()
        if self.rem >= self.a1:
            Timer(self.i, self.step_forward).start()
        else:
            self.finished = True

    def step_backward(self):			# 1 step in negative direction (usage: set_speed())
        self.step()
        self.decrease_elevation()
        if self.rem <= -self.a1:
            Timer(self.i, self.step_backward).start()
        else:
            self.finished = True

    def move_to_elevation(self, el):		# move to different elevation (before tracking)
        self.wait_until_finished()
        self.rem = self.rem + el - self.el
        if self.rem >= self.a1:
            self.set_positive_direction()
            Timer(self.dbs, self.step_forward2).start()
        elif self.rem <= -self.a1:
            self.set_negative_direction()
            Timer(self.dbs, self.step_backward2).start()
        else:
            self.finished = True

    def step_forward2(self):			# 1 step in positive direction (usage: move_to_elevation())
        self.step()
        self.increase_elevation()
        if self.rem >= self.a1:
            Timer(self.dbs, self.step_forward2).start()
        else:
            self.finished = True

    def step_backward2(self):			# 1 step in negative direction (usage: move_to_elevation())
        self.step()
        self.decrease_elevation()
        if self.rem <= -self.a1:
            Timer(self.dbs, self.step_backward2).start()
        else:
            self.finished = True

 
elevation_stepper = ElevationStepper()
