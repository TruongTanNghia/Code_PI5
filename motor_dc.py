"""
Dieu khien 2 DC motor qua Arduino + L298N tu Pi5.
Moi motor co cap limit switch RIENG -> chi dung motor do khi cham limit cua no.

Motor 1 (PAN, trai-phai):  watch M1MIN, M1MAX
Motor 2 (TILT, len-xuong): watch M2MIN, M2MAX

Cach dung:
    python motor_dc.py 1 f       # Motor 1 forward (PHAI), dung khi cham M1MIN/MAX
    python motor_dc.py 1 b       # Motor 1 backward (TRAI)
    python motor_dc.py 2 f       # Motor 2 up (forward)
    python motor_dc.py 2 b       # Motor 2 down (backward)

    python motor_dc.py 1 f --speed 6      # Toc do 6/9 (PWM 150)
    python motor_dc.py 1 f --no-limits    # Khong check limit (Ctrl+C de dung)
    python motor_dc.py 1 f --time 5       # Quay max 5 giay
    python motor_dc.py 1 f --quiet        # Tat log lien tuc
"""
import sys
import time
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


# Mapping: (motor, direction) -> (start_cmd, name, stop_cmd, [(label, pin), ...])
MOTOR_TABLE = {
    ("1", "f"): ('F', "M1 forward (PHAI)",
                 'X', [("M1MIN", PIN_M1_LIMIT_MIN), ("M1MAX", PIN_M1_LIMIT_MAX)]),
    ("1", "b"): ('B', "M1 backward (TRAI)",
                 'X', [("M1MIN", PIN_M1_LIMIT_MIN), ("M1MAX", PIN_M1_LIMIT_MAX)]),
    ("2", "f"): ('U', "M2 up",
                 'Y', [("M2MIN", PIN_M2_LIMIT_MIN), ("M2MAX", PIN_M2_LIMIT_MAX)]),
    ("2", "b"): ('D', "M2 down",
                 'Y', [("M2MIN", PIN_M2_LIMIT_MIN), ("M2MAX", PIN_M2_LIMIT_MAX)]),
}


def find_arduino_port():
    candidates = (
        sorted(glob.glob('/dev/ttyACM*')) +
        sorted(glob.glob('/dev/ttyUSB*'))
    )
    return candidates[0] if candidates else None


def is_pressed_raw(button):
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
    if button is None:
        return f"{label}(--)=----"
    gpio_low = button.is_pressed
    triggered = is_pressed_debounced(button, debounce)
    gpio_str = "LOW " if gpio_low else "HIGH"
    triggered_str = "[CHAM]" if triggered else "  tha "
    return f"{label}(GPIO{pin}):{gpio_str}={triggered_str}"


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("motor", nargs="?", default=None, choices=("1", "2"),
                        help="Motor 1 hoac 2")
    parser.add_argument("direction", nargs="?", default=None, choices=("f", "b"),
                        help="f = forward, b = backward")
    parser.add_argument("--port", default=None)
    parser.add_argument("--baud", type=int, default=9600)
    parser.add_argument("--no-limits", action="store_true")
    parser.add_argument("--time", type=float, default=0)
    parser.add_argument("--debounce", type=int, default=3)
    parser.add_argument("--speed", type=int, default=2, choices=range(0, 10),
                        help="Toc do 0-9 (default 2 = PWM 50, cham). Tang neu can nhanh hon.")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--log-interval", type=float, default=0.3)
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args()

    if args.help or args.motor is None or args.direction is None:
        print(__doc__)
        sys.exit(0)

    key = (args.motor, args.direction)
    if key not in MOTOR_TABLE:
        print(f"[!] Combination motor={args.motor} dir={args.direction} khong hop le.")
        sys.exit(1)

    start_cmd, name, stop_cmd, watch_pins = MOTOR_TABLE[key]

    # Mo serial
    port = args.port or find_arduino_port()
    if not port:
        print("[!] Khong tim thay Arduino port")
        sys.exit(1)

    print(f"[INFO] Arduino port: {port}")
    print(f"[INFO] Loai cong tac: {'NC' if SWITCH_NC else 'NO'}")
    print(f"[INFO] Motor: {name}")
    print(f"[INFO] Watch limits: {[lbl for lbl, _ in watch_pins]}")

    try:
        ser = serial.Serial(port, args.baud, timeout=0.1)
    except serial.SerialException as e:
        print(f"[!] Loi mo port: {e}")
        sys.exit(1)

    time.sleep(2.0)
    while ser.in_waiting:
        ser.read(ser.in_waiting)

    # Setup limit switches CUA MOTOR NAY (chi 2 cai)
    buttons = []
    if not args.no_limits:
        for label, pin in watch_pins:
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
        print(f"\n=== TRANG THAI 2 LIMIT CUA MOTOR {args.motor} ===")
        for label, pin, b in buttons:
            print(f"   {state_string(label, pin, b, args.debounce)}")

        triggered = [lbl for lbl, _, b in buttons
                     if b is not None and is_pressed_debounced(b, args.debounce)]
        if triggered:
            print(f"\n[!] CANH BAO: {triggered} dang TRIGGERED -> motor co the dung ngay!")
    else:
        print("\n[!] CHE DO --no-limits.")

    # Set toc do
    pwm = args.speed * 25
    print(f"\n[INFO] Set toc do: {args.speed}/9 (PWM {pwm}/255)")
    ser.write(str(args.speed).encode())
    time.sleep(0.05)

    # Gui lenh quay
    print(f"[INFO] Gui '{start_cmd}' -> {name}...")
    ser.write(start_cmd.encode())

    print(f"[INFO] Motor dang quay. ", end="")
    if args.no_limits:
        print("Ctrl+C -> dung.")
    elif args.time > 0:
        print(f"Toi da {args.time}s, cham limit, hoac Ctrl+C.")
    else:
        print("Cham limit cua motor nay -> dung. Ctrl+C -> dung.")
    print()

    # Vong giam sat + log
    start_time = time.time()
    last_log = 0

    try:
        while True:
            now = time.time()

            if args.time > 0 and (now - start_time) >= args.time:
                print(f"\n[!] Het {args.time}s. Gui stop ('{stop_cmd}')...")
                ser.write(stop_cmd.encode())
                time.sleep(0.3)
                return

            # Log trang thai
            if not args.no_limits and not args.quiet and (now - last_log) >= args.log_interval:
                elapsed = now - start_time
                states = " | ".join(state_string(l, p, b, args.debounce) for l, p, b in buttons)
                print(f"  [{elapsed:5.1f}s] {states}")
                last_log = now

            # Check limit -> stop motor
            if not args.no_limits:
                for label, pin, b in buttons:
                    if b is not None and is_pressed_debounced(b, args.debounce):
                        print(f"\n[!] >>> LIMIT {label} (GPIO{pin}) CHAM! <<< Stop motor {args.motor}...")
                        ser.write(stop_cmd.encode())
                        time.sleep(0.3)
                        return

            time.sleep(0.02)

    except KeyboardInterrupt:
        print(f"\n[!] Ctrl+C -> Stop motor {args.motor} ('{stop_cmd}')...")
        ser.write(stop_cmd.encode())
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
