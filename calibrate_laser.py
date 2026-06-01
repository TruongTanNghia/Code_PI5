"""
CALIBRATE OFFSET LASER (so buoc stepper)

Muc dich: do GOC LECH giua tam camera va tia laser, tinh theo SO BUOC stepper.
Sau khi calibrate, file 'laser_offset.txt' se chua 2 so (pan_steps, tilt_steps).
File main.py se doc 2 so do, moi khi vao deadzone se quay them so buoc do
de laser truoc khi ban.

CACH DUNG:
1. Dat 1 vat the (vd con chuot, hoac giay co diem dau) o KHOANG CACH thuc te.
2. Mo cam Anh dung (vd realsense-viewer / mat) -> dam bao TAM camera (giua khung
   hinh) chieu vao DUNG TAM VAT THE. Co the dung mat thuong nhin vao webcam.
   (NEU dung main.py thi cho tracking dua tam camera vao tam chuot xong ESC).
3. Chay file nay: py calibrate_laser.py
4. Bat laser bang phim ' ' (space). Laser se sang.
5. Dung phim:
     A / D = jog pan TRAI / PHAI
     W / S = jog tilt LEN / XUONG
     1..9  = chinh so buoc jog moi lan nhan (1=1 buoc cham, 9=50 buoc nhanh)
     SPACE = bat/tat laser
     R     = reset offset ve 0
     0     = re-zero (coi vi tri hien tai la moi)
     ENTER = LUU offset hien tai vao file laser_offset.txt
     Q     = thoat (khong luu)
6. Jog motor cho den khi LASER CHIEU TRUNG TAM vat the.
   Luc do, so step hien tai chinh la offset can luu.
7. Nhan ENTER de luu.

LUU Y:
- Calibrate o KHOANG CACH thuc te se dung muc tieu (tia laser va tia cam
  song song nhung lech nhau 1 doan -> tai khoang cach xa, lech pixel khac,
  nhung lech goc/buoc stepper la CO DINH).
- Sau khi calibrate, KHONG di chuyen vi tri tuong doi cua laser va camera.
"""

import sys
import time
import os

try:
    import serial
except Exception as e:
    print(f"[LOI] thieu pyserial: {e}")
    sys.exit(1)

try:
    import keyboard
except Exception as e:
    print(f"[LOI] thieu thu vien keyboard: {e}")
    print("      Cai: pip install keyboard")
    sys.exit(1)

# ===== CONG =====
if sys.platform.startswith("win"):
    PORT = "COM5"
else:
    PORT = "/dev/ttyUSB0"
BAUD = 9600

CONFIG_FILE = "laser_offset.txt"

# Toc do step/s khi jog (cham de chinh xac)
JOG_SPS = 400

# Quy uoc dau: pan>0 = phai, tilt>0 = xuong (giong main.py)

try:
    ser = serial.Serial(PORT, BAUD, timeout=0.2)
except Exception as e:
    print(f"[LOI] khong mo duoc {PORT}: {e}")
    sys.exit(1)

time.sleep(2)
ser.reset_input_buffer()
print(f"[OK] Da ket noi {PORT}.")
print("Dung phim A/D/W/S jog motor. SPACE bat/tat laser.")
print("1-9 = so buoc moi nhan. R=reset. 0=re-zero. ENTER=luu. Q=thoat.\n")


def send(s):
    ser.write(s.encode())
    ser.flush()


def jog(axis, steps):
    """Quay 'axis' (P/T) them 'steps' buoc voi toc do JOG_SPS, roi dung."""
    if steps == 0:
        return
    direction = 1 if steps > 0 else -1
    sps = JOG_SPS * direction
    # Thoi gian = |steps| / JOG_SPS giay
    duration = abs(steps) / JOG_SPS
    send(f"{axis}{sps}\n")
    time.sleep(duration)
    send(f"{axis}0\n")


offset_pan = 0      # so buoc tich luy tu vi tri 0
offset_tilt = 0
step_per_press = 5  # so buoc moi lan nhan A/D/W/S, chinh bang 1-9
laser_on = False

# Load offset cu (neu co)
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE) as f:
            line = f.read().strip()
            parts = line.split(",")
            offset_pan = int(parts[0])
            offset_tilt = int(parts[1])
            print(f"[INFO] Da load offset cu: pan={offset_pan}, tilt={offset_tilt}")
    except Exception:
        pass

print(f"Step moi nhan: {step_per_press}\n")

# Trang thai phim de chong giu phim lap lai qua nhanh
last_press = {}
PRESS_COOLDOWN = 0.05   # giay giua 2 lan an phim

def just_pressed(key):
    """Tra ve True neu key vua duoc nhan (khong qua nhanh)."""
    now = time.time()
    if keyboard.is_pressed(key):
        last = last_press.get(key, 0)
        if now - last >= PRESS_COOLDOWN:
            last_press[key] = now
            return True
    else:
        last_press[key] = 0
    return False


try:
    while True:
        # Doc Arduino tra ve (neu co)
        while ser.in_waiting:
            line = ser.readline().decode(errors="ignore").strip()
            if line and not line.startswith("LIM:"):
                print(f"  [ARD] {line}")

        # Bat/tat laser bang space
        if just_pressed('space'):
            laser_on = not laser_on
            send("L" if laser_on else "K")
            print(f"  Laser: {'ON' if laser_on else 'OFF'}")

        # Chinh step_per_press bang phim so
        for i in range(1, 10):
            if just_pressed(str(i)):
                step_per_press = [1, 2, 5, 10, 15, 20, 30, 40, 50][i-1]
                print(f"  Step moi nhan = {step_per_press}")

        # Jog
        if just_pressed('a'):  # pan trai
            jog("P", -step_per_press)
            offset_pan -= step_per_press
            print(f"  offset_pan={offset_pan}, offset_tilt={offset_tilt}")
        elif just_pressed('d'):  # pan phai
            jog("P", +step_per_press)
            offset_pan += step_per_press
            print(f"  offset_pan={offset_pan}, offset_tilt={offset_tilt}")
        elif just_pressed('w'):  # tilt len
            jog("T", -step_per_press)
            offset_tilt -= step_per_press
            print(f"  offset_pan={offset_pan}, offset_tilt={offset_tilt}")
        elif just_pressed('s'):  # tilt xuong
            jog("T", +step_per_press)
            offset_tilt += step_per_press
            print(f"  offset_pan={offset_pan}, offset_tilt={offset_tilt}")

        # Reset
        if just_pressed('r'):
            offset_pan = 0
            offset_tilt = 0
            print(f"  RESET -> offset_pan=0, offset_tilt=0")

        # Re-zero
        if just_pressed('0'):
            offset_pan = 0
            offset_tilt = 0
            print(f"  RE-ZERO tai vi tri hien tai -> offset=(0,0)")

        # Luu
        if just_pressed('enter'):
            with open(CONFIG_FILE, "w") as f:
                f.write(f"{offset_pan},{offset_tilt}\n")
            print(f"  [LUU] Da ghi vao {CONFIG_FILE}: pan={offset_pan}, tilt={offset_tilt}")

        # Thoat
        if keyboard.is_pressed('q'):
            print("\nThoat...")
            break

        time.sleep(0.01)

except KeyboardInterrupt:
    pass
finally:
    send("K")           # tat laser
    send("P0\n")        # dung motor
    send("T0\n")
    time.sleep(0.2)
    ser.close()
    print("[OK] Da dong cong.")