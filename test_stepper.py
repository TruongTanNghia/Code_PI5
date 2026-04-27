"""
Test 2 stepper Autonics A16K-M569 + 2 driver MD5-HD14
qua module PC817 4-kenh + 4 cong tac hanh trinh NC.

KICH BAN:
  Voi moi motor:
    1. Quay CW (toi MAX) cho den khi cham limit MAX -> dung
    2. Quay CCW (toi MIN) cho den khi cham limit MIN -> dung
    3. Bao cao tong so step di duoc

Cham vao bat ky cong tac nao se DUNG NGAY motor tuong ung.

Chay:
    python test_stepper.py        # test ca 2 motor
    python test_stepper.py 1      # chi motor 1 (PAN)
    python test_stepper.py 2      # chi motor 2 (TILT)
"""
import sys
import time
from stepper import Stepper
from config import (
    PIN_M1_CW, PIN_M1_CCW, PIN_M1_LIMIT_MIN, PIN_M1_LIMIT_MAX,
    PIN_M2_CW, PIN_M2_CCW, PIN_M2_LIMIT_MIN, PIN_M2_LIMIT_MAX,
    SWITCH_NC,
    STEPPER_PULSE_HIGH, STEPPER_PULSE_LOW, STEPPER_STEP_DEG,
)


def make(name, cw, ccw, lmin, lmax):
    return Stepper(name, cw, ccw,
                   pin_limit_min=lmin,
                   pin_limit_max=lmax,
                   switch_nc=SWITCH_NC,
                   pulse_high=STEPPER_PULSE_HIGH,
                   pulse_low=STEPPER_PULSE_LOW,
                   step_deg=STEPPER_STEP_DEG)


def fmt_lim(state):
    if state is None: return "khong cau hinh"
    return "TRIGGERED" if state else "tha (chua cham)"


def print_status(motor):
    s = motor.status()
    print(f"  {motor.name}: position={s['position_steps']} steps "
          f"({s['position_deg']:.1f} deg)")
    print(f"     limit MIN: {fmt_lim(s['limit_min_triggered'])}")
    print(f"     limit MAX: {fmt_lim(s['limit_max_triggered'])}")


def test_one(motor, max_steps=8000):
    print(f"\n{'='*55}")
    print(f"  TEST {motor.name}")
    print('='*55)
    print_status(motor)

    if motor.is_blocked(+1) and motor.is_blocked(-1):
        print(f"  [!] CA HAI cong tac cua {motor.name} dang trigger.")
        print(f"      Co the cong tac chua noi day, hoac SWITCH_NC sai.")
        return

    # Quay CW -> MAX
    print(f"\n  >>> Quay {motor.name} CW (-> MAX, max {max_steps} steps)...")
    n_cw = 0
    while n_cw < max_steps and motor.step(+1):
        n_cw += 1
        if n_cw % 200 == 0:
            print(f"      ...{n_cw} steps ({n_cw * motor.step_deg:.1f} deg)")
    print(f"      DUNG: {n_cw} steps "
          f"({'cham LIMIT MAX' if n_cw < max_steps else 'het max_steps'})")

    time.sleep(0.5)

    # Quay CCW -> MIN
    print(f"\n  >>> Quay {motor.name} CCW (-> MIN, max {max_steps} steps)...")
    n_ccw = 0
    while n_ccw < max_steps and motor.step(-1):
        n_ccw += 1
        if n_ccw % 200 == 0:
            print(f"      ...{n_ccw} steps ({n_ccw * motor.step_deg:.1f} deg)")
    print(f"      DUNG: {n_ccw} steps "
          f"({'cham LIMIT MIN' if n_ccw < max_steps else 'het max_steps'})")

    print(f"\n  KET QUA {motor.name}: CW={n_cw} steps, CCW={n_ccw} steps "
          f"= ~{max(n_cw, n_ccw) * motor.step_deg:.1f} deg hanh trinh")


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else None

    motors = []
    if arg in (None, "1"):
        motors.append(make("PAN  (M1)",
                           PIN_M1_CW, PIN_M1_CCW,
                           PIN_M1_LIMIT_MIN, PIN_M1_LIMIT_MAX))
    if arg in (None, "2"):
        motors.append(make("TILT (M2)",
                           PIN_M2_CW, PIN_M2_CCW,
                           PIN_M2_LIMIT_MIN, PIN_M2_LIMIT_MAX))

    print(f"Loai cong tac: {'NC (Normally Closed)' if SWITCH_NC else 'NO (Normally Open)'}")
    print("Khoi tao xong:")
    for m in motors:
        print_status(m)

    try:
        input("\nNhan ENTER de bat dau test (Ctrl+C de huy)...")
        for m in motors:
            test_one(m)
    except KeyboardInterrupt:
        print("\n[!] DUNG KHAN CAP.")
    finally:
        for m in motors:
            m.cleanup()
        print("\nCleanup done.")


if __name__ == "__main__":
    main()
