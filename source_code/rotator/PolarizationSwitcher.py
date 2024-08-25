###########################################################################################################################
#                                                                                                                         #
#    Author:         D. Nenicka                                                                                           #
#    Created:        3. 11. 2023                                                                                          #
#    Modified:       25. 8. 2024                                                                                          #
#    Description:    Module for controling VHF and UHF polarization switchers                                             #
#                                                                                                                         #
###########################################################################################################################


import RPi.GPIO as GPIO


class PolarizationSwitcher:
    def __init__(self):
        self.UHF_REL1 = 0
        self.UHF_REL2 = 5
        self.VHF_REL1 = 6
        self.VHF_REL2 = 13
        GPIO.setup(self.UHF_REL1, GPIO.OUT)
        GPIO.setup(self.UHF_REL2, GPIO.OUT)
        GPIO.setup(self.VHF_REL1, GPIO.OUT)
        GPIO.setup(self.VHF_REL2, GPIO.OUT)
        GPIO.output(self.UHF_REL1, GPIO.LOW)
        GPIO.output(self.UHF_REL2, GPIO.LOW)
        GPIO.output(self.VHF_REL1, GPIO.LOW)
        GPIO.output(self.VHF_REL2, GPIO.LOW)

    def set(self, pol):
        if pol == 'Vertical':
            GPIO.output(self.UHF_REL1, GPIO.LOW)
            GPIO.output(self.UHF_REL2, GPIO.LOW)
            GPIO.output(self.VHF_REL1, GPIO.LOW)
            GPIO.output(self.VHF_REL2, GPIO.LOW)
        if pol == 'Horizontal':
            GPIO.output(self.UHF_REL1, GPIO.LOW)
            GPIO.output(self.UHF_REL2, GPIO.HIGH)
            GPIO.output(self.VHF_REL1, GPIO.LOW)
            GPIO.output(self.VHF_REL2, GPIO.HIGH)
        if pol == 'LHCP':
            GPIO.output(self.UHF_REL1, GPIO.HIGH)
            GPIO.output(self.UHF_REL2, GPIO.LOW)
            GPIO.output(self.VHF_REL1, GPIO.HIGH)
            GPIO.output(self.VHF_REL2, GPIO.LOW)
        if pol == 'RHCP':
            GPIO.output(self.UHF_REL1, GPIO.HIGH)
            GPIO.output(self.UHF_REL2, GPIO.HIGH)
            GPIO.output(self.VHF_REL1, GPIO.HIGH)
            GPIO.output(self.VHF_REL2, GPIO.HIGH)
