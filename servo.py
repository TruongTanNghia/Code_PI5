import time
import board
import busio
from adafruit_pca9685 import PCA9685
from config import *

class ServoController:
    def __init__(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.pca = PCA9685(i2c)
        self.pca.frequency = 50

        self.pan_angle = 90
        self.tilt_angle = 90

        self.set_pan(self.pan_angle)
        self.set_tilt(self.tilt_angle)
        time.sleep(0.5)

    def angle_to_duty(self, angle):
        return int((500 + angle * 2000 / 180) / 20000 * 65535)

    def set_pan(self, angle):
        angle = max(PAN_MIN, min(PAN_MAX, angle))
        self.pan_angle = angle
        self.pca.channels[PAN_CHANNEL].duty_cycle = self.angle_to_duty(angle)

    def set_tilt(self, angle):
        angle = max(TILT_MIN, min(TILT_MAX, angle))
        self.tilt_angle = angle
        self.pca.channels[TILT_CHANNEL].duty_cycle = self.angle_to_duty(angle)
