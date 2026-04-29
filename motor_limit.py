"""
Quay motor LIEN TUC qua Arduino. Cham bat ky limit switch nao -> DUNG NGAY.

Yeu cau:
- Arduino da upload arduino/motor_test/motor_test.ino (V3)
- 4 limit switch da noi vao Pi5 (theo config.py)
- pyserial da cai

Cach dung:
    python motor_limit.py 1                       # M1 thuan + monitor limit
    python motor_limit.py 2 --no-limits           # M1 nguoc, KHONG monitor limit (de test motor)
    python motor_limit.py 1 --port /dev/ttyUSB0   # ep buoc port
    python motor_limit.py 1 --debounce 5          # can 5 lan doc lien tiep moi tinh la pressed (chong nhieu)

Cach hoat dong:
    1. Pi gui lenh -> Arduino bat dau quay LIEN TUC
    2. Pi liên tuc check limit switch (50 lan/giay)
    3. Khi limit cham N lan lien tiep (debounce) -> Pi gui 's' -> Arduino dung
    4. Hoac Ctrl+C -> Pi gui 's' va thoat
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
    if os.path.exists("/dev/serial0"):
        return "/dev/serial0"
    candidates = (
        sorted(glob.glob('/dev/ttyACM*')) +
        sorted(glob.glob('/dev/ttyUSB*'))
    )
    return candidates[0] if candidates else None


CHANNELS = {
    "1": ("M1 thuan (D2)", PIN_M1_LIMIT_MAX),
    "2": ("M1 nguoc (D3)", PIN_M1_LIMIT_MIN),
    "3": ("M2 thuan (D4)", PIN_M2_LIMIT_MAX),
    "4": ("M2 nguoc (D5)", PIN_M2_LIMIT_MIN),
}


def is_pressed_raw(button):
    """Doc 1 lan, khong debounce."""
    if button is None:
        return False
    return (not button.is_pressed) if SWITCH_NC else button.is_pressed


def is_pressed_debounced(button, n_required=3, sample_delay=0.005):
    """Doc N lan lien tiep, neu TAT CA deu pressed thi tra ve True.
    Chong nhieu dien tu tu motor."""
    if button is None:
        return False
    for _ in range(n_required):
        if not is_pressed_raw(button):
            return False
        time.sleep(sample_delay)
    return True


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("channel", nargs="?", default=None,
                        help="1/2/3/4")
    parser.add_argument("--port", default=None)
    parser.add_argument("--baud", type=int, default=9600)
    parser.add_argument("--no-limits", action="store_true",
                        help="Khong monitor limit switch (chi quay motor)")
    parser.add_argument("--debounce", type=int, default=3,
                        help="So lan doc lien tiep de coi la pressed (default 3)")
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args()

    if args.help or args.channel is None:
        print(__doc__)
        sys.exit(0)

    if args.channel not in CHANNELS:
        print(f"[!] Channel sai: '{args.channel}'. Dung 1/2/3/4")
        sys.exit(1)

    name, _ = CHANNELS[args.channel]

    # Mo serial
    port = args.port or find_arduino_port()
    if not port:
        print("[!] Khong tim thay Arduino port")
        sys.exit(1)

    print(f"[INFO] Arduino port: {port}")
    try:
        ser = serial.Serial(port, args.baud, timeout=0.1)
    except serial.SerialException as e:
        print(f"[!] Loi mo port: {e}")
        sys.exit(1)

    time.sleep(2.0)
    while ser.in_waiting:
        line = ser.readline().decode(errors="ignore").rstrip()
        if line:
            print(f"  [ARDUINO] {line}")

    # Mo limit switch (neu can)
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
                    # bounce_time cao hon (50ms) de chong nhieu
                    b = Button(pin, pull_up=True, bounce_time=0.05)
                    buttons.append((label, b))
                except Exception as e:
                    print(f"[!] Khong mo duoc GPIO{pin} cho {label}: {e}")
                    buttons.append((label, None))

        # In trang thai
        print(f"\nTrang thai limit switch hien tai (debounce {args.debounce} reads):")
        for label, b in buttons:
            if b is None:
                print(f"  {label}: chua cau hinh")
            else:
                state = "TRIGGERED" if is_pressed_debounced(b, args.debounce) else "tha"
                print(f"  {label}: {state}")
    else:
        print("\n[!] CHE DO --no-limits: KHONG monitor limit switch.")
        print("    Motor se quay den khi anh nhan Ctrl+C.")

    # Gui lenh
    print(f"\n[INFO] Gui lenh '{args.channel}' -> Arduino quay {name}...")
    ser.write(args.channel.encode())
    time.sleep(0.2)
    while ser.in_waiting:
        line = ser.readline().decode(errors="ignore").rstrip()
        if line:
            print(f"  [ARDUINO] {line}")

    print(f"[INFO] Motor dang quay. ", end="")
    if args.no_limits:
        print("Ctrl+C -> dung.")
    else:
        print("Cham limit -> dung. Ctrl+C -> dung.")
    print()

    # Vong giam sat
    try:
        while True:
            if not args.no_limits:
                for label, b in buttons:
                    if b is not None and is_pressed_debounced(b, args.debounce):
                        print(f"\n[!] LIMIT {label} CHAM ({args.debounce} reads xac nhan)! Gui STOP...")
                        ser.write(b's')
                        time.sleep(0.5)
                        while ser.in_waiting:
                            line = ser.readline().decode(errors="ignore").rstrip()
                            if line:
                                print(f"  [ARDUINO] {line}")
                        return

            # Doc output Arduino
            if ser.in_waiting:
                line = ser.readline().decode(errors="ignore").rstrip()
                if line:
                    print(f"  [ARDUINO] {line}")

            time.sleep(0.02)

    except KeyboardInterrupt:
        print("\n[!] Ctrl+C -> Gui STOP...")
        ser.write(b's')
        time.sleep(0.5)
        while ser.in_waiting:
            line = ser.readline().decode(errors="ignore").rstrip()
            if line:
                print(f"  [ARDUINO] {line}")

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
        print("\n[INFO] Cleanup done.")


if __name__ == "__main__":
    main()
