"""
Class dieu khien stepper Autonics A16K-M569 + driver MD5-HD14
qua module PC817 4-kenh + cong tac hanh trinh (limit switch).

QUY UOC HUONG:
- CW (clockwise) = quay ve phia MAX
- CCW (counter-cw) = quay ve phia MIN

CONG TAC NC (Normally Closed) - mac dinh, an toan hon:
- Tha     -> COM-NC dong -> GPIO ve GND (LOW) -> coi nhu CHUA cham
- Cham    -> COM-NC mo   -> GPIO float HIGH   -> CHAM (triggered)
- Day dut -> tuong duong "cham" -> motor dung -> sai-an-toan (fail-safe)

CONG TAC NO (Normally Open) - dao lai:
- Tha  -> mo   -> GPIO HIGH (pull-up) -> CHUA cham
- Cham -> dong -> GPIO LOW            -> CHAM
"""
import time
from gpiozero import OutputDevice, Button
from gpiozero.pins.lgpio import LGPIOFactory
from gpiozero import Device

if not isinstance(Device.pin_factory, LGPIOFactory):
    Device.pin_factory = LGPIOFactory()


class Stepper:
    def __init__(self, name, pin_cw, pin_ccw,
                 pin_limit_max=None, pin_limit_min=None,
                 switch_nc=True,
                 pulse_high=0.0005, pulse_low=0.0005, step_deg=0.72):
        self.name = name
        self.cw = OutputDevice(pin_cw, initial_value=False)
        self.ccw = OutputDevice(pin_ccw, initial_value=False)
        self.switch_nc = switch_nc

        # Both NC and NO use pull_up=True. We invert logic for NC.
        self.limit_max = (Button(pin_limit_max, pull_up=True, bounce_time=0.02)
                          if pin_limit_max is not None else None)
        self.limit_min = (Button(pin_limit_min, pull_up=True, bounce_time=0.02)
                          if pin_limit_min is not None else None)

        self.pulse_high = pulse_high
        self.pulse_low = pulse_low
        self.step_deg = step_deg
        self.position = 0  # so step ke tu khoi tao (CW = +, CCW = -)

    def _is_triggered(self, button):
        """True neu cong tac dang bi cham (xet ca NC va NO)."""
        if button is None:
            return False
        if self.switch_nc:
            # NC: tha = LOW = is_pressed True; cham = HIGH = is_pressed False
            return not button.is_pressed
        else:
            # NO: cham = LOW = is_pressed True
            return button.is_pressed

    def is_blocked(self, direction):
        """direction > 0 = CW (toi MAX); direction < 0 = CCW (toi MIN)."""
        if direction > 0:
            return self._is_triggered(self.limit_max)
        else:
            return self._is_triggered(self.limit_min)

    def step(self, direction):
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
        direction = 1 if n_steps > 0 else -1
        target = abs(int(n_steps))
        done = 0
        for _ in range(target):
            if not self.step(direction):
                break
            done += 1
        return done * direction

    def rotate_degrees(self, deg):
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
            "limit_max_triggered": self._is_triggered(self.limit_max) if self.limit_max else None,
            "limit_min_triggered": self._is_triggered(self.limit_min) if self.limit_min else None,
        }

    def stop(self):
        self.cw.off()
        self.ccw.off()

    def cleanup(self):
        self.stop()
        try:
            self.cw.close(); self.ccw.close()
            if self.limit_max: self.limit_max.close()
            if self.limit_min: self.limit_min.close()
        except Exception:
            pass
