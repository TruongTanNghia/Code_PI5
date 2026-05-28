"""
TEST MOTOR BANG PHIM A W S D (real-time)

Dung voi 'arduino_stepper_laser.ino'.
  A = pan trai     D = pan phai
  W = tilt len     S = tilt xuong
  (tha phim/nhan phim khac = dung)
  Q = thoat

Can cai thu vien 'keyboard':
  pip install keyboard
(Tren Windows co the can chay bang quyen Administrator de bat phim)

Neu khong cai duoc keyboard -> dung test_motor.py (go lenh + Enter).
"""

import sys
import time

try:
    import serial
except Exception as e:
    print(f"[LOI] thieu pyserial: {e}  -> pip install pyserial")
    sys.exit(1)

try:
    import keyboard
except Exception as e:
    print(f"[LOI] thieu thu vien keyboard: {e}")
    print("      Cai: pip install keyboard")
    print("      (hoac dung test_motor.py go lenh tay)")
    sys.exit(1)

# ===== CONG =====
if sys.platform.startswith("win"):
    PORT = "COM3"
else:
    PORT = "/dev/ttyUSB0"
BAUD = 9600

SPEED = 1500   # step/s khi nhan phim (chinh tuy y)

try:
    ser = serial.Serial(PORT, BAUD, timeout=0.2)
except Exception as e:
    print(f"[LOI] khong mo duoc {PORT}: {e}")
    print("      - Dong Serial Monitor / chuong trinh khac dang chiem cong")
    sys.exit(1)

time.sleep(2)
ser.reset_input_buffer()
print(f"[OK] Da ket noi {PORT}.")
print("Giu phim: A=trai D=phai W=len S=xuong | Q=thoat")
print("Tha phim = dung.\n")


def send(s):
    ser.write(s.encode())
    ser.flush()


# Trang thai truoc do de chi gui khi doi (do spam)
last_pan = 0
last_tilt = 0

try:
    while True:
        # doc Arduino tra ve (neu co)
        while ser.in_waiting:
            line = ser.readline().decode(errors="ignore").strip()
            if line:
                print("  [ARD]", line)

        if keyboard.is_pressed('q'):
            break

        # ===== PAN =====
        if keyboard.is_pressed('d'):
            pan = SPEED        # phai
        elif keyboard.is_pressed('a'):
            pan = -SPEED       # trai
        else:
            pan = 0

        # ===== TILT =====
        if keyboard.is_pressed('s'):
            tilt = SPEED       # xuong
        elif keyboard.is_pressed('w'):
            tilt = -SPEED      # len
        else:
            tilt = 0

        # chi gui khi thay doi
        if pan != last_pan:
            send(f"P{pan}\n")
            print(f"  >>> P{pan}")
            last_pan = pan
        if tilt != last_tilt:
            send(f"T{tilt}\n")
            print(f"  >>> T{tilt}")
            last_tilt = tilt

        time.sleep(0.02)

except KeyboardInterrupt:
    pass
finally:
    send("x")
    time.sleep(0.2)
    ser.close()
    print("\n[THOAT] Da dung motor.")
