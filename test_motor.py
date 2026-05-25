"""
Test 2 motor (pan + tilt) qua Arduino bang ban phim. Chay tren Windows.

Yeu cau:
- Arduino da upload arduino/motor_stepper/motor_stepper.ino (hoac motor_dc.ino)
- pip install pyserial

Cach dung:
    py test_motor.py             # che do interactive (an phim WASD)
    py test_motor.py auto        # tu dong chay test tat ca motor 2s/cai

PHIM DIEU KHIEN (interactive):
    D = pan PHAI       A = pan TRAI       H = dung pan
    W = tilt LEN       S = tilt XUONG     V = dung tilt
    X = STOP TAT CA
    L = laser ON       K = laser OFF
    Q = thoat
"""
import sys
import time
import serial
import serial.tools.list_ports


def find_arduino():
    """Tu dong tim Arduino COM port (bo qua COM1, uu tien CH340/Arduino)."""
    ports = list(serial.tools.list_ports.comports())
    # Bo qua COM1 (cong noi bo Windows)
    ports = [p for p in ports if p.device.upper() != "COM1"]

    # Uu tien Arduino/CH340/USB-Serial
    for p in ports:
        desc = (p.description or "").lower()
        if any(k in desc for k in ("arduino", "ch340", "ch9102", "cp210",
                                   "ftdi", "silicon labs", "usb-serial",
                                   "usb serial")):
            return p.device

    # Fallback: COM khac COM1 dau tien
    return ports[0].device if ports else None


def open_arduino():
    port = find_arduino()
    if not port:
        print("[!] Khong tim thay Arduino. Kiem tra Device Manager (Ports COM).")
        sys.exit(1)
    print(f"[INFO] Mo {port} @ 9600...")
    ser = serial.Serial(port, 9600, timeout=0.1)
    ser.setDTR(False)
    time.sleep(2)
    # Drain bat ky byte gi co san
    while ser.in_waiting:
        ser.read(ser.in_waiting)
    print("[OK] Da ket noi Arduino")
    return ser


def send(ser, cmd):
    print(f"  [SEND] '{cmd}'")
    ser.write(cmd.encode())
    ser.flush()


# =================== AUTO MODE ===================
def run_auto(ser):
    """Tu dong chay test tat ca motor + laser."""
    seq = [
        ("Pan PHAI 2s",   "d", "h", 2.0),
        ("Pan TRAI 2s",   "a", "h", 2.0),
        ("Tilt LEN 2s",   "w", "v", 2.0),
        ("Tilt XUONG 2s", "s", "v", 2.0),
        ("Laser ON 1s",   "L", "K", 1.0),
    ]

    print("\n========== AUTO TEST ==========")
    print("Quan sat 2 motor + laser theo thu tu.")
    print("Ctrl+C de dung som.\n")

    try:
        for name, start_cmd, stop_cmd, duration in seq:
            print(f"==> {name}")
            send(ser, start_cmd)
            time.sleep(duration)
            send(ser, stop_cmd)
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[!] Ctrl+C - dung som")
    finally:
        send(ser, 'x')
        send(ser, 'K')
        print("\n[INFO] Test xong.")


# =================== INTERACTIVE MODE ===================
def run_interactive(ser):
    """Doc phim ban phim real-time (Windows: msvcrt)."""
    try:
        import msvcrt
    except ImportError:
        print("[!] msvcrt chi co tren Windows. Linux dung 'auto' mode.")
        sys.exit(1)

    valid_keys = {
        'd': 'd',  'a': 'a',  'h': 'h',
        'w': 'w',  's': 's',  'v': 'v',
        'x': 'x',
        'l': 'L',  'k': 'K',
    }

    print("\n========== INTERACTIVE TEST ==========")
    print("Phim:")
    print("  D = pan PHAI       A = pan TRAI       H = dung pan")
    print("  W = tilt LEN       S = tilt XUONG     V = dung tilt")
    print("  X = STOP TAT CA")
    print("  L = laser ON       K = laser OFF")
    print("  Q = thoat")
    print()
    print("Bam phim de gui lenh:")

    try:
        while True:
            if msvcrt.kbhit():
                key_byte = msvcrt.getch()
                try:
                    key = key_byte.decode(errors="ignore").lower()
                except Exception:
                    continue

                if key == 'q':
                    print("\n[INFO] Thoat.")
                    break

                if key in valid_keys:
                    send(ser, valid_keys[key])
                # bo qua phim khac
            else:
                time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n[!] Ctrl+C")
    finally:
        send(ser, 'x')
        send(ser, 'K')
        time.sleep(0.2)


# =================== MAIN ===================
def main():
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "interactive"

    ser = open_arduino()

    try:
        if mode in ("auto", "a"):
            run_auto(ser)
        else:
            run_interactive(ser)
    finally:
        try:
            ser.close()
            print("[INFO] Da dong port.")
        except Exception:
            pass


if __name__ == "__main__":
    main()
