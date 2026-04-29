"""
Test ket noi Arduino qua UART (RX/TX cua Pi5 GPIO14/15).

YEU CAU:
- Pi5 GPIO14 (TX, chan 8)  -> Arduino RX (D0)
- Arduino TX (D1) -> divider 1K/2K -> Pi5 GPIO15 (RX, chan 10)
- Pi5 GND -> Arduino GND
- Arduino phai co nguon RIENG (DC jack 9V hoac Vin tu chan 5V Pi)
- Da bat UART trong raspi-config

Cach dung:
    python test_arduino_uart.py
"""
import sys
import time
import os

try:
    import serial
except ImportError:
    print("[!] Chua cai pyserial. Chay: pip install pyserial")
    sys.exit(1)


PORT = "/dev/serial0"
BAUD = 9600

print(f"=== TEST KET NOI ARDUINO QUA UART ===")
print(f"Port: {PORT}")
print(f"Baud: {BAUD}")
print()

# Verify UART available
if not os.path.exists(PORT):
    print(f"[!] Khong co {PORT}.")
    print("    Bat UART: sudo raspi-config -> Interface -> Serial Port -> Hardware: YES")
    sys.exit(1)

# Mo port
try:
    ser = serial.Serial(PORT, BAUD, timeout=2.0)
    print(f"[OK] Mo port thanh cong")
except serial.SerialException as e:
    print(f"[!] Loi mo port: {e}")
    print("    Permission? Chay: sudo usermod -a -G dialout $USER (roi logout/login)")
    sys.exit(1)

# UART KHONG reset Arduino tu dong (khac voi USB)
# Nen ta gui '1' truc tiep va doi phan hoi
print(f"[INFO] UART khong tu reset Arduino. Bo qua banner check.")
print()

# === TEST 1: Doc xem co data trong buffer khong ===
print("--- TEST 1: Doc trong 2 giay ---")
got_anything = False
end_time = time.time() + 2
while time.time() < end_time:
    if ser.in_waiting:
        try:
            line = ser.readline().decode(errors="ignore").rstrip()
            if line:
                print(f"   [ARDUINO] {line}")
                got_anything = True
        except Exception as e:
            print(f"   [LOI] {e}")

if not got_anything:
    print("   (Khong co data - binh thuong neu Arduino dang idle)")

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

if not got_response:
    print("[X] Arduino khong phan hoi gi sau 5s.")
    print("    Co the:")
    print("    - Arduino chua cap nguon (USB rut roi -> can DC jack hoac Vin)")
    print("    - UART RX/TX dau sai (kiem tra TX -> RX, RX -> TX)")
    print("    - Voltage divider sai (Arduino TX 5V -> 1K -> Pi RX, 2K xuong GND)")
    print("    - Pi5 chua bat UART (raspi-config)")
else:
    print()
    print("[OK] Arduino phan hoi -> UART HOAT DONG!")

# === TEST 3: Gui '2' de test them lan nua ===
print()
print("--- TEST 3: Gui '2' de chac chan 2 chieu ---")
print("(Cho 1 phut neu motor 1 dang quay het 1000 step truoc do)")
print()
time.sleep(5)  # cho motor 1 xong
ser.reset_input_buffer()
ser.write(b'2')
print("[INFO] Da gui: '2'")

got_response2 = False
end_time = time.time() + 8
while time.time() < end_time:
    if ser.in_waiting:
        try:
            line = ser.readline().decode(errors="ignore").rstrip()
            if line:
                print(f"   [ARDUINO] {line}")
                got_response2 = True
        except Exception:
            pass

# Tom tat
print()
print("=" * 50)
print(" TOM TAT")
print("=" * 50)
print(f"  Gui '1' -> Arduino phan hoi: {'OK' if got_response else 'FAIL'}")
print(f"  Gui '2' -> Arduino phan hoi: {'OK' if got_response2 else 'FAIL'}")

if got_response and got_response2:
    print()
    print("[!] UART thong suot 2 chieu.")
    print("    Neu motor van khong quay -> kiem tra dau noi 5V/GND/CW-")

ser.close()
print()
print("[INFO] Da dong port.")
