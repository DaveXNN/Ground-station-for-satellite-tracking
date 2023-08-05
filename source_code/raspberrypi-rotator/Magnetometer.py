####################################################################################################
#                                                                                                  #
#                                      AZIMUTH STEPPER MODULE                                      #
#                                                                                                  #
#                           Module for controlling azimuth stepper motor                           #
#                                                                                                  #
#                                           David Nenicka                                          #
#                                                                                                  #
####################################################################################################

import math
import smbus


bus = smbus.SMBus(1)


class Magnetometer:
    def __init__(self):
        self.declination = 3.5                          # define declination angle (in degrees) of location
        self.heading = 0                                # rotator heading
        bus.write_byte_data(0x1e, 0, 0x70)              # write to Configuration Register A
        bus.write_byte_data(0x1e, 0x01, 0xa0)           # write to Configuration Register B for gain
        bus.write_byte_data(0x1e, 0x02, 0)              # write to mode Register for selecting mode

    @staticmethod
    def read_raw_data(addr):
        high = bus.read_byte_data(0x1e, addr)           # read raw 16-bit value
        low = bus.read_byte_data(0x1e, addr+1)
        value = ((high << 8) | low)                     # concatenate higher and lower value
        if value > 32768:                               # to get signed value from module
            value = value - 65536
        return value

    def read_azimuth(self):
        for x in range(100):
            x = self.read_raw_data(addr=0x03) + 114
            z = self.read_raw_data(addr=0x05)
            y = self.read_raw_data(addr=0x07) + 128
            self.heading += float(math.atan2(y, x) * 180/3.14159265359) + self.declination - 176
            if self.heading > 360:
                self.heading = self.heading - 360
            if self.heading < 0:
                self.heading = self.heading + 360
        return self.heading / 100
