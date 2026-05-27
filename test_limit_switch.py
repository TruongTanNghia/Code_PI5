"""
TEST 4 CONG TAC HANH TRINH BANG PYTHON

Dung CHUNG voi 'arduino_stepper_laser.ino' (ban moi co lenh '+' auto-report).
Python gui '+' de bat che do tu dong in, roi doc trang thai cong tac.

CACH DUNG:
1. Nap 'arduino_stepper_laser.ino' (ban moi) vao Arduino.
2. DONG Serial Monitor cua Arduino IDE neu dang mo (khong se bi chiem cong).
3. Sua PORT ben duoi cho dung (Windows: COM3..., Linux/Pi: /dev/ttyUSB0).
4. Chay: py test_limit_switch.py
5. Nhan tung cong tac, xem dong in ra doi trang thai. Ctrl+C de thoat.
"""

import sys
import time
import serial

# ===== CAU HINH CONG =====
if sys.platform.startswith("win"):
    PORT = "COM3"          # <<< DOI cho dung COM cua Arduino tren Windows
else:
    PORT = "/dev/ttyUSB0"  # tren Raspberry Pi / Linux
BAUD = 9600


def main():
    try:
        ser = serial.Serial(PORT, BAUD, timeout=1)
    except serial.SerialException as e:
        print(f"[LOI] Khong mo duoc cong {PORT}: {e}")
        print("  - Kiem tra Arduino da cam chua")
        print("  - Dong Serial Monitor cua Arduino IDE neu dang mo")
        print("  - Sua bien PORT cho dung COM/tty")
        return

    time.sleep(2)            # cho Arduino reset sau khi mo cong
    ser.reset_input_buffer()
    ser.write(b"+")          # bat che do auto-report tren Arduino
    ser.flush()

    print(f"[OK] Da ket noi {PORT}. Da bat auto-report.")
    print("     Nhan tung cong tac de test. Ctrl+C de thoat.\n")

    try:
        while True:
            line = ser.readline().decode(errors="ignore").strip()
            if line:
                print(line)
    except KeyboardInterrupt:
        print("\n[THOAT] Da dung.")
    finally:
        ser.write(b"-")     # tat auto-report cho sach
        ser.flush()
        ser.close()


if __name__ == "__main__":
    main()
 