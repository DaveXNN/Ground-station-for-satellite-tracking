###########################################################################################################################
#                                                                                                                         #
#    Author:         D. Nenicka                                                                                           #
#    Created:        3. 11. 2023                                                                                          #
#    Modified:       25. 8. 2024                                                                                          #
#    Description:    Module for stepper motor control                                                                     #
#                                                                                                                         #
###########################################################################################################################


import RPi.GPIO as GPIO                        # module for GPIO control

from threading import Timer                    # module for running multiple tasks in the same time
from time import sleep                         # module with sleep() function


class Stepper:
    def __init__(self, ena_gpio, dir_gpio, pul_gpio, e1, microstep, ratio, azimuth_mode=False):
        self.ena = ena_gpio                    # number of ENA pin
        self.dir = dir_gpio                    # number of DIR pin
        self.pul = pul_gpio                    # number of PUL pin
        GPIO.setup(self.ena, GPIO.OUT)         # set ENA as output
        GPIO.setup(self.dir, GPIO.OUT)         # set DIR as output
        GPIO.setup(self.pul, GPIO.OUT)         # set PUL as output
        self.a1 = e1 / (microstep * ratio)     # elementary angle (angle of 1 step)
        self.direction = 0                     # direction
        self.position = 0                      # position
        self.remain = 0                        # remaining angle
        self.offset = 0                        # offset
        self.i = 0                             # time increment
        self.i2 = 0                            # time increment of the first step
        self.sd = 0.00001                      # duration of 1 step
        self.dbs = 0.001                       # min. delay between 2 steps
        self.finished = True                   # status: False -> moving, True -> finished moving
        self.azimuth_mode = azimuth_mode       # mode
        self.enable_motor()                    # enable stepper motor
        self.set_positive_direction()          # set positive direction

    def enable_motor(self):                    # enable stepper motor
        GPIO.output(self.ena, GPIO.HIGH)
        GPIO.output(self.pul, GPIO.HIGH)

    def disable_motor(self):                   # disable stepper motor
        GPIO.output(self.ena, GPIO.LOW)
        GPIO.output(self.pul, GPIO.HIGH)

    def set_positive_direction(self):          # set positive direction
        GPIO.output(self.dir, GPIO.HIGH)

    def set_negative_direction(self):          # set negative direction
        GPIO.output(self.dir, GPIO.LOW)

    def step(self):                            # do 1 step
        GPIO.output(self.pul, GPIO.LOW)
        sleep(self.sd)
        GPIO.output(self.pul, GPIO.HIGH)

    def increase(self):                        # increase direction and position by 1 elementary angle
        self.direction += self.a1
        self.position += self.a1
        self.remain -= self.a1
        if self.azimuth_mode:
            if self.direction >= 360:
                self.direction -= 360

    def decrease(self):                        # decrease direction and position by 1 elementary angle
        self.direction -= self.a1
        self.position -= self.a1
        self.remain += self.a1
        if self.azimuth_mode:
            if self.direction <= 0:
                self.direction += 360

    def wait_until_finished(self):             # wait until another AZ process is finished
        while not self.finished:
            pass
        self.finished = False

    def set_speed(self, duration, angle):      # set speed (parameters: duration, angle)
        self.wait_until_finished()
        self.remain += angle
        self.i = (self.a1 * duration) / abs(self.remain)
        self.i2 = self.i / 2
        if self.remain >= self.a1:
            self.set_positive_direction()
            Timer(self.i2, self.step_forward).start()
        elif self.remain <= -self.a1:
            self.set_negative_direction()
            Timer(self.i2, self.step_backward).start()
        else:
            self.finished = True

    def step_forward(self):                    # 1 step in positive direction (usage: set_speed())
        self.step()
        self.increase()
        if self.remain >= self.a1:
            Timer(self.i, self.step_forward).start()
        else:
            self.finished = True

    def step_backward(self):                   # 1 step in negative direction (usage: set_speed())
        self.step()
        self.decrease()
        if self.remain <= -self.a1:
            Timer(self.i, self.step_backward).start()
        else:
            self.finished = True

    def move_to_direction(self, direction):    # move to different direction (before tracking)
        self.wait_until_finished()
        self.remain = self.remain + direction - self.direction
        if self.remain > 180:
            self.remain -= 360
        if self.remain < -180:
            self.remain += 360
        if self.remain >= self.a1:
            self.set_positive_direction()
            Timer(self.dbs, self.step_forward2).start()
        elif self.remain <= -self.a1:
            self.set_negative_direction()
            Timer(self.dbs, self.step_backward2).start()
        else:
            self.finished = True

    def step_forward2(self):                   # 1 step in positive direction (usage: move_to_direction(), reset_position())
        self.step()
        self.increase()
        if self.remain >= self.a1:
            Timer(self.dbs, self.step_forward2).start()
        else:
            self.finished = True

    def step_backward2(self):                  # 1 step in negative direction (usage: move_to_direction(), reset_position())
        self.step()
        self.decrease()
        if self.remain <= -self.a1:
            Timer(self.dbs, self.step_backward2).start()
        else:
            self.finished = True

    def reset_position(self):                  # reset position to zero
        self.wait_until_finished()
        self.remain -= self.position
        if self.remain >= self.a1:
            self.set_positive_direction()
            Timer(self.dbs, self.step_forward2).start()
        elif self.remain <= -self.a1:
            self.set_negative_direction()
            Timer(self.dbs, self.step_backward2).start()
        else:
            self.finished = True

    def set_offset(self, offset):              # set offset
        self.wait_until_finished()
        self.remain = self.remain + offset - self.offset
        self.offset = offset
        if self.remain >= self.a1:
            self.set_positive_direction()
            Timer(self.dbs, self.step_forward3).start()
        elif self.remain <= -self.a1:
            self.set_negative_direction()
            Timer(self.dbs, self.step_backward3).start()
        else:
            self.finished = True

    def step_forward3(self):                   # 1 step in positive direction (usage: set_offset())
        self.step()
        self.remain -= self.a1
        if self.remain >= self.a1:
            Timer(self.dbs, self.step_forward3).start()
        else:
            self.finished = True

    def step_backward3(self):                  # 1 step in negative direction (usage: set_offset())
        self.step()
        self.remain += self.a1
        if self.remain <= -self.a1:
            Timer(self.dbs, self.step_backward3).start()
        else:
            self.finished = True
