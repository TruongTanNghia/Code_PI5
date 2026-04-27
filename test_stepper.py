"""
Test Autonics A16K-M569 (5-phase stepper) + MD5-HD14 driver + 2 limit switches.

KICH BAN TEST:
  1. Quay CW (chieu kim dong ho) cho den khi cham limit switch CW -> dung
  2. Quay nguoc CCW cho den khi cham limit switch CCW -> dung
  3. Bao cao tong so xung di duoc

Chay: python test_stepper.py
Ctrl+C de huy bat ky luc nao.
"""
import time
from gpiozero import OutputDevice, Button
from gpiozero.pins.lgpio import LGPIOFactory
from gpiozero import Device
Device.pin_factory = LGPIOFactory()


# ===== GPIO BCM pin (anh co the doi tuy y) =====
PIN_CW_PULSE = 27       # -> MD5-HD14 chan "CW +" (chan "CW -" noi GND)
PIN_CCW_PULSE = 22      # -> MD5-HD14 chan "CCW +" (chan "CCW -" noi GND)
PIN_LIMIT_CW = 23       # <- Limit switch CW (NO -> GPIO, COM -> GND)
PIN_LIMIT_CCW = 24      # <- Limit switch CCW (NO -> GPIO, COM -> GND)

# ===== Thong so xung (~1kHz, motor quay cham, an toan de test) =====
PULSE_HIGH = 0.0005     # 500us
PULSE_LOW = 0.0005      # 500us -> 1000 steps/giay
STEP_DEG = 0.72         # A16K-M569: 0.72 deg/step (fullstep, chua microstep)


cw_pin = OutputDevice(PIN_CW_PULSE, initial_value=False)
ccw_pin = OutputDevice(PIN_CCW_PULSE, initial_value=False)
# pull_up=True: trang thai mac dinh la HIGH; khi cong tac dong (NO->COM->GND) thi HIGH->LOW
# bounce_time chong rung tiep diem
limit_cw = Button(PIN_LIMIT_CW, pull_up=True, bounce_time=0.02)
limit_ccw = Button(PIN_LIMIT_CCW, pull_up=True, bounce_time=0.02)


def one_step(direction):
    """Phat 1 xung. Tra ve False neu cham limit (khong phat xung)."""
    if direction > 0:
        if limit_cw.is_pressed:
            return False
        cw_pin.on()
        time.sleep(PULSE_HIGH)
        cw_pin.off()
        time.sleep(PULSE_LOW)
    else:
        if limit_ccw.is_pressed:
            return False
        ccw_pin.on()
        time.sleep(PULSE_HIGH)
        ccw_pin.off()
        time.sleep(PULSE_LOW)
    return True


def rotate_until_limit(direction, max_steps=20000):
    name = "CW" if direction > 0 else "CCW"
    print(f"\n[STEPPER] Bat dau quay {name} (toi da {max_steps} steps)...")
    count = 0
    while count < max_steps:
        if not one_step(direction):
            print(f"[STEPPER] >>> DA CHAM LIMIT {name} <<< sau {count} steps "
                  f"(~{count * STEP_DEG:.1f} deg)")
            return count
        count += 1
        if count % 200 == 0:
            print(f"   ... {count} steps (~{count * STEP_DEG:.1f} deg)")
    print(f"[STEPPER] Het max_steps ({max_steps}) ma chua cham limit.")
    return count


def main():
    print("=" * 55)
    print(" Autonics A16K-M569 + MD5-HD14 + Limit switch test")
    print("=" * 55)
    print(f"  CW pulse  -> GPIO{PIN_CW_PULSE}")
    print(f"  CCW pulse -> GPIO{PIN_CCW_PULSE}")
    print(f"  Limit CW  <- GPIO{PIN_LIMIT_CW}")
    print(f"  Limit CCW <- GPIO{PIN_LIMIT_CCW}")
    print()
    print("Trang thai limit switch hien tai:")
    print(f"  CW limit : {'TRIGGERED (dang an)' if limit_cw.is_pressed else 'tha (open)'}")
    print(f"  CCW limit: {'TRIGGERED (dang an)' if limit_ccw.is_pressed else 'tha (open)'}")
    print()

    if limit_cw.is_pressed and limit_ccw.is_pressed:
        print("[!] CA HAI limit dang trigger - kiem tra day noi.")
        print("    Neu khong cam limit: noi GPIO23 va GPIO24 voi 3.3V hoac de pull_up=False.")
        return

    input("Nhan ENTER de bat dau test (Ctrl+C de huy)...")

    try:
        n_cw = rotate_until_limit(+1)
        time.sleep(0.5)
        n_ccw = rotate_until_limit(-1)

        print()
        print("=" * 55)
        print(f" TONG KET:  CW = {n_cw} steps   |   CCW = {n_ccw} steps")
        print(f" Khoang chuyen dong toi da = {max(n_cw, n_ccw) * STEP_DEG:.1f} deg")
        print("=" * 55)

    except KeyboardInterrupt:
        print("\n[!] DUNG KHAN CAP (Ctrl+C)")

    finally:
        cw_pin.off()
        ccw_pin.off()
        print("Cleanup done.")


if __name__ == "__main__":
    main()
