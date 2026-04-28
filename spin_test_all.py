"""
THU 4 KIEU XUNG khac nhau - tim kieu nao motor quay duoc.

Kich ban: 4 pattern lien tiep, moi pattern 30 xung, in ro ten pattern.
Anh nhin (hoac so) truc motor xem pattern nao no quay/rung.

Cach dung:
    python spin_test_all.py        # motor 1 (M1 CW = GPIO17)
    python spin_test_all.py 2      # motor 2 (M2 CW = GPIO22)
"""
import sys
import time
from gpiozero import OutputDevice
from gpiozero.pins.lgpio import LGPIOFactory
from gpiozero import Device
Device.pin_factory = LGPIOFactory()

from config import PIN_M1_CW, PIN_M2_CW

motor = sys.argv[1] if len(sys.argv) > 1 else "1"
PIN = PIN_M1_CW if motor == "1" else PIN_M2_CW

pin = OutputDevice(PIN, initial_value=False)

PATTERNS = [
    # (ten, idle_state, on_time, off_time, polarity)
    ("Pattern 1: HIGH 50ms + LOW 150ms (NORMAL - dang chay)",
     False, 0.05, 0.15, "high"),
    ("Pattern 2: LOW 50ms + HIGH 150ms (INVERTED)",
     True, 0.05, 0.15, "low"),
    ("Pattern 3: HIGH 1ms + LOW 199ms (XUNG NGAN normal)",
     False, 0.001, 0.199, "high"),
    ("Pattern 4: LOW 1ms + HIGH 199ms (XUNG NGAN inverted)",
     True, 0.001, 0.199, "low"),
]


def run_pattern(name, idle, on_time, off_time, polarity, n_steps=30):
    print()
    print("=" * 60)
    print(f"  {name}")
    print("=" * 60)
    print(f"  - Idle state: {'HIGH' if idle else 'LOW'}")
    print(f"  - Active: {polarity.upper()} for {on_time*1000:.0f}ms")
    print(f"  - Inactive: {(1.0/((on_time+off_time))):.1f} step/giay")
    print()

    # Set idle state
    if idle:
        pin.on()
    else:
        pin.off()
    time.sleep(0.5)  # let signal stabilize

    for i in range(1, n_steps + 1):
        if polarity == "high":
            pin.on()
            time.sleep(on_time)
            pin.off()
        else:
            pin.off()
            time.sleep(on_time)
            pin.on()
        time.sleep(off_time)
        print(f"    >>> step {i}/{n_steps}", end="\r", flush=True)

    print(f"    >>> DA XONG {n_steps} step.            ")
    # Reset to LOW idle
    pin.off()
    time.sleep(0.3)


def main():
    print()
    print("##" * 30)
    print(f"  THU 4 KIEU XUNG tren MOTOR {motor} (GPIO{PIN})")
    print("##" * 30)
    print()
    print("HUONG DAN:")
    print("  - Dan bang keo / sticker len truc motor")
    print("  - So tay nhe vao truc motor (de cam neu no rung)")
    print("  - Mot trong 4 pattern PHAI lam motor quay/rung")
    print("  - Pattern nao thanh cong, em sua code theo pattern do")
    print()
    input("Nhan ENTER de bat dau test 4 pattern...")

    try:
        for name, idle, on_t, off_t, pol in PATTERNS:
            run_pattern(name, idle, on_t, off_t, pol)
            input(f"\n>>> Motor co quay/rung trong pattern nay khong? "
                  "Nhan ENTER de thu pattern tiep theo...")

        print()
        print("=" * 60)
        print("  XONG. Tom tat:")
        print("=" * 60)
        print()
        print("Pattern nao motor QUAY/RUNG -> bao em pattern so may.")
        print("Em se sua spin.py va test_stepper.py theo pattern do.")
        print()
        print("Neu KHONG pattern nao quay duoc -> van de o cho khac:")
        print("  - HOLD OFF dang kich (truc motor xoay tu do = bi)")
        print("  - PC817 OUT khong thuc su noi voi driver CW-")
        print("  - DIP 1/2 CLK dat sai mode")

    except KeyboardInterrupt:
        print("\n\nDUNG (Ctrl+C).")
    finally:
        pin.off()
        pin.close()


if __name__ == "__main__":
    main()
