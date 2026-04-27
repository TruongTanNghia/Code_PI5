import time
from config import (
    PAN_CHANNEL, TILT_CHANNEL,
    PAN_MIN, PAN_MAX, TILT_MIN, TILT_MAX,
)


class ServoController:
    def __init__(self):
        self.pan_angle = 90
        self.tilt_angle = 90
        self.pca = None
        self._mock = False

        try:
            import board
            import busio
            from adafruit_pca9685 import PCA9685

            i2c = busio.I2C(board.SCL, board.SDA)
            self.pca = PCA9685(i2c)
            self.pca.frequency = 50
            print("[SERVO] PCA9685 ket noi OK (I2C 0x40)")
        except (ImportError, ValueError, OSError) as e:
            print(f"[SERVO] Khong tim thay PCA9685 ({e}). Chay MOCK mode (in goc ra terminal).")
            self._mock = True

        self.set_pan(self.pan_angle)
        self.set_tilt(self.tilt_angle)
        time.sleep(0.3)

    @staticmethod
    def angle_to_duty(angle):
        return int((500 + angle * 2000 / 180) / 20000 * 65535)

    def set_pan(self, angle):
        angle = max(PAN_MIN, min(PAN_MAX, angle))
        self.pan_angle = angle
        if self._mock:
            return
        self.pca.channels[PAN_CHANNEL].duty_cycle = self.angle_to_duty(angle)

    def set_tilt(self, angle):
        angle = max(TILT_MIN, min(TILT_MAX, angle))
        self.tilt_angle = angle
        if self._mock:
            return
        self.pca.channels[TILT_CHANNEL].duty_cycle = self.angle_to_duty(angle)
