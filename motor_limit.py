"""
Quay motor LIEN TUC qua Arduino. Cham bat ky limit switch nao -> DUNG NGAY.

Yeu cau:
- Arduino da upload arduino/motor_test/motor_test.ino (continuous + stop)
- 4 limit switch da noi vao Pi5 (theo config.py)
- pyserial da cai (pip install pyserial)

Cach dung:
    python motor_limit.py 1            # M1 thuan (D2)
    python motor_limit.py 2            # M1 nguoc (D3)
    python motor_limit.py 3            # M2 thuan (D4)
    python motor_limit.py 4            # M2 nguoc (D5)

    python motor_limit.py 1 --port /dev/ttyUSB0     # ep buoc port

Cach hoat dong:
    1. Pi gui lenh '1' -> Arduino bat dau quay LIEN TUC
    2. Pi liên tuc check 4 limit switch (~50 lan/giay)
    3. Khi BAT KY switch nao bi cham -> Pi gui 's' -> Arduino dung
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


# Mapping channel -> ten + limit can quan tam
CHANNELS = {
    "1": ("M1 thuan (D2)", PIN_M1_LIMIT_MAX),   # quay thuan -> ve MAX
    "2": ("M1 nguoc (D3)", PIN_M1_LIMIT_MIN),   # quay nguoc -> ve MIN
    "3": ("M2 thuan (D4)", PIN_M2_LIMIT_MAX),
    "4": ("M2 nguoc (D5)", PIN_M2_LIMIT_MIN),
}


def is_pressed(button):
    """NC switch: cham = HIGH (is_pressed False) -> triggered = not is_pressed.
       NO switch: cham = LOW (is_pressed True) -> triggered = is_pressed."""
    if button is None:
        return False
    return (not button.is_pressed) if SWITCH_NC else button.is_pressed


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("channel", nargs="?", default=None,
                        help="1/2/3/4")
    parser.add_argument("--port", default=None)
    parser.add_argument("--baud", type=int, default=9600)
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args()

    if args.help or args.channel is None:
        print(__doc__)
        sys.exit(0)

    if args.channel not in CHANNELS:
        print(f"[!] Channel sai: '{args.channel}'. Dung 1/2/3/4")
        sys.exit(1)

    name, watch_pin = CHANNELS[args.channel]

    # Mo serial den Arduino
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

    time.sleep(2.0)  # Arduino reset
    while ser.in_waiting:
        ser.readline()  # discard banner

    # Mo TAT CA limit switch (de check an toan)
    all_pins = [
        ("M1 MIN", PIN_M1_LIMIT_MIN),
        ("M1 MAX", PIN_M1_LIMIT_MAX),
        ("M2 MIN", PIN_M2_LIMIT_MIN),
        ("M2 MAX", PIN_M2_LIMIT_MAX),
    ]
    buttons = []
    for label, pin in all_pins:
        if pin is None:
            buttons.append((label, None))
        else:
            try:
                b = Button(pin, pull_up=True, bounce_time=0.02)
                buttons.append((label, b))
            except Exception as e:
                print(f"[!] Khong mo duoc GPIO{pin} cho {label}: {e}")
                buttons.append((label, None))

    # Check trang thai ban dau
    print(f"\nTrang thai limit switch hien tai:")
    for label, b in buttons:
        if b is None:
            print(f"  {label}: chua cau hinh")
        else:
            state = "TRIGGERED" if is_pressed(b) else "tha"
            print(f"  {label}: {state}")

    # Neu limit muc tieu dang trigger -> bo qua
    target_button = next((b for label, b in buttons if all_pins[buttons.index((label, b))][1] == watch_pin), None)
    # Don gian hon: tim button theo pin
    target_button = None
    for label, b in buttons:
        if b is not None:
            # Lay pin tu config
            if (label == "M1 MIN" and watch_pin == PIN_M1_LIMIT_MIN) or \
               (label == "M1 MAX" and watch_pin == PIN_M1_LIMIT_MAX) or \
               (label == "M2 MIN" and watch_pin == PIN_M2_LIMIT_MIN) or \
               (label == "M2 MAX" and watch_pin == PIN_M2_LIMIT_MAX):
                target_button = (label, b)
                break

    if target_button and is_pressed(target_button[1]):
        print(f"\n[!] Limit {target_button[0]} dang TRIGGERED -> khong the quay theo huong nay.")
        ser.close()
        sys.exit(1)

    # Gui lenh quay
    print(f"\n[INFO] Gui lenh '{args.channel}' -> Arduino quay {name}...")
    ser.write(args.channel.encode())
    time.sleep(0.1)
    while ser.in_waiting:
        line = ser.readline().decode(errors="ignore").rstrip()
        if line:
            print(f"  [ARDUINO] {line}")

    print(f"[INFO] Motor dang quay. Cham limit switch -> dung. Ctrl+C -> dung.")
    print()

    # Vong giam sat
    try:
        while True:
            # Check tat ca limit switch
            for label, b in buttons:
                if b is not None and is_pressed(b):
                    print(f"\n[!] LIMIT {label} CHAM! Gui lenh STOP...")
                    ser.write(b's')
                    time.sleep(0.3)
                    while ser.in_waiting:
                        line = ser.readline().decode(errors="ignore").rstrip()
                        if line:
                            print(f"  [ARDUINO] {line}")
                    return

            # Doc output Arduino (neu co)
            if ser.in_waiting:
                line = ser.readline().decode(errors="ignore").rstrip()
                if line:
                    print(f"  [ARDUINO] {line}")

            time.sleep(0.02)  # 50 Hz check rate

    except KeyboardInterrupt:
        print("\n[!] Ctrl+C -> Gui lenh STOP...")
        ser.write(b's')
        time.sleep(0.3)
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
