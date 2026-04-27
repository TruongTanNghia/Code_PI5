"""
Test motor + limit switch tich hop - CHE DO AN TOAN.

- Mac dinh chay CHAM (100 step/s = ~72 deg/s) de anh kip phan ung.
- Quay qua lai MIN <-> MAX, in vi tri + trang thai limit live.
- Cham limit -> motor DUNG NGAY -> dao chieu.
- Tu dong bao ve neu motor thieu limit (chi quay 1 chieu).

Cach dung:
    python test_stepper.py            # ca 2 motor, 100 step/s
    python test_stepper.py 1          # chi motor 1
    python test_stepper.py 2          # chi motor 2
    python test_stepper.py 1 50       # motor 1, RAT cham (50 step/s)
    python test_stepper.py 1 100 3    # motor 1, 100 step/s, 3 chu ky qua lai

Ctrl+C de DUNG KHAN CAP bat ky luc nao.
"""
import sys
import time
from stepper import Stepper
from config import (
    PIN_M1_CW, PIN_M1_CCW, PIN_M1_LIMIT_MIN, PIN_M1_LIMIT_MAX,
    PIN_M2_CW, PIN_M2_CCW, PIN_M2_LIMIT_MIN, PIN_M2_LIMIT_MAX,
    SWITCH_NC, STEPPER_STEP_DEG, STEPPER_TEST_SPS,
)


def make(name, cw, ccw, lmin, lmax, sps):
    half = 0.5 / sps  # nua chu ky -> high va low bang nhau
    return Stepper(name, cw, ccw,
                   pin_limit_min=lmin, pin_limit_max=lmax,
                   switch_nc=SWITCH_NC,
                   pulse_high=half, pulse_low=half,
                   step_deg=STEPPER_STEP_DEG)


def fmt_lim(state):
    if state is None: return "(none)"
    return "[CHAM]" if state else " tha "


def print_live(motor, direction):
    s = motor.status()
    arrow = "CW->MAX" if direction > 0 else "CCW->MIN"
    print(f"\r  {motor.name}  pos={motor.position:>5}  "
          f"({motor.position * motor.step_deg:>+7.1f} deg)  "
          f"{arrow}  "
          f"MIN={fmt_lim(s['limit_min_triggered'])}  "
          f"MAX={fmt_lim(s['limit_max_triggered'])}",
          end="", flush=True)


def rotate_one_pass(motor, direction, max_steps=15000):
    """Quay 1 chieu cho den khi cham limit hoac het max_steps. Tra ve so step."""
    n = 0
    while n < max_steps:
        if not motor.step(direction):
            return n, "limit"
        n += 1
        if n % 25 == 0:
            print_live(motor, direction)
    return n, "max_steps"


def safe_test_motor(motor, n_cycles=5, max_steps=15000):
    has_min = motor.limit_min is not None
    has_max = motor.limit_max is not None
    s0 = motor.status()
    init_min = s0["limit_min_triggered"]
    init_max = s0["limit_max_triggered"]

    print(f"\n{'='*60}")
    print(f" TEST {motor.name}")
    print(f"{'='*60}")
    print(f"  limit MIN: {'co cau hinh' if has_min else 'KHONG'}  -> {fmt_lim(init_min)}")
    print(f"  limit MAX: {'co cau hinh' if has_max else 'KHONG'}  -> {fmt_lim(init_max)}")

    # An toan: bo qua chieu khong co limit
    if not has_min and not has_max:
        print(f"  [!] {motor.name} khong co limit nao -> bo qua test (qua nguy hiem)")
        return

    if has_min and has_max and init_min and init_max:
        print(f"  [!] CA HAI limit dang trigger - bo qua.")
        return

    only_dir = None
    if not has_max or init_max:
        only_dir = -1
        print(f"  [!] Khong test duoc chieu CW (limit MAX thieu/dang trigger).")
        print(f"      Chi quay CCW -> MIN.")
    elif not has_min or init_min:
        only_dir = +1
        print(f"  [!] Khong test duoc chieu CCW (limit MIN thieu/dang trigger).")
        print(f"      Chi quay CW -> MAX.")

    # Quay 1 chieu
    if only_dir is not None:
        print(f"\n  >>> Quay 1 chieu, max {max_steps} steps...")
        n, reason = rotate_one_pass(motor, only_dir, max_steps)
        print()
        print(f"  Dung: {n} steps ({reason})")
        return

    # Du 2 limit -> qua lai n_cycles vong
    print(f"\n  >>> Quay qua lai MIN <-> MAX, {n_cycles} chu ky...")
    direction = +1  # bat dau CW
    for cycle in range(1, n_cycles * 2 + 1):  # 1 chu ky = 2 luot
        leg = "CW" if direction > 0 else "CCW"
        print(f"\n  [Chu ky {(cycle+1)//2}/{n_cycles}] Luot {leg}...")
        n, reason = rotate_one_pass(motor, direction, max_steps)
        print()
        print(f"     => {leg} dung sau {n} steps ({reason})")
        if reason == "max_steps":
            print(f"     [!] Khong cham limit sau {max_steps} steps - dung de an toan.")
            return
        time.sleep(0.5)
        direction = -direction

    print(f"\n  XONG {motor.name}: hoan tat {n_cycles} chu ky.")


def main():
    arg_motor = sys.argv[1] if len(sys.argv) > 1 else None
    sps = int(sys.argv[2]) if len(sys.argv) > 2 else STEPPER_TEST_SPS
    n_cycles = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    print(f"Toc do test: {sps} step/s ({sps * STEPPER_STEP_DEG:.1f} deg/s)")
    print(f"So chu ky qua lai: {n_cycles}")
    print(f"Loai cong tac: {'NC' if SWITCH_NC else 'NO'}")

    motors = []
    if arg_motor in (None, "1"):
        motors.append(make("PAN  (M1)",
                           PIN_M1_CW, PIN_M1_CCW,
                           PIN_M1_LIMIT_MIN, PIN_M1_LIMIT_MAX, sps))
    if arg_motor in (None, "2"):
        motors.append(make("TILT (M2)",
                           PIN_M2_CW, PIN_M2_CCW,
                           PIN_M2_LIMIT_MIN, PIN_M2_LIMIT_MAX, sps))

    print("\nKhoi tao xong:")
    for m in motors:
        s = m.status()
        print(f"  {m.name}: MIN={fmt_lim(s['limit_min_triggered'])}  "
              f"MAX={fmt_lim(s['limit_max_triggered'])}")

    print("\nLuu y AN TOAN:")
    print("  - Cham vao limit switch tay = motor dung ngay -> dao chieu")
    print("  - Ctrl+C bat ky luc nao = motor dung khan cap")
    print("  - Neu motor dung va khong dao chieu -> kiem tra dau noi")

    try:
        input("\nNhan ENTER de bat dau (Ctrl+C de huy)...")
        for m in motors:
            safe_test_motor(m, n_cycles=n_cycles)
    except KeyboardInterrupt:
        print("\n\n[!] DUNG KHAN CAP (Ctrl+C).")
    finally:
        for m in motors:
            m.cleanup()
        print("\nCleanup done.")


if __name__ == "__main__":
    main()
