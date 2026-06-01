"""
CALIBRATE OFFSET LASER (co webcam + laser bat lien tuc)

Mo cua so webcam de Anh nhin thay chom do laser tren khung hinh.
Laser BAT NGAY tu dau va SANG LIEN TUC.

CACH DUNG:
1. Dat muc tieu (con chuot mau / mieng giay co cham) o khoang cach thuc te.
2. Chay: py calibrate_laser.py
   -> Cua so cam mo + laser bat sang.
3. Cua so cam co CROSSHAIR XANH danh dau TAM camera (giua khung hinh).
4. Truoc khi calibrate, quay motor cho TAM CAMERA (crosshair xanh) trung vao
   tam muc tieu. Co the lam bang main.py (tracking) roi ESC, hoac dung A/D/W/S
   o day.
5. Sau khi tam cam trung muc tieu -> nhan '0' de re-zero offset.
6. Bay gio dieu chinh cho CHOM LASER (do tren cam) trung tam muc tieu:
     A / D = jog pan TRAI / PHAI
     W / S = jog tilt LEN / XUONG
     1..9  = so buoc moi nhan (1=1 buoc cham, 9=50 buoc nhanh)
     SPACE = tat/bat laser
     R     = reset offset ve 0
     0     = re-zero (coi vi tri hien tai la moi)
     ENTER = LUU offset hien tai vao laser_offset.txt
     Q     = thoat
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
    import cv2
except Exception as e:
    print(f"[LOI] thieu opencv: {e}  -> pip install opencv-python")
    sys.exit(1)

# ===== CONG =====
if sys.platform.startswith("win"):
    PORT = "COM5"
    cam_backend = cv2.CAP_DSHOW
else:
    PORT = "/dev/ttyUSB0"
    cam_backend = cv2.CAP_V4L2
BAUD = 9600
CAM_INDEX = 0
FRAME_W = 640
FRAME_H = 480
CONFIG_FILE = "laser_offset.txt"

# Toc do step/s khi jog (cham de chinh xac)
JOG_SPS = 400

# ===== MO SERIAL =====
try:
    ser = serial.Serial(PORT, BAUD, timeout=0.2)
except Exception as e:
    print(f"[LOI] khong mo duoc {PORT}: {e}")
    sys.exit(1)

time.sleep(2)
ser.reset_input_buffer()
print(f"[OK] Da ket noi {PORT}.")

# BAT LASER NGAY
ser.write(b"L")
ser.flush()
laser_on = True
print("[OK] LASER da BAT.")

# ===== MO CAM =====
cap = cv2.VideoCapture(CAM_INDEX, cam_backend)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_W)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_H)
cap.set(cv2.CAP_PROP_FPS, 30)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

if not cap.isOpened():
    print(f"[LOI] Khong mo duoc webcam o index {CAM_INDEX}")
    ser.write(b"K"); ser.close()
    sys.exit(1)

print("[OK] Da mo webcam.")
print("\n=== PHIM TAT (nhan tren cua so cam) ===")
print(" A/D = pan trai/phai   |   W/S = tilt len/xuong")
print(" 1-9 = so buoc moi nhan (1=1 buoc, 9=50 buoc)")
print(" SPACE = tat/bat laser    R = reset offset")
print(" 0 = re-zero tai vi tri hien tai")
print(" ENTER = LUU offset      Q hoac ESC = thoat\n")


def send(s):
    ser.write(s.encode())
    ser.flush()


def jog(axis, steps):
    """Quay 'axis' (P/T) them 'steps' buoc voi toc do JOG_SPS, roi dung."""
    if steps == 0:
        return
    direction = 1 if steps > 0 else -1
    sps = JOG_SPS * direction
    duration = abs(steps) / JOG_SPS
    send(f"{axis}{sps}\n")
    time.sleep(duration)
    send(f"{axis}0\n")


# ===== TRANG THAI =====
offset_pan = 0
offset_tilt = 0
step_per_press = 5
STEP_LEVELS = [1, 2, 5, 10, 15, 20, 30, 40, 50]

# Load offset cu (neu co)
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE) as f:
            parts = f.read().strip().split(",")
            offset_pan = int(parts[0])
            offset_tilt = int(parts[1])
            print(f"[INFO] Loaded offset cu: pan={offset_pan}, tilt={offset_tilt}")
    except Exception:
        pass


try:
    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            continue
        h, w = frame.shape[:2]
        cx, cy = w // 2, h // 2

        # Ve crosshair XANH tai TAM CAMERA
        cv2.drawMarker(frame, (cx, cy), (0, 255, 0),
                       markerType=cv2.MARKER_CROSS, markerSize=30, thickness=2)
        cv2.circle(frame, (cx, cy), 25, (0, 255, 0), 1)

        # Hien thong tin
        cv2.putText(frame,
                    f"OFFSET steps: pan={offset_pan}  tilt={offset_tilt}",
                    (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(frame,
                    f"Step/nhan: {step_per_press} (phim 1-9)",
                    (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        cv2.putText(frame,
                    f"LASER: {'ON' if laser_on else 'OFF'} (SPACE)",
                    (10, 72),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (0, 0, 255) if laser_on else (200, 200, 200), 1)
        cv2.putText(frame,
                    "A/D pan  W/S tilt  ENTER=luu  R=reset  Q=thoat",
                    (10, h - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

        cv2.imshow("Calibrate Laser - chinh chom do trung muc tieu", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == 0xFF:
            continue

        if key == 27 or key == ord('q'):   # ESC hoac Q
            break

        elif key == ord('a'):   # pan trai
            jog("P", -step_per_press)
            offset_pan -= step_per_press
            print(f"  offset=({offset_pan}, {offset_tilt})")
        elif key == ord('d'):   # pan phai
            jog("P", +step_per_press)
            offset_pan += step_per_press
            print(f"  offset=({offset_pan}, {offset_tilt})")
        elif key == ord('w'):   # tilt len
            jog("T", -step_per_press)
            offset_tilt -= step_per_press
            print(f"  offset=({offset_pan}, {offset_tilt})")
        elif key == ord('s'):   # tilt xuong
            jog("T", +step_per_press)
            offset_tilt += step_per_press
            print(f"  offset=({offset_pan}, {offset_tilt})")

        elif key == ord(' '):   # space = tat/bat laser
            laser_on = not laser_on
            send("L" if laser_on else "K")
            print(f"  Laser: {'ON' if laser_on else 'OFF'}")

        elif key == ord('r'):   # reset offset
            offset_pan = 0
            offset_tilt = 0
            print("  RESET offset = (0, 0)")
        elif key == ord('0'):   # re-zero
            offset_pan = 0
            offset_tilt = 0
            print("  RE-ZERO tai vi tri hien tai -> offset = (0, 0)")

        elif key == 13 or key == 10:   # ENTER
            with open(CONFIG_FILE, "w") as f:
                f.write(f"{offset_pan},{offset_tilt}\n")
            print(f"  [LUU] {CONFIG_FILE}: pan={offset_pan}, tilt={offset_tilt}")

        elif ord('1') <= key <= ord('9'):
            idx = key - ord('1')
            step_per_press = STEP_LEVELS[idx]
            print(f"  Step/nhan = {step_per_press}")

except KeyboardInterrupt:
    pass

finally:
    send("K")           # tat laser
    send("P0\n")
    send("T0\n")
    time.sleep(0.2)
    ser.close()
    cap.release()
    cv2.destroyAllWindows()
    print("[OK] Da dong cong + dong cam.")