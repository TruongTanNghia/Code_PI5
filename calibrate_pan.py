"""
DO VUNG TUAN TRA PAN - NHICH TUNG BUOC NHO (an toan, khong chay ao).

Moi lan bam phim, motor nhich 1 BUOC NHO roi DUNG NGAY. Khong chay lien tuc.
Co camera de nhin. Danh dau mep TRAI/PHAI, luu vao pan_range.txt.

CACH DUNG:
    py calibrate_pan.py

PHIM (bam trong cua so camera):
    A / mui ten TRAI  = nhich TRAI 1 buoc
    D / mui ten PHAI  = nhich PHAI 1 buoc
    (giu phim = nhich lien tuc tung buoc, nha ra la dung)
    W = tang buoc nhich (di nhanh hon)
    S = giam buoc nhich (di cham hon, ti mi hon)
    Z = set vi tri hien tai = 0 (tam)
    1 = danh dau MEP TRAI  + luu
    2 = danh dau MEP PHAI  + luu
    SPACE = dung khan cap
    ESC = thoat
"""
import sys
import time
import glob

import cv2
import numpy as np

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("[!] Chua cai pyserial. Chay: pip install pyserial")
    sys.exit(1)

IS_WINDOWS = sys.platform.startswith("win")
PAN_RANGE_FILE = "pan_range.txt"

NUDGE_SPS = 200          # toc do khi nhich (cham)
step_size = 40           # so step moi lan bam phim (chinh bang W/S)
STEP_MIN, STEP_MAX = 5, 400


def find_arduino_port():
    if IS_WINDOWS:
        ports = [p for p in serial.tools.list_ports.comports()
                 if p.device.upper() != "COM1"]
        for p in ports:
            d = (p.description or "").lower()
            if any(k in d for k in ("arduino", "ch340", "ch9102", "cp210",
                                    "ftdi", "silicon labs", "usb-serial", "usb serial")):
                return p.device
        return ports[0].device if ports else None
    cands = sorted(glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*"))
    return cands[0] if cands else None


def open_camera():
    backends = ([cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY] if IS_WINDOWS
                else [cv2.CAP_V4L2, cv2.CAP_ANY])
    for idx in range(0, 6):
        for be in backends:
            cap = cv2.VideoCapture(idx, be)
            if cap.isOpened():
                ok, fr = cap.read()
                if ok and fr is not None and fr.size > 0:
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    print(f"[INFO] Camera OK: index={idx}")
                    return cap
            cap.release()
    return None


def main():
    global step_size

    port = find_arduino_port()
    if not port:
        print("[!] Khong tim thay Arduino.")
        sys.exit(1)
    print(f"[INFO] Arduino: {port}")
    ser = serial.Serial(port, 9600, timeout=0.1)
    ser.setDTR(False)
    time.sleep(2)
    ser.reset_input_buffer()
    ser.write(b"S")   # SCAN mode: Arduino khong tu chan, minh tu lai
    ser.flush()

    def send(s):
        ser.write(s.encode())
        ser.flush()

    def nudge(direction):
        """Nhich 1 buoc nho: chay NUDGE_SPS trong thoi gian = step/sps, roi dung."""
        nonlocal_pos = step_size * direction
        dur = step_size / NUDGE_SPS
        send(f"P{NUDGE_SPS * direction}\n")
        time.sleep(dur)
        send("P0\n")
        return nonlocal_pos

    cap = open_camera()
    pan_pos = 0.0
    mark_left = None
    mark_right = None

    import os
    if os.path.exists(PAN_RANGE_FILE):
        try:
            with open(PAN_RANGE_FILE) as f:
                lo, hi = f.read().strip().split(",")
                mark_left, mark_right = int(lo), int(hi)
                print(f"[INFO] File cu: TRAI={mark_left} PHAI={mark_right}")
        except Exception:
            pass

    def save_file():
        l = int(mark_left) if mark_left is not None else 0
        r = int(mark_right) if mark_right is not None else 0
        lo, hi = min(l, r), max(l, r)
        with open(PAN_RANGE_FILE, "w") as f:
            f.write(f"{lo},{hi}")
        print(f"[CAL] >>> LUU pan_range.txt: TRAI={lo} PHAI={hi} (rong {hi-lo})")

    print("[INFO] San sang. Bam A/D nhich, 1/2 danh dau, ESC thoat.")

    try:
        while True:
            frame = None
            if cap is not None:
                ok, fr = cap.read()
                if ok and fr is not None:
                    frame = fr
            if frame is None:
                frame = np.zeros((480, 640, 3), dtype=np.uint8)

            def put(t, y, c=(0, 255, 255), s=0.6):
                cv2.putText(frame, t, (12, y), cv2.FONT_HERSHEY_SIMPLEX, s, c, 2)

            put("DO VUNG TUAN TRA PAN", 30, (0, 255, 0))
            put(f"VI TRI: {int(pan_pos)} step", 65, (255, 255, 0), 0.8)
            put(f"Buoc nhich: {step_size} step  (W=tang S=giam)", 95, (255, 200, 0), 0.5)
            put(f"MEP TRAI(1): {int(mark_left) if mark_left is not None else '--'}", 125)
            put(f"MEP PHAI(2): {int(mark_right) if mark_right is not None else '--'}", 150)
            if mark_left is not None and mark_right is not None:
                put(f"=> Rong vung: {abs(int(mark_right)-int(mark_left))} step", 175, (0, 255, 0))
            put("A=trai  D=phai (nhich tung buoc)", 430, (200, 200, 200), 0.5)
            put("1=mep trai  2=mep phai  Z=set0  ESC=thoat", 455, (200, 200, 200), 0.5)

            cv2.imshow("Calibrate PAN", frame)
            key = cv2.waitKey(20) & 0xFF

            if key == 27:
                break
            elif key in (ord('a'), 81):       # 81 = mui ten trai
                pan_pos += nudge(-1)
            elif key in (ord('d'), 83):       # 83 = mui ten phai
                pan_pos += nudge(+1)
            elif key == ord('w'):
                step_size = min(STEP_MAX, step_size + 10)
                print(f"[CAL] buoc nhich = {step_size}")
            elif key == ord('s'):
                step_size = max(STEP_MIN, step_size - 10)
                print(f"[CAL] buoc nhich = {step_size}")
            elif key == ord(' '):
                send("P0\n")
            elif key == ord('z'):
                pan_pos = 0.0
                print("[CAL] set vi tri = 0")
            elif key == ord('1'):
                mark_left = pan_pos
                print(f"[CAL] MEP TRAI = {int(pan_pos)}")
                save_file()
            elif key == ord('2'):
                mark_right = pan_pos
                print(f"[CAL] MEP PHAI = {int(pan_pos)}")
                save_file()

    except KeyboardInterrupt:
        print("\n[INFO] Ctrl+C")
    finally:
        send("P0\n"); send("T0\n"); send("x")
        time.sleep(0.2)
        ser.close()
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()
        print("[INFO] Da dung motor + dong ket noi.")


if __name__ == "__main__":
    main()
