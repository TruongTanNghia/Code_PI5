"""
CALIBRATE TAM QUET PAN (trai/phai) bang TOA DO.

Anh lai pan trai/phai bang phim, danh dau 2 bien TRAI va PHAI,
roi luu vao file pan_range.txt. main.py se tu dung tam quet do.

KHONG can cong tac hanh trinh - dem toa do bang phan mem.

CACH DUNG:
    py calibrate_pan.py

PHIM (bam trong cua so "Calibrate PAN"):
    D = quay PHAI (giu/bam nhieu lan)
    A = quay TRAI
    SPACE = DUNG
    Z = set vi tri hien tai = 0 (tam)
    1 = danh dau BIEN TRAI  (o vi tri hien tai)
    2 = danh dau BIEN PHAI  (o vi tri hien tai)
    S = LUU ra file pan_range.txt
    ESC = thoat (tu dung motor)

QUY TRINH:
    1. Bam A/D lai camera ve giua tam quet -> bam Z (set 0)
    2. Bam A quay TRAI het muc an toan -> bam 1 (danh dau bien trai)
    3. Bam D quay PHAI het muc an toan -> bam 2 (danh dau bien phai)
    4. Bam S de luu. Xong!
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
JOG_SPS = 500   # toc do lai tay (step/s) - vua phai, an toan


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


def main():
    port = find_arduino_port()
    if not port:
        print("[!] Khong tim thay Arduino.")
        sys.exit(1)
    print(f"[INFO] Arduino: {port}")
    ser = serial.Serial(port, 9600, timeout=0.1)
    ser.setDTR(False)
    time.sleep(2)
    ser.reset_input_buffer()

    def send(s):
        ser.write(s.encode())
        ser.flush()

    pan_pos = 0.0
    jog_dir = 0           # -1 trai, 0 dung, +1 phai
    last_sps = 0
    mark_left = None
    mark_right = None
    prev_t = time.time()

    print("[INFO] San sang. Bam phim trong cua so 'Calibrate PAN'.")

    try:
        while True:
            now = time.time()
            dt = now - prev_t
            prev_t = now

            # Tich phan vi tri
            pan_pos += last_sps * dt

            # ===== Ve giao dien =====
            img = np.zeros((360, 640, 3), dtype=np.uint8)
            def put(t, y, c=(0, 255, 255), s=0.6):
                cv2.putText(img, t, (15, y), cv2.FONT_HERSHEY_SIMPLEX, s, c, 1)

            put("CALIBRATE PAN - do tam quet bang toa do", 30, (0, 255, 0), 0.6)
            put(f"VI TRI HIEN TAI: {int(pan_pos)} step", 75, (255, 255, 0), 0.8)
            dir_txt = "PHAI ->" if jog_dir > 0 else ("<- TRAI" if jog_dir < 0 else "DUNG")
            put(f"Dang chay: {dir_txt}", 110)
            put(f"Bien TRAI (1): {int(mark_left) if mark_left is not None else '---'}", 150)
            put(f"Bien PHAI (2): {int(mark_right) if mark_right is not None else '---'}", 180)
            if mark_left is not None and mark_right is not None:
                rng = (mark_right - mark_left)
                put(f"=> Tam quet rong: {int(rng)} step", 210, (0, 255, 0))
            put("D=phai  A=trai  SPACE=dung  Z=set0", 260, (200, 200, 200), 0.5)
            put("1=danh dau TRAI  2=danh dau PHAI", 285, (200, 200, 200), 0.5)
            put("S=luu file  ESC=thoat", 310, (200, 200, 200), 0.5)

            cv2.imshow("Calibrate PAN", img)
            key = cv2.waitKey(30) & 0xFF

            if key == 27:        # ESC
                break
            elif key == ord('d'):
                jog_dir = +1
                last_sps = JOG_SPS
                send(f"P{JOG_SPS}\n")
            elif key == ord('a'):
                jog_dir = -1
                last_sps = -JOG_SPS
                send(f"P{-JOG_SPS}\n")
            elif key == ord(' '):
                jog_dir = 0
                last_sps = 0
                send("P0\n")
            elif key == ord('z'):
                pan_pos = 0.0
                print("[CAL] set vi tri = 0 (tam)")
            elif key == ord('1'):
                mark_left = pan_pos
                print(f"[CAL] danh dau BIEN TRAI = {int(pan_pos)}")
            elif key == ord('2'):
                mark_right = pan_pos
                print(f"[CAL] danh dau BIEN PHAI = {int(pan_pos)}")
            elif key == ord('s'):
                if mark_left is None or mark_right is None:
                    print("[!] Chua danh dau du 2 bien (bam 1 va 2 truoc).")
                else:
                    lo = int(min(mark_left, mark_right))
                    hi = int(max(mark_left, mark_right))
                    with open(PAN_RANGE_FILE, "w") as f:
                        f.write(f"{lo},{hi}")
                    print(f"[CAL] DA LUU pan_range.txt: min={lo}, max={hi}")
                    print(f"      main.py se quet pan trong khoang nay.")

    except KeyboardInterrupt:
        print("\n[INFO] Ctrl+C")
    finally:
        send("P0\n")
        send("T0\n")
        send("x")
        time.sleep(0.2)
        ser.close()
        cv2.destroyAllWindows()
        print("[INFO] Da dung motor + dong ket noi.")


if __name__ == "__main__":
    main()
