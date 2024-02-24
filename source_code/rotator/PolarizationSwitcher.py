import RPi.GPIO as GPIO


class PolarizationSwitcher:
    def __init__(self):
        self.A = 0
        self.B = 5
        GPIO.setup(self.A, GPIO.OUT)
        GPIO.setup(self.B, GPIO.OUT)
        GPIO.output(self.A, GPIO.LOW)
        GPIO.output(self.B, GPIO.LOW)

    def set(self, pol):
        if pol == 'Vertical':
            GPIO.output(self.A, GPIO.LOW)
            GPIO.output(self.B, GPIO.LOW)
        if pol == 'Horizontal':
            GPIO.output(self.A, GPIO.LOW)
            GPIO.output(self.B, GPIO.HIGH)
        if pol == 'LHCP':
            GPIO.output(self.A, GPIO.HIGH)
            GPIO.output(self.B, GPIO.LOW)
        if pol == 'RHCP':
            GPIO.output(self.A, GPIO.HIGH)
            GPIO.output(self.B, GPIO.HIGH)


polarization_switcher = PolarizationSwitcher()
