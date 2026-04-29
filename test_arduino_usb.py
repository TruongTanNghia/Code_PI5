"""
Test ket noi Arduino qua USB - DON GIAN NHAT.

Cach dung:
    python test_arduino_usb.py
    python test_arduino_usb.py /dev/ttyUSB1   # neu port khac
"""
import sys
import time
import glob

try:
    import serial
except ImportError:
    print("[!] Chua cai pyserial. Chay: pip install pyserial")
    sys.exit(1)


# Tim port USB
def find_usb_port():
    candidates = sorted(glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*'))
    if not candidates:
        return None
    return candidates[0]


# Lay port tu CLI hoac auto-detect
port = sys.argv[1] if len(sys.argv) > 1 else find_usb_port()

if not port:
    print("[!] Khong tim thay /dev/ttyUSB* hoac /dev/ttyACM*")
    print("    Cam Arduino vao Pi5 chua? Thu: lsusb")
    sys.exit(1)

print(f"=== TEST KET NOI ARDUINO ===")
print(f"Port: {port}")
print(f"Baud: 9600")
print()

# Mo port
try:
    ser = serial.Serial(port, 9600, timeout=2.0)
    print(f"[OK] Mo port thanh cong")
except serial.SerialException as e:
    print(f"[!] Loi mo port: {e}")
    sys.exit(1)

# Doi Arduino reset (DTR auto-reset khi mo USB serial)
print(f"[INFO] Doi 2s cho Arduino reset...")
time.sleep(2.0)

# === TEST 1: Doc xem Arduino tu in gi khong ===
print()
print("--- TEST 1: Doc banner Arduino (5 giay) ---")
got_anything = False
end_time = time.time() + 5
while time.time() < end_time:
    if ser.in_waiting:
        try:
            line = ser.readline().decode(errors="ignore").rstrip()
            if line:
                print(f"   [ARDUINO] {line}")
                got_anything = True
        except Exception as e:
            print(f"   [LOI] {e}")

if got_anything:
    print()
    print("[OK] Arduino dang gui du lieu -> KET NOI THANH CONG!")
else:
    print()
    print("[X] Khong nhan duoc gi tu Arduino sau 5s.")
    print("    Co the:")
    print("    - Arduino chua cap nguon (cam USB chac chan)")
    print("    - Sai port")
    print("    - Sai baud rate (code Arduino can dung 9600)")

# === TEST 2: Gui '1' va doc phan hoi ===
print()
print("--- TEST 2: Gui '1' den Arduino, doi 5s phan hoi ---")
ser.reset_input_buffer()
ser.write(b'1')
print("[INFO] Da gui: '1'")

got_response = False
end_time = time.time() + 5
while time.time() < end_time:
    if ser.in_waiting:
        try:
            line = ser.readline().decode(errors="ignore").rstrip()
            if line:
                print(f"   [ARDUINO] {line}")
                got_response = True
        except Exception:
            pass

if got_response:
    print()
    print("[OK] Arduino phan hoi lenh '1' -> 2 CHIEU OK!")
else:
    print()
    print("[X] Arduino khong phan hoi lenh '1'.")

# Tom tat
print()
print("=" * 50)
print(" TOM TAT")
print("=" * 50)
print(f"  Doc tu Arduino: {'OK' if got_anything else 'FAIL'}")
print(f"  Gui den Arduino: {'OK' if got_response else 'FAIL'}")

ser.close()
print()
print("[INFO] Da dong port.")
