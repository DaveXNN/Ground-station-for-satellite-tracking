import math
import RPi.GPIO as GPIO                                             # library for GPIO pins of Raspberry Pi
import smbus                                                        # library for I2C communication via GPIO2 and GPIO3 pins
import sys
import threading
import time

bus = smbus.SMBus(1)                                                # I2C bus for magnetometer

class AzimuthStepper():                                             # module for azimuth stepper motor control
    def __init__(self):                                         
        self.step_duration = 0.00001                                # duration from rising to falling edge               
        self.remain = 0                                             # remaining angle which rotator must turn 
        self.ratio = (110/9)                                        # ratio of spur gears
        self.microstepping = 4                                      # microstepping of stepper motor
        self.angle1 = 1.8 / (self.microstepping * self.ratio)       # angle of one step of rotator (in degrees)
        self.max_speed = 5                                          # max speed (in degrees per second)
        self.setting_state = False                                  # True = setting mode (we set azimuth manualy using rotary encoder)
        self.change = 0                                             # azimuth change during setting mode
        self.ENABLE = 0                                             # digital pin, enable stepper motor
        self.DIR = 1                                                # digital pin, direction of rotation
        self.STEP = 4                                               # digital pin, step on falling edge
        self.A = 8                                                  # digital pin, pin A of rotary encoder
        self.B = 9                                                  # digital pin, pin B of rotary encoder
        self.SW = 10                                                # digital pin, button of rotary encoder
        GPIO.setup(self.ENABLE, GPIO.OUT)                           # set ENABLE to output
        GPIO.setup(self.DIR, GPIO.OUT)                              # set DIR to output                      
        GPIO.setup(self.STEP, GPIO.OUT)                             # set STEP to output 
        GPIO.setup(self.A, GPIO.IN, pull_up_down = GPIO.PUD_UP)     # set A to input
        GPIO.setup(self.B, GPIO.IN, pull_up_down = GPIO.PUD_UP)     # set B to input
        GPIO.setup(self.SW, GPIO.IN, pull_up_down = GPIO.PUD_UP)    # set SW to input
        GPIO.output(self.ENABLE, GPIO.LOW)                          # set ENABLE to zero (motor is disabled)
        GPIO.output(self.DIR, GPIO.HIGH)                            # set DIR to one (positive direction)
        GPIO.output(self.STEP, GPIO.HIGH)                           # set step to one
        GPIO.add_event_detect(self.SW, GPIO.RISING, callback = self.set, bouncetime = 500) # external interrupt (when the button in pressed, switches to setting mode)

    def set_speed(self, duration, angle):                           # set azimuth speed for duration and angle
        GPIO.output(self.ENABLE, GPIO.HIGH)
        self.start_time = time.time()
        self.duration = duration
        self.angle = angle
        self.remain += self.angle
        if (self.remain != 0):
            if(self.remain < -180):
                self.remain = self.remain + 360
            if(self.remain > 180):
                self.remain = self.remain - 360
            if(self.remain < 0):
                GPIO.output(self.DIR, GPIO.LOW)
            else:
                GPIO.output(self.DIR, GPIO.HIGH)
            self.increment = (self.angle1 * self.duration) / abs(self.remain)
            self.next_t = time.time() + self.increment
            if((time.time() - self.start_time) < (self.duration - self.increment)): 
                threading.Timer(self.next_t - time.time(), self.create_step).start()

    def create_step(self):                                              # create timer interrupt for one step
        if (self.remain > 0):
            self.remain -= self.angle1
        else:
            self.remain += self.angle1
        self.step()
        self.next_t += self.increment
        if (time.time() - self.start_time) < (self.duration - self.increment):
            threading.Timer(self.next_t - time.time(), self.create_step).start()
        else:
            GPIO.output(self.ENABLE, GPIO.LOW)

    def step(self):                                                     # one step
        GPIO.output(self.STEP, GPIO.LOW)
        time.sleep(self.step_duration)
        GPIO.output(self.STEP, GPIO.HIGH)

    def turn_to_azimuth(self, azimuth):                                 # turn rotator to given azimuth
        self.azimuth = azimuth
        self.delta_az = self.azimuth - magnetometer.read_azimuth(measurements = 100)
        self.delta_t = abs(self.delta_az)/self.max_speed
        self.set_speed(self.delta_t, self.delta_az)
        time.sleep(self.delta_t)

    def set(self, channel):                                             # manual azimuth setting
        GPIO.output(self.ENABLE, GPIO.HIGH)                             # set ENABLE to one (motor is enabled)
        self.setting_state = not self.setting_state
        if self.setting_state:
            print("Azimuth setting")
            self.prev = False
            while GPIO.input(self.SW):
                self.encoder_A = GPIO.input(self.A)
                self.encoder_B = GPIO.input(self.B)
                if((not self.encoder_A) and self.prev):                                   
                    if(self.encoder_A == self.encoder_B):
                        self.change += self.angle1
                        GPIO.output(self.DIR, GPIO.HIGH)
                    else:
                        self.change -= self.angle1
                        GPIO.output(self.DIR, GPIO.LOW)
                    time.sleep(0.00001)
                    self.step()
                self.prev = self.encoder_A
            print("Azimuth change: " + str(round(self.change, 2)) + "*\n")
            self.change = 0
        else:
            GPIO.output(self.ENABLE, GPIO.LOW)
            
class ElevationStepper():                                           # module for elevation stepper motor control
    def __init__(self):
        self.step_duration = 0.00001                                # duration from rising to falling edge              
        self.remain = 0                                             # remaining angle which rotator must turn 
        self.ratio = 11                                             # ratio of spur gears
        self.microstepping = 4                                      # microstepping of stepper motor
        self.angle1 = 1.8 / (self.microstepping * self.ratio)       # angle of one step of rotator (in degrees)
        self.setting_state = False                                  # True = setting mode (we set azimuth manualy using rotary encoder)
        self.change = 0                                             # azimuth change during setting mode
        self.ENABLE = 5                                             # digital pin, enable stepper motor
        self.DIR = 6                                                # digital pin, direction of rotation
        self.STEP = 7                                               # digital pin, step on falling edge
        self.A = 11                                                 # digital pin, pin A of rotary encoder
        self.B = 12                                                 # digital pin, pin B of rotary encoder
        self.SW = 13                                                # digital pin, button of rotary encoder
        GPIO.setup(self.ENABLE, GPIO.OUT)                           # set ENABLE to output
        GPIO.setup(self.DIR, GPIO.OUT)                              # set DIR to output   
        GPIO.setup(self.STEP, GPIO.OUT)                             # set STEP to output 
        GPIO.setup(self.A, GPIO.IN, pull_up_down = GPIO.PUD_UP)     # set A to input
        GPIO.setup(self.B, GPIO.IN, pull_up_down = GPIO.PUD_UP)     # set B to input
        GPIO.setup(self.SW, GPIO.IN, pull_up_down = GPIO.PUD_UP)    # set SW to input
        GPIO.output(self.ENABLE, GPIO.LOW)                          # set ENABLE to zero (motor is disabled)
        GPIO.output(self.DIR, GPIO.LOW)                             # set DIR to one (positive direction)
        GPIO.output(self.STEP, GPIO.HIGH)                           # set step to one
        GPIO.add_event_detect(self.SW, GPIO.RISING, callback = self.set, bouncetime = 500) # external interrupt (when the button in pressed, switches to setting mode)

    def set_speed(self, duration, angle):                           # set elevation speed for duration and angle
        GPIO.output(self.ENABLE, GPIO.HIGH)                         # set ENABLE to one (stepper motor is enabled)
        self.start_time = time.time()
        self.duration = duration
        self.angle = angle
        self.remain += self.angle
        if(self.remain != 0):
            if(self.remain < 0):
                GPIO.output(self.DIR, GPIO.LOW)
            else:
                GPIO.output(self.DIR, GPIO.HIGH)
            self.increment = (self.angle1 * self.duration) / abs(self.remain)
            self.next_t = time.time() + self.increment
            if((time.time() - self.start_time) < (self.duration - self.increment)): 
                threading.Timer(self.next_t - time.time(), self.create_step).start()

    def create_step(self):                                          # create timer interrupt for one step
        if (self.remain > 0):
            self.remain -= self.angle1
        else:
            self.remain += self.angle1
        self.step()
        self.next_t += self.increment
        if (time.time() - self.start_time) < (self.duration - self.increment):
            threading.Timer(self.next_t - time.time(), self.create_step).start()
        else:
            GPIO.output(self.ENABLE, GPIO.LOW)

    def step(self):                                                 # one step
        GPIO.output(self.STEP, GPIO.LOW)
        time.sleep(self.step_duration)
        GPIO.output(self.STEP, GPIO.HIGH)

    def set(self, channel):                                         # manual elevation setting
        GPIO.output(self.ENABLE, GPIO.HIGH)
        self.setting_state = not self.setting_state
        if self.setting_state:
            print("Elevation setting")
            self.prev = False
            while GPIO.input(self.SW):
                self.encoder_A = GPIO.input(self.A)
                self.encoder_B = GPIO.input(self.B)
                if((not self.encoder_A) and self.prev):                                   
                    if(self.encoder_A == self.encoder_B):
                        self.change += self.angle1
                        GPIO.output(self.DIR, GPIO.HIGH)
                    else:
                        self.change -= self.angle1
                        GPIO.output(self.DIR, GPIO.LOW)
                    time.sleep(0.00001)
                    self.step()
                self.prev = self.encoder_A
            print("Elevation change: " + str(round(self.change, 2)) + "*\n")
            self.change = 0
        else:
            GPIO.output(self.ENABLE, GPIO.LOW)

class Magnetometer():                                                   # module for magnetometer control
    def __init__(self):
        self.declination = 3.5                                          # declination angle (in degrees) of location
        bus.write_byte_data(0x1e, 0, 0x70)                              # write to Configuration Register A
        bus.write_byte_data(0x1e, 0x01, 0xa0)                           # write to Configuration Register B for gain
        bus.write_byte_data(0x1e, 0x02, 0)                              # write to mode Register for selecting mode
        self.az_cor = -176                                              # azimuth correction
        self.x_cor = 114                                                # x magnetic field correction
        self.y_cor = 128                                                # y magnetic field correction

    def read_raw_data(self, addr):
        high = bus.read_byte_data(0x1e, addr)                           # Read raw 16-bit value
        low = bus.read_byte_data(0x1e, addr+1)  
        value = ((high << 8) | low)                                     # concatenate higher and lower value
        if(value > 32768):                                              # to get signed value from module
            value = value - 65536
        return value

    def read_azimuth(self, measurements):                               # read azimuth
        self.sum = 0
        for x in range(measurements):                                   # x times measure magnetic field
            x = self.read_raw_data(addr = 0x03) + self.x_cor            # measure magnetic field in x axis
            z = self.read_raw_data(addr = 0x05)                         # measure magnetic field in y axis
            y = self.read_raw_data(addr = 0x07) + self.y_cor            # measure magnetic field in z axis
            self.heading = float(math.atan2(y, x) * 180/3.14159265359) + self.declination + self.az_cor # calculate heading
            if(self.heading > 360):
                self.heading = self.heading - 360
            if(self.heading < 0):
                self.heading = self.heading + 360
            self.sum = self.sum + self.heading
        self.heading = self.sum / measurements
        return self.heading

magnetometer = Magnetometer()
