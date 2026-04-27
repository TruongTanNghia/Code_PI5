import time
import threading
from config import LASER_PIN, LASER_BURST_TIME, LASER_COOLDOWN

try:
    # Pi5 dung lgpio backend (RPi.GPIO khong chay duoc tren Pi5)
    from gpiozero import LED
    from gpiozero.pins.lgpio import LGPIOFactory
    from gpiozero import Device
    Device.pin_factory = LGPIOFactory()
    _GPIO_OK = True
except Exception as e:
    print(f"[LASER] gpiozero/lgpio khong san sang ({e}). Chay che do MOCK (in ra terminal).")
    _GPIO_OK = False


class LaserController:
    def __init__(self):
        self._lock = threading.Lock()
        self._last_fire_end = 0.0
        self._busy = False

        if _GPIO_OK:
            self.led = LED(LASER_PIN)
            self.led.off()
        else:
            self.led = None

    def _set(self, on: bool):
        if self.led is not None:
            if on:
                self.led.on()
            else:
                self.led.off()
        else:
            print(f"[LASER MOCK] {'ON' if on else 'OFF'}")

    def can_fire(self) -> bool:
        if self._busy:
            return False
        return (time.time() - self._last_fire_end) >= LASER_COOLDOWN

    def fire_burst(self):
        """Ban 1 phat ngan trong thread rieng (khong block vong lap chinh)."""
        if not self.can_fire():
            return False

        def _job():
            with self._lock:
                self._busy = True
                self._set(True)
                time.sleep(LASER_BURST_TIME)
                self._set(False)
                self._last_fire_end = time.time()
                self._busy = False

        threading.Thread(target=_job, daemon=True).start()
        return True

    def is_firing(self) -> bool:
        return self._busy

    def cleanup(self):
        try:
            self._set(False)
            if self.led is not None:
                self.led.close()
        except Exception:
            pass
