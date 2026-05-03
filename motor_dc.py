"""
Dieu khien DC motor qua Arduino + L298N tu Pi5.
Cham bat ky limit switch -> motor DUNG NGAY.

Yeu cau:
- Arduino da upload arduino/motor_dc/motor_dc.ino
- 4 limit switch noi vao Pi5 GPIO theo config.py
- pyserial (pip install pyserial)
- gpiozero, lgpio

Cach dung:
    python motor_dc.py f                  # quay thuan, cham limit -> dung
    python motor_dc.py b                  # quay nguoc, cham limit -> dung
    python motor_dc.py f --no-limits      # quay thuan, KHONG check limit, Ctrl+C de dung
    python motor_dc.py f --time 5         # quay 5 giay roi tu dung (con check limit)

Cach hoat dong:
    1. Pi gui 'F' (hoac 'B') -> Arduino quay motor
    2. Pi check 4 limit switch lien tuc (~50 lan/giay)
    3. Khi BAT KY switch nao bi cham (3 lan lien tiep) -> Pi gui 'S' -> Arduino dung
    4. Hoac het thoi gian (--time) -> Pi gui 'S'
    5. Hoac Ctrl+C -> Pi gui 'S' va thoat
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
                        help="So lan doc lien tiep (chong nhieu, default 3)")
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args()

    if args.help or args.direction is None:
        print(__doc__)
        sys.exit(0)

    direction = args.direction.lower()
    if direction not in ('f', 'b', 'F', 'B'):
        print(f"[!] Direction sai: '{direction}'. Dung 'f' (forward) hoac 'b' (backward).")
        sys.exit(1)

    cmd_byte = b'F' if direction in ('f', 'F') else b'B'
    cmd_name = "FORWARD" if direction in ('f', 'F') else "BACKWARD"

    # Mo serial
    port = args.port or find_arduino_port()
    if not port:
        print("[!] Khong tim thay Arduino port (/dev/ttyUSB* hoac /dev/ttyACM*)")
        sys.exit(1)

    print(f"[INFO] Arduino port: {port}")
    try:
        ser = serial.Serial(port, args.baud, timeout=0.1)
    except serial.SerialException as e:
        print(f"[!] Loi mo port: {e}")
        sys.exit(1)

    time.sleep(2.0)  # cho Arduino reset xong (DTR cap discharge)
    while ser.in_waiting:
        ser.read(ser.in_waiting)

    # Setup limit switches
    buttons = []
    if not args.no_limits:
        all_pins = [
            ("M1 MIN", PIN_M1_LIMIT_MIN),
            ("M1 MAX", PIN_M1_LIMIT_MAX),
            ("M2 MIN", PIN_M2_LIMIT_MIN),
            ("M2 MAX", PIN_M2_LIMIT_MAX),
        ]
        for label, pin in all_pins:
            if pin is None:
                buttons.append((label, None))
            else:
                try:
                    b = Button(pin, pull_up=True, bounce_time=0.05)
                    buttons.append((label, b))
                except Exception as e:
                    print(f"[!] Khong mo duoc GPIO{pin} cho {label}: {e}")
                    buttons.append((label, None))

        # In trang thai limit
        print(f"\nTrang thai limit switch hien tai:")
        for label, b in buttons:
            if b is None:
                print(f"  {label}: chua cau hinh")
            else:
                state = "TRIGGERED" if is_pressed_debounced(b, args.debounce) else "tha"
                print(f"  {label}: {state}")

        # Neu co cai dang trigger -> canh bao
        triggered_now = [label for label, b in buttons
                         if b is not None and is_pressed_debounced(b, args.debounce)]
        if triggered_now:
            print(f"\n[!] CANH BAO: {triggered_now} dang trigger - motor co the dung ngay sau khi quay!")
    else:
        print("\n[!] CHE DO --no-limits: KHONG check limit switch.")

    # Gui lenh quay
    print(f"\n[INFO] Gui lenh '{cmd_byte.decode()}' -> Motor {cmd_name}...")
    ser.write(cmd_byte)

    print(f"[INFO] Motor dang quay. ", end="")
    if args.no_limits:
        print("Ctrl+C -> dung.")
    elif args.time > 0:
        print(f"Quay toi da {args.time}s, hoac cham limit, hoac Ctrl+C.")
    else:
        print("Cham limit -> dung. Ctrl+C -> dung.")
    print()

    # Vong giam sat
    start_time = time.time()
    try:
        while True:
            # Kiem tra timeout
            if args.time > 0 and (time.time() - start_time) >= args.time:
                print(f"\n[!] Het {args.time}s. Gui STOP...")
                ser.write(b'S')
                time.sleep(0.3)
                return

            # Kiem tra limit switch
            if not args.no_limits:
                for label, b in buttons:
                    if b is not None and is_pressed_debounced(b, args.debounce):
                        print(f"\n[!] LIMIT {label} CHAM! Gui STOP...")
                        ser.write(b'S')
                        time.sleep(0.3)
                        return

            time.sleep(0.02)  # 50 Hz check rate

    except KeyboardInterrupt:
        print("\n[!] Ctrl+C -> Gui STOP...")
        ser.write(b'S')
        time.sleep(0.3)

    finally:
        try:
            ser.close()
        except Exception:
            pass
        for label, b in buttons:
            if b is not None:
                try:
                    b.close()
                except Exception:
                    pass
        print("[INFO] Cleanup done.")


if __name__ == "__main__":
    main()
