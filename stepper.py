"""
Class dieu khien stepper Autonics A16K-M569 + driver MD5-HD14
qua module PC817 4-kenh (cach ly + buffer).

LUU Y VE PC817:
- Pi GPIO HIGH -> LED PC817 sang -> transistor dan -> CW-/CCW- ve GND
  -> driver thay 1 xung -> motor di 1 buoc.
- Tin hieu khong bi nguoc (HIGH on Pi = pulse on driver).

LIMIT SWITCH:
- COM -> GND, NO -> GPIO (code bat pull_up=True)
- Tha = HIGH; Cham = LOW => `is_pressed = True`.
- Khi triggered, ham step() khong phat xung, tra ve False.
"""
import time
from gpiozero import OutputDevice, Button
from gpiozero.pins.lgpio import LGPIOFactory
from gpiozero import Device

# Set 1 lan duy nhat cho ca process (an toan neu goi nhieu lan)
if not isinstance(Device.pin_factory, LGPIOFactory):
    Device.pin_factory = LGPIOFactory()


class Stepper:
    def __init__(self, name, pin_cw, pin_ccw,
                 pin_limit_cw=None, pin_limit_ccw=None,
                 pulse_high=0.0005, pulse_low=0.0005, step_deg=0.72):
        self.name = name
        self.cw = OutputDevice(pin_cw, initial_value=False)
        self.ccw = OutputDevice(pin_ccw, initial_value=False)
        self.limit_cw = (Button(pin_limit_cw, pull_up=True, bounce_time=0.02)
                         if pin_limit_cw is not None else None)
        self.limit_ccw = (Button(pin_limit_ccw, pull_up=True, bounce_time=0.02)
                          if pin_limit_ccw is not None else None)
        self.pulse_high = pulse_high
        self.pulse_low = pulse_low
        self.step_deg = step_deg
        self.position = 0  # so step ke tu khi khoi tao (CW = +, CCW = -)

    def is_blocked(self, direction):
        if direction > 0 and self.limit_cw is not None and self.limit_cw.is_pressed:
            return True
        if direction < 0 and self.limit_ccw is not None and self.limit_ccw.is_pressed:
            return True
        return False

    def step(self, direction):
        """Phat 1 xung. Tra ve False neu cham limit (khong phat)."""
        if self.is_blocked(direction):
            return False
        pin = self.cw if direction > 0 else self.ccw
        pin.on()
        time.sleep(self.pulse_high)
        pin.off()
        time.sleep(self.pulse_low)
        self.position += 1 if direction > 0 else -1
        return True

    def rotate_steps(self, n_steps):
        """Quay n_steps. n_steps duong = CW, am = CCW. Tra ve so step thuc te di duoc."""
        direction = 1 if n_steps > 0 else -1
        target = abs(int(n_steps))
        done = 0
        for _ in range(target):
            if not self.step(direction):
                break
            done += 1
        return done * direction

    def rotate_degrees(self, deg):
        """Quay theo do (xap xi). Duong = CW, am = CCW."""
        steps = int(round(deg / self.step_deg))
        return self.rotate_steps(steps) * self.step_deg

    def home(self, direction=-1, max_steps=20000):
        """Quay den khi cham limit, set position = 0."""
        count = 0
        while count < max_steps and self.step(direction):
            count += 1
        self.position = 0
        return count

    def status(self):
        return {
            "name": self.name,
            "position_steps": self.position,
            "position_deg": self.position * self.step_deg,
            "limit_cw_triggered": self.limit_cw.is_pressed if self.limit_cw else None,
            "limit_ccw_triggered": self.limit_ccw.is_pressed if self.limit_ccw else None,
        }

    def stop(self):
        self.cw.off()
        self.ccw.off()

    def cleanup(self):
        self.stop()
        try:
            self.cw.close(); self.ccw.close()
            if self.limit_cw: self.limit_cw.close()
            if self.limit_ccw: self.limit_ccw.close()
        except Exception:
            pass
