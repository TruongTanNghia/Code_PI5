"""
Test 4 cong tac hanh trinh - LIVE MONITOR + CHECKLIST.

Khong quay motor. Treo chay vinh vien, anh bam tung cong tac de verify.

Cach dung:
    python test_switches.py

Banner se hien "ALL SWITCHES VERIFIED" khi ca 4 cai deu da duoc bam
va tha it nhat 1 lan -> an toan de chay motor.

Ctrl+C de thoat.
"""
import os
import sys
import time
from gpiozero import Button
from gpiozero.pins.lgpio import LGPIOFactory
from gpiozero import Device
Device.pin_factory = LGPIOFactory()

from config import (
    PIN_M1_LIMIT_MIN, PIN_M1_LIMIT_MAX,
    PIN_M2_LIMIT_MIN, PIN_M2_LIMIT_MAX,
    SWITCH_NC,
)


class SwitchProbe:
    def __init__(self, name, pin):
        self.name = name
        self.pin = pin
        self.button = Button(pin, pull_up=True, bounce_time=0.02) if pin is not None else None
        self.press_count = 0     # so lan da bam
        self.release_count = 0   # so lan da tha
        self.last_state = None   # trang thai gan nhat (True=cham)

    def is_triggered(self):
        """NC: cham = HIGH = is_pressed False"""
        if self.button is None:
            return None
        return (not self.button.is_pressed) if SWITCH_NC else self.button.is_pressed

    def update(self):
        """Goi moi loop. Tra ve event neu co thay doi: 'press', 'release', None."""
        cur = self.is_triggered()
        if cur is None:
            return None
        event = None
        if self.last_state is not None:
            if cur and not self.last_state:
                self.press_count += 1
                event = "press"
            elif not cur and self.last_state:
                self.release_count += 1
                event = "release"
        self.last_state = cur
        return event

    @property
    def verified(self):
        """Da bam VA tha it nhat 1 lan thi coi nhu verified."""
        return self.press_count >= 1 and self.release_count >= 1


def clear_screen():
    os.system("clear")


def main():
    probes = [
        SwitchProbe("M1 MIN", PIN_M1_LIMIT_MIN),
        SwitchProbe("M1 MAX", PIN_M1_LIMIT_MAX),
        SwitchProbe("M2 MIN", PIN_M2_LIMIT_MIN),
        SwitchProbe("M2 MAX", PIN_M2_LIMIT_MAX),
    ]

    event_log = []  # 5 event gan nhat

    try:
        while True:
            # Update tat ca probe
            for p in probes:
                ev = p.update()
                if ev:
                    ts = time.strftime("%H:%M:%S")
                    if ev == "press":
                        event_log.append(f"[{ts}] [+] {p.name} BI CHAM (lan thu {p.press_count})")
                    else:
                        event_log.append(f"[{ts}] [-] {p.name} duoc tha")
                    event_log = event_log[-8:]

            # Ve giao dien
            clear_screen()
            print("=" * 60)
            print(" TEST 4 LIMIT SWITCHES — Bam tung cong tac de verify")
            print(f" Loai: {'NC (Normally Closed)' if SWITCH_NC else 'NO (Normally Open)'}")
            print("=" * 60)
            print()
            print(f" {'Switch':<10} {'GPIO':<8} {'Hien tai':<14} {'#Bam':<6} {'#Tha':<6} {'Verify':<10}")
            print(" " + "-" * 56)

            all_verified = True
            for p in probes:
                pin_str = f"GPIO{p.pin}" if p.pin is not None else "(none)"
                if p.button is None:
                    status = "(khong cau hinh)"
                    verify = "-"
                    all_verified = False
                else:
                    cur = p.is_triggered()
                    status = "## CHAM ##" if cur else "....tha...."
                    if p.verified:
                        verify = "[OK] VERIFIED"
                    else:
                        # Hien con thieu gi
                        need = []
                        if p.press_count == 0: need.append("bam")
                        if p.release_count == 0: need.append("tha")
                        verify = "Can: " + "+".join(need)
                        all_verified = False
                print(f" {p.name:<10} {pin_str:<8} {status:<14} {p.press_count:<6} {p.release_count:<6} {verify}")

            print()
            print(" Event log gan nhat:")
            if not event_log:
                print("   (chua co su kien — bam thu 1 cong tac di anh!)")
            else:
                for e in event_log:
                    print(f"   {e}")
            print()

            if all_verified:
                print(" " + "*" * 56)
                print(" *   ALL SWITCHES VERIFIED — AN TOAN DE CHAY MOTOR   *")
                print(" *   Tiep theo: python test_stepper.py               *")
                print(" " + "*" * 56)
            else:
                remaining = sum(1 for p in probes if not p.verified)
                print(f" Con {remaining}/4 switch chua verify. Bam roi tha tung cai.")

            print("\n (Ctrl+C de thoat)")
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\nThoat. Tom tat:")
        for p in probes:
            mark = "[OK]" if p.verified else "[--]"
            print(f"  {mark} {p.name}: {p.press_count} lan bam, {p.release_count} lan tha")


if __name__ == "__main__":
    main()
