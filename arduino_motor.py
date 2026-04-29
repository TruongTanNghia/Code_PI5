"""
Dieu khien Arduino quay motor tu Pi5 qua UART hoac USB.

Yeu cau:
- Arduino da upload arduino/motor_test/motor_test.ino (simple version)
- Cai pyserial: pip install pyserial

Cach dung:
    python arduino_motor.py 1            # M1 thuan, 1000 step (~720 deg / 2 vong)
    python arduino_motor.py 2            # M1 nguoc
    python arduino_motor.py 3            # M2 thuan
    python arduino_motor.py 4            # M2 nguoc
    python arduino_motor.py monitor      # chi xem output Arduino

    python arduino_motor.py 1 --port /dev/ttyUSB0     # ep buoc port USB

Moi lenh quay 1000 step (~2 vong) roi tu dung.
"""
import sys
import time
import glob
import os
import argparse

try:
    import serial
except ImportError:
    print("Chua cai pyserial. Chay: pip install pyserial")
    sys.exit(1)


def find_serial_port():
    if os.path.exists("/dev/serial0"):
        return "/dev/serial0"
    candidates = (
        sorted(glob.glob('/dev/ttyAMA*')) +
        sorted(glob.glob('/dev/ttyACM*')) +
        sorted(glob.glob('/dev/ttyUSB*'))
    )
    return candidates[0] if candidates else None


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("cmd", nargs="?", default=None,
                        help="1/2/3/4 = kenh, monitor = xem output")
    parser.add_argument("--port", default=None,
                        help="Override port (vd: /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=9600)
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args()

    if args.help or args.cmd is None:
        print(__doc__)
        sys.exit(0)

    port = args.port or find_serial_port()
    if not port:
        print("[!] Khong tim thay serial port.")
        sys.exit(1)

    print(f"[INFO] Mo port: {port} @ {args.baud}")
    try:
        ser = serial.Serial(port, args.baud, timeout=0.5)
    except serial.SerialException as e:
        print(f"[!] Khong mo duoc port: {e}")
        sys.exit(1)

    time.sleep(2.0)  # cho Arduino reset

    cmd = args.cmd.lower()
    valid_channels = {"1", "2", "3", "4"}

    # MONITOR mode
    if cmd == "monitor":
        print("[INFO] Mode monitor - Ctrl+C de thoat.")
        try:
            while True:
                line = ser.readline().decode(errors="ignore").rstrip()
                if line:
                    print(f"  [ARDUINO] {line}")
        except KeyboardInterrupt:
            print("\n[INFO] Thoat monitor.")
        finally:
            ser.close()
        return

    # SPIN
    if cmd not in valid_channels:
        print(f"[!] Tham so sai: '{cmd}'. Dung: 1/2/3/4, monitor")
        ser.close()
        sys.exit(1)

    # Doc banner Arduino
    while ser.in_waiting:
        line = ser.readline().decode(errors="ignore").rstrip()
        if line:
            print(f"  [ARDUINO] {line}")

    # Gui lenh
    print(f"[INFO] Gui lenh '{cmd}' -> Arduino quay 1000 step...")
    ser.write(cmd.encode())

    # Cho Arduino chay xong (~10-15 giay)
    print("[INFO] Doi motor quay xong (Ctrl+C de thoat sa hon)...")
    print()
    try:
        # Doc output Arduino cho den khi thay "XONG" hoac timeout
        timeout_at = time.time() + 30  # toi da 30s
        while time.time() < timeout_at:
            line = ser.readline().decode(errors="ignore").rstrip()
            if line:
                print(f"  [ARDUINO] {line}")
                if "XONG" in line:
                    break
    except KeyboardInterrupt:
        print("\n[INFO] Thoat.")
    finally:
        ser.close()
        print("[INFO] Da dong ket noi.")


if __name__ == "__main__":
    main()
