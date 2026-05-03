"""
Dieu khien DC motor qua Arduino + L298N tu Pi5.
Cham bat ky limit switch -> motor DUNG NGAY.
LOG REAL-TIME trang thai 4 switch moi 0.3s de debug.

Cach dung:
    python motor_dc.py f                  # quay thuan, cham limit -> dung
    python motor_dc.py b                  # quay nguoc
    python motor_dc.py f --no-limits      # KHONG check limit
    python motor_dc.py f --time 5         # quay toi da 5 giay
    python motor_dc.py f --quiet          # tat log lien tuc
"""
import sys
import time
import os
import glob
import argparse

try:
    import serial
except ImportError:
    print("[!] Chua cai pyserial. Chay: pip install pyserial")
    sys.exit(1)

from gpiozero import Button
from gpiozero.pins.lgpio import LGPIOFactory
from gpiozero import Device
Device.pin_factory = LGPIOFactory()

from config import (
    PIN_M1_LIMIT_MIN, PIN_M1_LIMIT_MAX,
    PIN_M2_LIMIT_MIN, PIN_M2_LIMIT_MAX,
    SWITCH_NC,
)


def find_arduino_port():
    candidates = (
        sorted(glob.glob('/dev/ttyACM*')) +
        sorted(glob.glob('/dev/ttyUSB*'))
    )
    return candidates[0] if candidates else None


def is_pressed_raw(button):
    """Sau khi dien giai NC/NO config."""
    if button is None:
        return False
    return (not button.is_pressed) if SWITCH_NC else button.is_pressed


def is_pressed_debounced(button, n=3, sample_delay=0.005):
    if button is None:
        return False
    for _ in range(n):
        if not is_pressed_raw(button):
            return False
        time.sleep(sample_delay)
    return True


def state_string(label, pin, button, debounce):
    """Format trang thai 1 switch de log."""
    if button is None:
        return f"{label}(--)=----"
    # gpiozero is_pressed: True khi pin LOW (pull_up=True)
    gpio_low = button.is_pressed
    triggered = is_pressed_debounced(button, debounce)
    gpio_str = "LOW " if gpio_low else "HIGH"
    triggered_str = "[CHAM]" if triggered else "  tha "
    return f"{label}(GPIO{pin}):{gpio_str}={triggered_str}"


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("direction", nargs="?", default=None,
                        help="f = forward, b = backward")
    parser.add_argument("--port", default=None,
                        help="Override port (default: auto-detect)")
    parser.add_argument("--baud", type=int, default=9600)
    parser.add_argument("--no-limits", action="store_true",
                        help="Khong monitor limit switch")
    parser.add_argument("--time", type=float, default=0,
                        help="Toi da quay X giay (0 = khong gioi han)")
    parser.add_argument("--debounce", type=int, default=3,
                        help="So lan doc lien tiep (default 3)")
    parser.add_argument("--quiet", action="store_true",
                        help="Tat log trang thai lien tuc")
    parser.add_argument("--log-interval", type=float, default=0.3,
                        help="Khoang cach in log (giay, default 0.3)")
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args()

    if args.help or args.direction is None:
        print(__doc__)
        sys.exit(0)

    direction = args.direction.lower()
    if direction not in ('f', 'b'):
        print(f"[!] Direction sai: '{direction}'. Dung 'f' hoac 'b'.")
        sys.exit(1)

    cmd_byte = b'F' if direction == 'f' else b'B'
    cmd_name = "FORWARD" if direction == 'f' else "BACKWARD"

    # Mo serial
    port = args.port or find_arduino_port()
    if not port:
        print("[!] Khong tim thay Arduino port")
        sys.exit(1)

    print(f"[INFO] Arduino port: {port}")
    print(f"[INFO] Loai cong tac: {'NC (Normally Closed)' if SWITCH_NC else 'NO (Normally Open)'}")

    try:
        ser = serial.Serial(port, args.baud, timeout=0.1)
    except serial.SerialException as e:
        print(f"[!] Loi mo port: {e}")
        sys.exit(1)

    time.sleep(2.0)
    while ser.in_waiting:
        ser.read(ser.in_waiting)

    # Setup limit switches
    all_pins = [
        ("M1MIN", PIN_M1_LIMIT_MIN),
        ("M1MAX", PIN_M1_LIMIT_MAX),
        ("M2MIN", PIN_M2_LIMIT_MIN),
        ("M2MAX", PIN_M2_LIMIT_MAX),
    ]
    buttons = []
    if not args.no_limits:
        for label, pin in all_pins:
            if pin is None:
                buttons.append((label, pin, None))
            else:
                try:
                    b = Button(pin, pull_up=True, bounce_time=0.05)
                    buttons.append((label, pin, b))
                except Exception as e:
                    print(f"[!] Khong mo duoc GPIO{pin} ({label}): {e}")
                    buttons.append((label, pin, None))

        # In trang thai ban dau
        print(f"\n=== TRANG THAI BAN DAU 4 LIMIT SWITCH ===")
        for label, pin, b in buttons:
            print(f"   {state_string(label, pin, b, args.debounce)}")

        # Canh bao neu co cai dang trigger
        triggered = [label for label, _, b in buttons
                     if b is not None and is_pressed_debounced(b, args.debounce)]
        if triggered:
            print(f"\n[!] CANH BAO: {triggered} dang TRIGGERED!")
            print("    Motor se dung NGAY khi quay.")
            print("    Neu cong tac chua bam ma van TRIGGERED -> sai loai NC/NO trong config")
            print("    Hoac dau chua dung. Sua SWITCH_NC trong config.py.")
    else:
        print("\n[!] CHE DO --no-limits: KHONG check limit switch.")

    # Gui lenh quay
    print(f"\n[INFO] Gui lenh '{cmd_byte.decode()}' -> Motor {cmd_name}...")
    ser.write(cmd_byte)

    print(f"[INFO] Motor dang quay. ", end="")
    if args.no_limits:
        print("Ctrl+C -> dung.")
    elif args.time > 0:
        print(f"Toi da {args.time}s, cham limit, hoac Ctrl+C de dung.")
    else:
        print("Cham limit -> dung. Ctrl+C -> dung.")
    print()

    # Vong giam sat + log
    start_time = time.time()
    last_log = 0
    iteration = 0

    try:
        while True:
            iteration += 1
            now = time.time()

            # Kiem tra timeout
            if args.time > 0 and (now - start_time) >= args.time:
                print(f"\n[!] Het {args.time}s. Gui STOP...")
                ser.write(b'S')
                time.sleep(0.3)
                return

            # Log trang thai cong tac (moi log_interval)
            if not args.no_limits and not args.quiet and (now - last_log) >= args.log_interval:
                elapsed = now - start_time
                states = " | ".join(state_string(l, p, b, args.debounce) for l, p, b in buttons)
                print(f"  [{elapsed:5.1f}s] {states}")
                last_log = now

            # Kiem tra limit switch -> dung
            if not args.no_limits:
                for label, pin, b in buttons:
                    if b is not None and is_pressed_debounced(b, args.debounce):
                        print(f"\n[!] >>> LIMIT {label} (GPIO{pin}) CHAM! <<< Gui STOP...")
                        ser.write(b'S')
                        time.sleep(0.3)
                        return

            time.sleep(0.02)

    except KeyboardInterrupt:
        print("\n[!] Ctrl+C -> Gui STOP...")
        ser.write(b'S')
        time.sleep(0.3)

    finally:
        try:
            ser.close()
        except Exception:
            pass
        for label, pin, b in buttons:
            if b is not None:
                try:
                    b.close()
                except Exception:
                    pass
        print("[INFO] Cleanup done.")


if __name__ == "__main__":
    main()
