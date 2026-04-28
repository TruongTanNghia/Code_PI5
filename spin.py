"""
QUAY MOTOR - DON GIAN NHAT.

Chi step 1 chieu CW, xung rat rong (50ms), 5 step/giay.
Khong limit switch, khong gi het. Chay den khi Ctrl+C.

Cach dung:
    python spin.py        # motor 1
    python spin.py 2      # motor 2
    python spin.py 1 r    # motor 1, chieu CCW (nguoc)
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

motor = sys.argv[1] if len(sys.argv) > 1 else "1"
direction = sys.argv[2] if len(sys.argv) > 2 else "f"  # f=forward(CW), r=reverse(CCW)

if motor == "1":
    PIN = PIN_M1_CW if direction == "f" else PIN_M1_CCW
    name = f"MOTOR 1 - {'CW' if direction == 'f' else 'CCW'}"
elif motor == "2":
    PIN = PIN_M2_CW if direction == "f" else PIN_M2_CCW
    name = f"MOTOR 2 - {'CW' if direction == 'f' else 'CCW'}"
else:
    print("Usage: python spin.py [1|2] [f|r]")
    sys.exit(1)

# Xung CUC ROng - 50ms HIGH + 150ms LOW = 5 step/giay
PULSE_HIGH = 0.05
PULSE_LOW  = 0.15

pin = OutputDevice(PIN, initial_value=False)

print()
print("=" * 50)
print(f"  {name}  (GPIO{PIN})")
print("=" * 50)
print(f"  Xung HIGH: {PULSE_HIGH*1000:.0f} ms")
print(f"  Xung LOW : {PULSE_LOW*1000:.0f} ms")
print(f"  Toc do: 5 step/giay (~3.6 deg/giay)")
print()
print("KIEM TRA TRUC TIEP:")
print("  1. LED PC817 (kenh tuong ung) PHAI nhay theo nhip 5 lan/giay")
print("  2. LED RUN tren driver MD5-HD14 PHAI nhay theo nhip")
print("  3. Truc motor PHAI quay tu tu (3.6 deg moi giay)")
print()
print("Ctrl+C de dung.")
print()

count = 0
t_start = time.time()
try:
    while True:
        # PHAT XUNG RO RANG
        pin.on()
        time.sleep(PULSE_HIGH)
        pin.off()
        count += 1

        elapsed = time.time() - t_start
        deg = count * 0.72
        print(f"  >>> STEP {count:4d}  |  goc tich luy: {deg:7.1f} deg  "
              f"|  thoi gian: {elapsed:5.1f}s  <<<", flush=True)

        time.sleep(PULSE_LOW)

except KeyboardInterrupt:
    print()
    print(f"\nDA DUNG. Tong: {count} step ({count * 0.72:.1f} deg) trong "
          f"{time.time() - t_start:.1f} giay.")

finally:
    pin.off()
    pin.close()
