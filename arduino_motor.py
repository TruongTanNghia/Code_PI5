"""
Dieu khien Arduino quay motor tu Pi5 qua UART (GPIO14/15) hoac USB.

YEU CAU:
- Arduino da upload arduino/motor_test/motor_test.ino
- Cam day theo 1 trong 2 cach:
    A) UART (mac dinh, anh dang dung):
       Pi GPIO14 (TX, chan 8)  -> Arduino RX (D0)
       Arduino TX (D1) -[1K]-+- Pi GPIO15 (RX, chan 10)
                             |
                            [2K]
                             |
                            GND
       Pi GND (chan 6)        -> Arduino GND
       (Voltage divider 1K/2K de ha 5V Arduino xuong 3.3V cho Pi)

    B) USB: cap USB Arduino vao Pi
- Cai pyserial: pip install pyserial
- Da bat UART trong raspi-config (chi cho mode A)

CACH DUNG:
    python arduino_motor.py 1            # quay kenh U1, toc do vua
    python arduino_motor.py 2 f          # kenh U2, NHANH (1000 step/s)
    python arduino_motor.py 3 l          # kenh U3, CHAM (50 step/s)
    python arduino_motor.py 4 v          # kenh U4, RAT CHAM (5 step/s)
    python arduino_motor.py stop         # dung motor
    python arduino_motor.py monitor      # chi xem output Arduino

    python arduino_motor.py 1 m --port /dev/ttyACM0   # ep buoc dung USB

Ctrl+C de dung va thoat.
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


# Thu tu uu tien tim port:
# 1. /dev/serial0 (UART chuan tren Pi - GPIO14/15)
# 2. /dev/ttyAMA* (UART truc tiep)
# 3. /dev/ttyACM*, /dev/ttyUSB* (USB)
def find_serial_port():
    if os.path.exists("/dev/serial0"):
        return "/dev/serial0"
    candidates = (
        sorted(glob.glob('/dev/ttyAMA*')) +
        sorted(glob.glob('/dev/ttyACM*')) +
        sorted(glob.glob('/dev/ttyUSB*'))
    )
    return candidates[0] if candidates else None


def drain(ser, label="ARDUINO"):
    """Doc het du lieu hien co tu serial va in ra."""
    while ser.in_waiting:
        line = ser.readline().decode(errors="ignore").rstrip()
        if line:
            print(f"  [{label}] {line}")


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("cmd", nargs="?", default=None,
                        help="1/2/3/4 = kenh, stop = dung, monitor = xem output")
    parser.add_argument("speed", nargs="?", default="m",
                        help="v=rat cham, l=cham, m=vua, f=nhanh")
    parser.add_argument("--port", default=None,
                        help="Override port (vd: /dev/ttyACM0)")
    parser.add_argument("--baud", type=int, default=9600)
    parser.add_argument("-h", "--help", action="store_true")
    args = parser.parse_args()

    if args.help or args.cmd is None:
        print(__doc__)
        sys.exit(0)

    port = args.port or find_serial_port()
    if not port:
        print("[!] Khong tim thay serial port (UART hoac USB).")
        print("    Bat UART: sudo raspi-config -> Interface -> Serial -> enable hardware")
        print("    Hoac cam Arduino qua USB.")
        sys.exit(1)

    print(f"[INFO] Mo port: {port} @ {args.baud}")
    try:
        ser = serial.Serial(port, args.baud, timeout=0.5)
    except serial.SerialException as e:
        print(f"[!] Khong mo duoc port {port}: {e}")
        if "/dev/serial0" in port or "ttyAMA" in port:
            print("    UART chua bat? Chay: sudo raspi-config")
            print("    -> Interface Options -> Serial Port")
            print("    -> Login shell: NO, Hardware: YES, Reboot")
        sys.exit(1)

    # Cho Arduino reset (chi xay ra khi mo USB serial; UART thi khong reset)
    time.sleep(2.0)
    drain(ser)

    cmd = args.cmd.lower()

    valid_channels = {"1", "2", "3", "4"}
    valid_speeds = {"v", "l", "m", "f"}

    # === STOP ===
    if cmd in ("stop", "s"):
        ser.write(b's')
        print("[INFO] Da gui lenh STOP.")
        time.sleep(0.5)
        drain(ser)
        ser.close()
        return

    # === MONITOR ===
    if cmd == "monitor":
        print("[INFO] Mode monitor - chi xem output Arduino. Ctrl+C de thoat.")
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

    # === SPIN CHANNEL ===
    if cmd not in valid_channels:
        print(f"[!] Tham so sai: '{cmd}'. Dung: 1/2/3/4, stop, monitor")
        ser.close()
        sys.exit(1)

    if args.speed not in valid_speeds:
        print(f"[!] Toc do sai: '{args.speed}'. Dung: v / l / m / f")
        ser.close()
        sys.exit(1)

    print(f"[INFO] Set toc do: '{args.speed}'")
    ser.write(args.speed.encode())
    time.sleep(0.2)
    drain(ser)

    print(f"[INFO] Quay kenh {cmd}...")
    ser.write(cmd.encode())
    time.sleep(0.2)

    print("[INFO] Motor dang quay. Ctrl+C de DUNG.")
    print()
    try:
        while True:
            line = ser.readline().decode(errors="ignore").rstrip()
            if line:
                print(f"  [ARDUINO] {line}")
    except KeyboardInterrupt:
        print("\n[INFO] Gui lenh STOP...")
        ser.write(b's')
        time.sleep(0.5)
        drain(ser)
    finally:
        ser.close()
        print("[INFO] Da dong ket noi.")


if __name__ == "__main__":
    main()
