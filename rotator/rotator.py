import math
import RPi.GPIO as GPIO
import signal
import smbus
import sys
import threading
import time

bus = smbus.SMBus(1)

class AzimuthStepper():
    def __init__(self):
        self.step_duration = 0.00001
        self.remain = 0
        self.ratio = (110/9)
        self.microstepping = 4
        self.angle1 = 1.8 / (self.microstepping * self.ratio)
        self.max_speed = 5
        self.setting_state = False
        self.change = 0
        self.ENABLE = 0
        self.DIR = 1
        self.STEP = 4
        self.A = 8
        self.B = 9 
        self.SW = 10
        GPIO.setup(self.ENABLE, GPIO.OUT)
        GPIO.setup(self.DIR, GPIO.OUT)
        GPIO.setup(self.STEP, GPIO.OUT)
        GPIO.setup(self.A, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        GPIO.setup(self.B, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        GPIO.setup(self.SW, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        GPIO.output(self.ENABLE, GPIO.LOW)
        GPIO.output(self.DIR, GPIO.HIGH)
        GPIO.output(self.STEP, GPIO.LOW)
        GPIO.add_event_detect(self.SW, GPIO.RISING, callback = self.set, bouncetime = 500)

    def set_speed(self, duration, angle):
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

    def create_step(self):
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

    def step(self):
        GPIO.output(self.STEP, GPIO.LOW)
        time.sleep(self.step_duration)
        GPIO.output(self.STEP, GPIO.HIGH)

    def turn_to_azimuth(self, azimuth):
        self.azimuth = azimuth
        self.delta_az = self.azimuth - magnetometer.read_azimuth(measurements = 100)
        self.delta_t = abs(self.delta_az)/self.max_speed
        self.set_speed(self.delta_t, self.delta_az)
        time.sleep(self.delta_t)

    def set(self, channel):
        GPIO.output(self.ENABLE, GPIO.HIGH)
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
            
class ElevationStepper():
    def __init__(self):
        self.step_duration = 0.00001
        self.remain = 0
        self.ratio = 11
        self.microstepping = 4
        self.angle1 = 1.8 / (self.microstepping * self.ratio)
        self.setting_state = False
        self.change = 0
        self.ENABLE = 5
        self.DIR = 6
        self.STEP = 7
        self.A = 11
        self.B = 12
        self.SW = 13
        GPIO.setup(self.ENABLE, GPIO.OUT)
        GPIO.setup(self.DIR, GPIO.OUT)
        GPIO.setup(self.STEP, GPIO.OUT)
        GPIO.setup(self.A, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        GPIO.setup(self.B, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        GPIO.setup(self.SW, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        GPIO.output(self.ENABLE, GPIO.LOW)
        GPIO.output(self.DIR, GPIO.LOW)
        GPIO.output(self.STEP, GPIO.HIGH)
        GPIO.add_event_detect(self.SW, GPIO.RISING, callback = self.set, bouncetime = 500)

    def set_speed(self, duration, angle):
        GPIO.output(self.ENABLE, GPIO.HIGH)
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

    def create_step(self):
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

    def step(self):
        GPIO.output(self.STEP, GPIO.LOW)
        time.sleep(self.step_duration)
        GPIO.output(self.STEP, GPIO.HIGH)

    def set(self, channel):
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

class Magnetometer():
    def __init__(self):
        self.declination = 3.5                        # define declination angle (in degrees) of location
        bus.write_byte_data(0x1e, 0, 0x70)            # write to Configuration Register A
        bus.write_byte_data(0x1e, 0x01, 0xa0)         # Write to Configuration Register B for gain
        bus.write_byte_data(0x1e, 0x02, 0)            # Write to mode Register for selecting mode

    def read_raw_data(self, addr):
        high = bus.read_byte_data(0x1e, addr)         # Read raw 16-bit value
        low = bus.read_byte_data(0x1e, addr+1)  
        value = ((high << 8) | low)                   # concatenate higher and lower value
        if(value > 32768):                            # to get signed value from module
            value = value - 65536
        return value

    def read_azimuth(self, measurements):
        self.measurements = measurements
        self.sum = 0
        for x in range(self.measurements):
            x = self.read_raw_data(addr = 0x03) + 114
            z = self.read_raw_data(addr = 0x05)
            y = self.read_raw_data(addr = 0x07) + 128
            self.heading = float(math.atan2(y, x) * 180/3.14159265359) + self.declination - 176
            if(self.heading > 360):
                self.heading = self.heading - 360
            if(self.heading < 0):
                self.heading = self.heading + 360
            self.sum = self.sum + self.heading
        self.heading = self.sum / self.measurements
        return self.heading

magnetometer = Magnetometer()
