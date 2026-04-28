"""
TEST 4 KENH PC817 - DON GIAN NHAT.

Cach dung:
    python spin.py 1            # kenh U1, 200 step/s (default - thay motor xoay ro)
    python spin.py 1 500        # kenh U1, 500 step/s (rat nhanh)
    python spin.py 1 50         # kenh U1, 50 step/s (cham, de quan sat LED)
    python spin.py 1 5          # kenh U1, 5 step/s (cuc cham)

Kenh:
    1 = U1 (driver1 CW  - motor1 thuan)
    2 = U2 (driver1 CCW - motor1 nguoc)
    3 = U3 (driver2 CW  - motor2 thuan)
    4 = U4 (driver2 CCW - motor2 nguoc)
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

CHANNELS = {
    "1": (PIN_M1_CW,  "U1", "Driver 1 - CW  (motor 1 thuan)"),
    "2": (PIN_M1_CCW, "U2", "Driver 1 - CCW (motor 1 nguoc)"),
    "3": (PIN_M2_CW,  "U3", "Driver 2 - CW  (motor 2 thuan)"),
    "4": (PIN_M2_CCW, "U4", "Driver 2 - CCW (motor 2 nguoc)"),
}

ch = sys.argv[1] if len(sys.argv) > 1 else "1"
sps = int(sys.argv[2]) if len(sys.argv) > 2 else 200  # mac dinh 200 step/s

if ch not in CHANNELS:
    print(f"Sai tham so. Dung: python spin.py [1|2|3|4] [step/giay]")
    sys.exit(1)

PIN, U_NAME, DESC = CHANNELS[ch]

# Tinh chu ky xung tu sps (step per second)
half = 0.5 / sps
PULSE_HIGH = half
PULSE_LOW  = half

pin = OutputDevice(PIN, initial_value=False)

print()
print("=" * 55)
print(f"  TEST KENH {ch} -> PC817 {U_NAME}")
print("=" * 55)
print(f"  Pi GPIO: {PIN}")
print(f"  PC817:   IN{ch} -> {U_NAME}")
print(f"  {DESC}")
print(f"  Toc do: {sps} step/giay = {sps * 0.72:.1f} deg/giay "
      f"= {sps * 0.72 / 360:.1f} vong/giay")
print(f"  Xung: {PULSE_HIGH*1000:.1f}ms HIGH + {PULSE_LOW*1000:.1f}ms LOW")
print()
print("Ctrl+C de dung.")
print()

count = 0
t_start = time.time()
last_print = 0

try:
    while True:
        pin.on()
        time.sleep(PULSE_HIGH)
        pin.off()
        time.sleep(PULSE_LOW)
        count += 1

        # In trang thai moi 0.3s (de khong spam terminal)
        now = time.time()
        if now - last_print >= 0.3:
            elapsed = now - t_start
            print(f"  KENH {ch} ({U_NAME})  STEP {count:6d}  "
                  f"|  goc tich luy: {count * 0.72:8.1f} deg "
                  f"({count * 0.72 / 360:.2f} vong)  "
                  f"|  {elapsed:5.1f}s", flush=True)
            last_print = now

except KeyboardInterrupt:
    elapsed = time.time() - t_start
    print()
    print(f"\nDA DUNG.")
    print(f"  Tong: {count} step ({count * 0.72:.1f} deg = "
          f"{count * 0.72 / 360:.2f} vong)")
    print(f"  Thoi gian: {elapsed:.1f}s")
    print(f"  Toc do thuc te: {count/elapsed:.0f} step/giay")

finally:
    pin.off()
    pin.close()
