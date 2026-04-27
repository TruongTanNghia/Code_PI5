"""
Test 4 cong tac hanh trinh - HIEN TRANG THAI LIVE.
Khong quay motor.

Cach dung:
    python test_switches.py

Bam tay vao tung cong tac, xem trang thai chuyen tu "..." -> "CHAM"
de xac nhan day noi dung. Ctrl+C de thoat.
"""
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

# Map: ten -> pin
SWITCHES = [
    ("M1 MIN", PIN_M1_LIMIT_MIN),
    ("M1 MAX", PIN_M1_LIMIT_MAX),
    ("M2 MIN", PIN_M2_LIMIT_MIN),
    ("M2 MAX", PIN_M2_LIMIT_MAX),
]

# Tao Button cho moi switch
buttons = []
for name, pin in SWITCHES:
    if pin is None:
        buttons.append((name, pin, None))
    else:
        b = Button(pin, pull_up=True, bounce_time=0.02)
        buttons.append((name, pin, b))


def is_triggered(b):
    """NC: cham = HIGH = is_pressed False -> triggered = not is_pressed"""
    if b is None:
        return None
    return (not b.is_pressed) if SWITCH_NC else b.is_pressed


def state_str(state):
    if state is None:
        return "(chua config)"
    return "## CHAM ##" if state else "....tha...."


def main():
    print(f"Loai cong tac: {'NC (Normally Closed)' if SWITCH_NC else 'NO (Normally Open)'}")
    print("\nBam tay vao tung cong tac de kiem tra.")
    print("Trang thai phai chuyen 'tha' -> 'CHAM' khi bam.")
    print("Ctrl+C de thoat.\n")
    print(f"{'Switch':<10} {'GPIO':<8} {'Trang thai':<15}")
    print("-" * 35)

    last_states = {name: None for name, _, _ in buttons}

    try:
        while True:
            line_parts = []
            for name, pin, b in buttons:
                state = is_triggered(b)
                pin_str = f"GPIO{pin}" if pin is not None else "-"
                line_parts.append(f"{name:<10} {pin_str:<8} {state_str(state):<15}")

                # Bao khi co thay doi
                if last_states[name] is not None and state != last_states[name]:
                    if state:
                        print(f"   [+] {name} VUA BI CHAM!")
                    else:
                        print(f"   [-] {name} vua tha ra.")
                last_states[name] = state

            # In trang thai hien tai (1 dong, ghi de)
            status_line = "  |  ".join(
                f"{name}: {state_str(is_triggered(b))}" for name, _, b in buttons
            )
            print(f"\r{status_line}", end="", flush=True)
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n\nThoat.")


if __name__ == "__main__":
    main()
