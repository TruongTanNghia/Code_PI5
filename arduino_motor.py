"""
Dieu khien Arduino quay motor tu Pi5 (qua USB Serial).

Yeu cau:
- Arduino da upload code arduino/motor_test/motor_test.ino
- Cap USB Arduino vao Pi5
- Cai pyserial: pip install pyserial

Cach dung:
    python arduino_motor.py 1            # quay kenh U1, toc do vua
    python arduino_motor.py 2 f          # quay kenh U2, NHANH (1000 step/s)
    python arduino_motor.py 3 l          # quay kenh U3, CHAM (50 step/s)
    python arduino_motor.py 4 v          # quay kenh U4, RAT CHAM (5 step/s)
    python arduino_motor.py stop         # dung motor
    python arduino_motor.py monitor      # chi xem output Arduino, khong gui lenh

Ctrl+C de dung va thoat.
"""
import sys
import time
import glob

try:
    import serial
except ImportError:
    print("Chua cai pyserial. Chay: pip install pyserial")
    sys.exit(1)


def find_arduino_port():
    """Tu dong tim port Arduino (Linux: /dev/ttyUSB0 hoac /dev/ttyACM0)."""
    candidates = sorted(
        glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*')
    )
    if not candidates:
        print("[!] Khong tim thay Arduino.")
        print("    Kiem tra: cap USB Arduino, lenh `ls /dev/tty*`")
        sys.exit(1)
    return candidates[0]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    arg = sys.argv[1].lower()
    speed = sys.argv[2].lower() if len(sys.argv) > 2 else "m"

    valid_channels = {"1", "2", "3", "4"}
    valid_speeds = {"v", "l", "m", "f"}

    port = find_arduino_port()
    print(f"[INFO] Ket noi Arduino: {port}")

    ser = serial.Serial(port, 9600, timeout=0.5)
    time.sleep(2.0)  # Arduino auto-reset khi mo serial, doi 2s khoi dong

    # Doc message khoi dong cua Arduino
    while ser.in_waiting:
        line = ser.readline().decode(errors="ignore").rstrip()
        if line:
            print(f"  [ARDUINO] {line}")

    # Xu ly lenh
    if arg == "stop" or arg == "s":
        ser.write(b's')
        print("[INFO] Da gui lenh STOP.")
        time.sleep(0.5)
        while ser.in_waiting:
            print(f"  [ARDUINO] {ser.readline().decode(errors='ignore').rstrip()}")
        ser.close()
        return

    if arg == "monitor":
        print("[INFO] Mode monitor - chi xem output Arduino. Ctrl+C de thoat.")
        try:
            while True:
                line = ser.readline().decode(errors="ignore").rstrip()
                if line:
                    print(f"  [ARDUINO] {line}")
        except KeyboardInterrupt:
            print("\n[INFO] Thoat monitor.")
            ser.close()
        return

    if arg not in valid_channels:
        print(f"[!] Tham so sai: '{arg}'")
        print("    Dung: 1, 2, 3, 4, stop, monitor")
        ser.close()
        sys.exit(1)

    if speed not in valid_speeds:
        print(f"[!] Toc do sai: '{speed}'. Dung: v (rat cham), l (cham), m (vua), f (nhanh)")
        ser.close()
        sys.exit(1)

    # Gui toc do truoc
    print(f"[INFO] Set toc do: '{speed}'")
    ser.write(speed.encode())
    time.sleep(0.2)
    while ser.in_waiting:
        print(f"  [ARDUINO] {ser.readline().decode(errors='ignore').rstrip()}")

    # Gui lenh chon kenh
    print(f"[INFO] Quay kenh {arg}...")
    ser.write(arg.encode())
    time.sleep(0.2)

    # In output Arduino lien tuc cho den khi Ctrl+C
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
        while ser.in_waiting:
            print(f"  [ARDUINO] {ser.readline().decode(errors='ignore').rstrip()}")
    finally:
        ser.close()
        print("[INFO] Da dong ket noi.")


if __name__ == "__main__":
    main()
