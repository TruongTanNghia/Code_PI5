"""
TEST 4 KENH PC817 - DON GIAN NHAT.

Phat xung 5 step/giay vao 1 chan, chay den khi Ctrl+C.

Cach dung:
    python spin.py 1     # test kenh U1 (GPIO17 -> IN1 -> U1 -> driver1 CW-)
    python spin.py 2     # test kenh U2 (GPIO27 -> IN2 -> U2 -> driver1 CCW-)
    python spin.py 3     # test kenh U3 (GPIO22 -> IN3 -> U3 -> driver2 CW-)
    python spin.py 4     # test kenh U4 (GPIO23 -> IN4 -> U4 -> driver2 CCW-)

Mac dinh (khong tham so) la kenh 1.
"""
import sys
import time
from gpiozero import OutputDevice
from gpiozero.pins.lgpio import LGPIOFactory
from gpiozero import Device
Device.pin_factory = LGPIOFactory()

from config import (
    PIN_M1_CW, PIN_M1_CCW,
    PIN_M2_CW, PIN_M2_CCW,
)

# Mapping: so kenh -> (GPIO, ten, mo ta)
CHANNELS = {
    "1": (PIN_M1_CW,  "U1", "Driver 1 - CW  (motor 1 quay thuan)"),
    "2": (PIN_M1_CCW, "U2", "Driver 1 - CCW (motor 1 quay nguoc)"),
    "3": (PIN_M2_CW,  "U3", "Driver 2 - CW  (motor 2 quay thuan)"),
    "4": (PIN_M2_CCW, "U4", "Driver 2 - CCW (motor 2 quay nguoc)"),
}

ch = sys.argv[1] if len(sys.argv) > 1 else "1"
if ch not in CHANNELS:
    print(f"Sai tham so. Dung: python spin.py [1|2|3|4]")
    print(f"  1 = kenh U1 (motor 1 thuan)")
    print(f"  2 = kenh U2 (motor 1 nguoc)")
    print(f"  3 = kenh U3 (motor 2 thuan)")
    print(f"  4 = kenh U4 (motor 2 nguoc)")
    sys.exit(1)

PIN, U_NAME, DESC = CHANNELS[ch]

# Xung 50ms HIGH + 150ms LOW = 5 step/giay
PULSE_HIGH = 0.05
PULSE_LOW  = 0.15

pin = OutputDevice(PIN, initial_value=False)

print()
print("=" * 55)
print(f"  TEST KENH {ch} -> PC817 {U_NAME}")
print("=" * 55)
print(f"  Pi GPIO: {PIN}")
print(f"  PC817:   IN{ch} -> {U_NAME}")
print(f"  {DESC}")
print(f"  Xung: 50ms HIGH + 150ms LOW = 5 step/giay")
print()
print("KIEM TRA:")
print(f"  1. LED PC817 kenh {ch} co nhay khong?")
print(f"  2. Motor (cua driver tuong ung) co quay khong?")
print()
print("Ctrl+C de dung.")
print()

count = 0
t_start = time.time()
try:
    while True:
        pin.on()
        time.sleep(PULSE_HIGH)
        pin.off()
        count += 1
        elapsed = time.time() - t_start
        print(f"  >>> KENH {ch} ({U_NAME})  STEP {count:4d}  "
              f"|  goc: {count * 0.72:7.1f} deg  "
              f"|  thoi gian: {elapsed:5.1f}s  <<<", flush=True)
        time.sleep(PULSE_LOW)

except KeyboardInterrupt:
    print()
    print(f"\nDA DUNG. Tong: {count} step ({count * 0.72:.1f} deg) "
          f"trong {time.time() - t_start:.1f} giay.")

finally:
    pin.off()
    pin.close()
