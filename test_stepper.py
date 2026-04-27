"""
Test 2 stepper Autonics A16K-M569 + 2 driver MD5-HD14 qua PC817 4-kenh
+ limit switch.

KICH BAN:
  - Voi moi motor: quay CW cho den khi cham limit -> dung
                   quay CCW cho den khi cham limit -> dung
                   in tong so step di duoc.
  - Cham vao bat ky limit nao se DUNG NGAY motor tuong ung.

Chay: python test_stepper.py
Ctrl+C de huy.

CHON MOTOR DE TEST:
    python test_stepper.py        -> test ca 2 motor
    python test_stepper.py 1      -> chi test motor 1 (PAN)
    python test_stepper.py 2      -> chi test motor 2 (TILT)
"""
import sys
import time
from stepper import Stepper
from config import (
    PIN_M1_CW, PIN_M1_CCW, PIN_M1_LIMIT_CW, PIN_M1_LIMIT_CCW,
    PIN_M2_CW, PIN_M2_CCW, PIN_M2_LIMIT_CW, PIN_M2_LIMIT_CCW,
    STEPPER_PULSE_HIGH, STEPPER_PULSE_LOW, STEPPER_STEP_DEG,
)


def make(name, cw, ccw, lcw, lccw):
    return Stepper(name, cw, ccw, lcw, lccw,
                   pulse_high=STEPPER_PULSE_HIGH,
                   pulse_low=STEPPER_PULSE_LOW,
                   step_deg=STEPPER_STEP_DEG)


def print_status(motor):
    s = motor.status()
    lc = s["limit_cw_triggered"]
    la = s["limit_ccw_triggered"]
    lc_str = "TRIGGERED" if lc else ("open" if lc is False else "khong cau hinh")
    la_str = "TRIGGERED" if la else ("open" if la is False else "khong cau hinh")
    print(f"  {motor.name}: position={s['position_steps']} steps "
          f"({s['position_deg']:.1f} deg) | limit CW={lc_str} | limit CCW={la_str}")


def test_one_motor(motor, max_steps=8000):
    print(f"\n{'='*55}")
    print(f" TEST MOTOR: {motor.name}")
    print(f"{'='*55}")
    print_status(motor)

    if motor.is_blocked(+1) and motor.is_blocked(-1):
        print(f"  [!] Ca hai limit cua {motor.name} dang trigger - bo qua.")
        return

    print(f"\n  >>> Quay {motor.name} CW (toi da {max_steps} steps)...")
    n_cw = 0
    while n_cw < max_steps and motor.step(+1):
        n_cw += 1
        if n_cw % 200 == 0:
            print(f"      ...{n_cw} steps ({n_cw * motor.step_deg:.1f} deg)")
    if n_cw >= max_steps:
        print(f"  >>> Het max_steps ({max_steps}) ma chua cham limit CW.")
    else:
        print(f"  >>> CHAM LIMIT CW sau {n_cw} steps.")

    time.sleep(0.5)

    print(f"\n  >>> Quay {motor.name} CCW (toi da {max_steps} steps)...")
    n_ccw = 0
    while n_ccw < max_steps and motor.step(-1):
        n_ccw += 1
        if n_ccw % 200 == 0:
            print(f"      ...{n_ccw} steps ({n_ccw * motor.step_deg:.1f} deg)")
    if n_ccw >= max_steps:
        print(f"  >>> Het max_steps ({max_steps}) ma chua cham limit CCW.")
    else:
        print(f"  >>> CHAM LIMIT CCW sau {n_ccw} steps.")

    print(f"\n  KET QUA {motor.name}: CW={n_cw} steps, CCW={n_ccw} steps "
          f"(khoang {max(n_cw, n_ccw) * motor.step_deg:.1f} deg)")


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else None

    motors = []
    if arg in (None, "1"):
        motors.append(make("PAN (M1)",
                           PIN_M1_CW, PIN_M1_CCW,
                           PIN_M1_LIMIT_CW, PIN_M1_LIMIT_CCW))
    if arg in (None, "2"):
        motors.append(make("TILT (M2)",
                           PIN_M2_CW, PIN_M2_CCW,
                           PIN_M2_LIMIT_CW, PIN_M2_LIMIT_CCW))

    print("Khoi tao xong cac motor:")
    for m in motors:
        print_status(m)

    try:
        input("\nNhan ENTER de bat dau test (Ctrl+C de huy)...")
        for m in motors:
            test_one_motor(m)
    except KeyboardInterrupt:
        print("\n[!] DUNG KHAN CAP.")
    finally:
        for m in motors:
            m.cleanup()
        print("\nCleanup done.")


if __name__ == "__main__":
    main()
