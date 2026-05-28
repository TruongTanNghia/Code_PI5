"""
TEST MOTOR STEPPER - BAN CO LOG DAY DU
Moi thu deu in ra man hinh: ket noi, lenh gui, Arduino tra ve, loi.

CACH DUNG:
  py test_motor.py
  Lenh:
    p 1000   pan phai | p -1000 pan trai | p 0 dung pan
    t 800    tilt xuong | t -800 len     | t 0 dung tilt
    L / K    laser on / off
    ?        in trang thai limit
    x        dung het
    q        thoat
"""

import sys
import time

print("=" * 50)
print("TEST MOTOR - khoi dong")
print("=" * 50)

# --- import serial, log neu thieu thu vien ---
try:
    import serial
    import serial.tools.list_ports
    print("[OK] da import pyserial")
except Exception as e:
    print(f"[LOI] khong import duoc pyserial: {e}")
    print("      Cai bang: pip install pyserial")
    sys.exit(1)

# --- liet ke cong COM dang co ---
print("\n[INFO] Cac cong COM dang co tren may:")
ports = list(serial.tools.list_ports.comports())
if not ports:
    print("   (KHONG thay cong nao! Arduino chua cam? chua cai driver CH340?)")
for p in ports:
    print(f"   {p.device} - {p.description}")

# --- chon cong ---
if sys.platform.startswith("win"):
    PORT = "COM3"
else:
    PORT = "/dev/ttyUSB0"
BAUD = 9600
print(f"\n[INFO] Se ket noi: {PORT} @ {BAUD}")
print("       (neu sai, sua bien PORT trong file)")

# --- mo cong, log loi chi tiet ---
try:
    ser = serial.Serial(PORT, BAUD, timeout=0.2)
    print(f"[OK] da mo {PORT}")
except serial.SerialException as e:
    print(f"[LOI] khong mo duoc {PORT}:")
    print(f"      {e}")
    print("      Nguyen nhan thuong gap:")
    print("      - Serial Monitor cua Arduino IDE dang mo (DONG no lai)")
    print("      - main.py / chuong trinh khac dang chiem cong")
    print("      - Sai so COM (xem list o tren)")
    sys.exit(1)
except Exception as e:
    print(f"[LOI] loi khac khi mo cong: {e}")
    sys.exit(1)

time.sleep(2)              # cho Arduino reset
ser.reset_input_buffer()
print("[OK] san sang. Go lenh ('q' de thoat).\n")


def gui(msg):
    """Gui lenh + log lai, bao loi neu co."""
    try:
        n = ser.write(msg.encode())
        ser.flush()
        print(f"   >>> da gui: {repr(msg)} ({n} byte)")
    except Exception as e:
        print(f"   [LOI] gui that bai: {e}")


def doc_arduino():
    """Doc moi thu Arduino tra ve, in ra."""
    try:
        while ser.in_waiting:
            line = ser.readline().decode(errors="ignore").strip()
            if line:
                print(f"   <<< Arduino: {line}")
    except Exception as e:
        print(f"   [LOI] doc that bai: {e}")


try:
    while True:
        doc_arduino()   # in bat ky gi Arduino gui truoc

        cmd = input(">> ").strip()
        if not cmd:
            continue

        if cmd == "q":
            break
        elif cmd == "x":
            gui("x")
        elif cmd == "L":
            gui("L")
        elif cmd == "K":
            gui("K")
        elif cmd == "?":
            gui("?")
            time.sleep(0.15)
            doc_arduino()
        elif cmd.startswith("p"):
            parts = cmd.split()
            sps = parts[1] if len(parts) > 1 else "0"
            gui(f"P{sps}\n")
        elif cmd.startswith("t"):
            parts = cmd.split()
            sps = parts[1] if len(parts) > 1 else "0"
            gui(f"T{sps}\n")
        else:
            print("   Lenh khong hieu. Vd: p 1000 | t -800 | L | K | ? | x | q")

        time.sleep(0.1)
        doc_arduino()

except KeyboardInterrupt:
    print("\n[INFO] Ctrl+C")
finally:
    try:
        gui("x")
        time.sleep(0.2)
        ser.close()
        print("[OK] da dong cong, dung het motor.")
    except Exception as e:
        print(f"[LOI] khi dong: {e}")
