import RPi.GPIO as GPIO

from threading import Timer
from time import sleep


class AzimuthStepper:
    def __init__(self):
        self.sd = 0.00001			# duration of 1 step
        self.dbs = 0.001			# min. delay between 2 steps
        self.rat = 12.22222			# ratio of spur gears
        self.ms = 4				# microstepping
        self.a1 = 1.8 / (self.ms * self.rat)	# elementary angle (angle of 1 step)
        self.az = 0				# azimuth
        self.pos = 0				# position
        self.rem = 0				# remaining angle
        self.i = 0				# time increment
        self.i2 = 0				# increment of the first step
        self.offset = 0                         # offset
        self.finished = True			# status: False -> moving, True -> finished moving
        self.ENABLE = 10			# number of ENABLE pin
        self.DIR = 9				# number of DIR pin
        self.STEP = 11				# number of STEP pin
        GPIO.setup(self.ENABLE, GPIO.OUT)	# set ENABLE as output
        GPIO.setup(self.DIR, GPIO.OUT)		# set DIR as output
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

    def increase_azimuth(self):			# increase azimuth (values) by 1 elementary angle
        self.az += self.a1
        self.pos += self.a1
        self.rem -= self.a1
        if self.az >= 360:
            self.az -= 360

    def decrease_azimuth(self):			# decrease azimuth (values) by 1 elementary angle
        self.az -= self.a1
        self.pos -= self.a1
        self.rem += self.a1
        if self.az <= 0:
            self.az += 360

    def wait_until_finished(self):		# wait until another AZ process is finished
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
        self.increase_azimuth()
        if self.rem >= self.a1:
            Timer(self.i, self.step_forward).start()
        else:
            self.finished = True

    def step_backward(self):			# 1 step in negative direction (usage: set_speed())
        self.step()
        self.decrease_azimuth()
        if self.rem <= -self.a1:
            Timer(self.i, self.step_backward).start()
        else:
            self.finished = True

    def move_to_azimuth(self, az):		# move to different azimuth (before tracking)
        self.wait_until_finished()
        self.rem = self.rem + az - self.az
        if self.rem > 180:
            self.rem -= 360
        if self.rem < -180:
            self.rem += 360
        if self.rem >= self.a1:
            self.set_positive_direction()
            Timer(self.dbs, self.step_forward2).start()
        elif self.rem <= -self.a1:
            self.set_negative_direction()
            Timer(self.dbs, self.step_backward2).start()
        else:
            self.finished = True

    def step_forward2(self):			# 1 step in positive direction (usage: move_to_azimuth(), reset_position())
        self.step()
        self.increase_azimuth()
        if self.rem >= self.a1:
            Timer(self.dbs, self.step_forward2).start()
        else:
            self.finished = True

    def step_backward2(self):			# 1 step in negative direction (usage: move_to_azimuth(), reset_position())
        self.step()
        self.decrease_azimuth()
        if self.rem <= -self.a1:
            Timer(self.dbs, self.step_backward2).start()
        else:
            self.finished = True

    def reset_position(self):			# reset AZ position to zero
        self.wait_until_finished()
        self.rem -= self.pos
        if self.rem >= self.a1:
            self.set_positive_direction()
            Timer(self.dbs, self.step_forward2).start()
        elif self.rem <= -self.a1:
            self.set_negative_direction()
            Timer(self.dbs, self.step_backward2).start()
        else:
            self.finished = True

    def set_offset(self, offset):               # set AZ offset
        self.wait_until_finished()
        self.rem = self.rem + offset - self.offset
        self.offset = offset
        if self.rem >= self.a1:
            self.set_positive_direction()
            Timer(self.dbs, self.step_forward3).start()
        elif self.rem <= -self.a1:
            self.set_negative_direction()
            Timer(self.dbs, self.step_backward3).start()
        else:
            self.finished = True

    def step_forward3(self):			# 1 step in positive direction (usage: set_offset())
        self.step()
        self.rem -= self.a1
        if self.rem >= self.a1:
            Timer(self.dbs, self.step_forward3).start()
        else:
            self.finished = True

    def step_backward3(self):			# 1 step in negative direction (usage: set_offset())
        self.step()
        self.rem += self.a1
        if self.rem <= -self.a1:
            Timer(self.dbs, self.step_backward3).start()
        else:
            self.finished = True
