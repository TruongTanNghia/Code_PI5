"""
CALIBRATE TAM QUET PAN (trai/phai) - CO CAMERA + CHAM CONG TAC DE DO CHUAN.

Lai pan trai/phai. Khi CHAM CONG TAC HANH TRINH that -> tu dong danh dau bien
+ dung motor (do chinh xac). Cung co the danh dau tay (1/2).
Luu toa do vao pan_range.txt -> main.py dung luon.

CACH DUNG:
    py calibrate_pan.py

PHIM (bam trong cua so camera):
    D = quay PHAI (cham cong tac PHAI -> tu danh dau + dung)
    A = quay TRAI (cham cong tac TRAI -> tu danh dau + dung)
    SPACE = DUNG
    Z = set vi tri hien tai = 0 (tam)
    1 = danh dau BIEN TRAI tay   2 = danh dau BIEN PHAI tay
    S = LUU file pan_range.txt
    ESC = thoat

QUY TRINH DE NHAT (dung cong tac):
    1. Bam D -> motor quay phai den khi CHAM cong tac -> tu danh dau PHAI + dung
    2. Bam A -> motor quay trai den khi CHAM cong tac -> tu danh dau TRAI + dung
    3. Bam S -> luu. Xong!
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
JOG_SPS = 250   # toc do lai tay (CHAM de an toan + de canh cong tac)


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
                    print(f"[INFO] Camera OK: index={idx}")
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    return cap
            cap.release()
    return None


# ===== Trang thai limit tu Arduino =====
lim = {"tilt_neg": False, "tilt_pos": False, "pan_neg": False, "pan_pos": False}
_buf = ""

def poll_limits(ser):
    global _buf
    try:
        n = ser.in_waiting
    except Exception:
        return
    if not n:
        return
    _buf += ser.read(n).decode(errors="ignore")
    while "\n" in _buf:
        line, _buf = _buf.split("\n", 1)
        line = line.strip()
        if line.startswith("LIM:"):
            try:
                a0, a1, a2, a3 = (int(x) for x in line[4:].split(",")[:4])
                lim["tilt_neg"] = bool(a0)
                lim["tilt_pos"] = bool(a1)
                lim["pan_neg"] = bool(a2)
                lim["pan_pos"] = bool(a3)
            except Exception:
                pass


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
    ser.write(b"M\n")   # bat machine-report de doc cong tac
    ser.flush()
    time.sleep(0.1)
    ser.write(b"S")     # SCAN mode: Arduino KHONG tu chan, de minh lai cham cong tac
    ser.flush()

    def send(s):
        ser.write(s.encode())
        ser.flush()

    cap = open_camera()
    if cap is None:
        print("[!] Khong mo duoc camera (van do duoc, chi la khong co hinh).")

    pan_pos = 0.0
    last_sps = 0
    mark_left = None
    mark_right = None
    prev_t = time.time()

    print("[INFO] San sang. Bam phim trong cua so.")

    try:
        while True:
            now = time.time()
            dt = now - prev_t
            prev_t = now
            pan_pos += last_sps * dt

            poll_limits(ser)

            # ===== TU DANH DAU khi cham cong tac that =====
            # quay phai (last_sps>0) cham cong tac chan-quay-phai (pan_pos = A3 slot)
            if last_sps > 0 and lim["pan_pos"]:
                mark_right = pan_pos
                last_sps = 0
                send("P0\n")
                print(f"[CAL] CHAM cong tac PHAI -> bien PHAI = {int(pan_pos)} (da dung)")
            elif last_sps < 0 and lim["pan_neg"]:
                mark_left = pan_pos
                last_sps = 0
                send("P0\n")
                print(f"[CAL] CHAM cong tac TRAI -> bien TRAI = {int(pan_pos)} (da dung)")

            # ===== Lay frame camera =====
            frame = None
            if cap is not None:
                ok, fr = cap.read()
                if ok and fr is not None:
                    frame = fr
            if frame is None:
                frame = np.zeros((480, 640, 3), dtype=np.uint8)

            # ===== Overlay thong tin =====
            def put(t, y, c=(0, 255, 255), s=0.6):
                cv2.putText(frame, t, (12, y), cv2.FONT_HERSHEY_SIMPLEX, s, c, 2)

            put("CALIBRATE PAN", 30, (0, 255, 0))
            put(f"VI TRI: {int(pan_pos)} step", 60, (255, 255, 0), 0.8)
            dir_txt = "PHAI->" if last_sps > 0 else ("<-TRAI" if last_sps < 0 else "DUNG")
            put(f"{dir_txt}", 90)
            put(f"bien TRAI(1): {int(mark_left) if mark_left is not None else '--'}", 120)
            put(f"bien PHAI(2): {int(mark_right) if mark_right is not None else '--'}", 145)
            # trang thai cong tac
            lp = "PHAI:NHAN" if lim["pan_pos"] else "phai:nha"
            ln = "TRAI:NHAN" if lim["pan_neg"] else "trai:nha"
            put(f"congtac {ln} {lp}", 170,
                (0, 0, 255) if (lim["pan_pos"] or lim["pan_neg"]) else (180, 180, 180), 0.5)
            put("D=phai A=trai SPACE=dung Z=set0", 450, (200, 200, 200), 0.5)
            put("1/2=mark tay  S=luu  ESC=thoat", 470, (200, 200, 200), 0.5)

            cv2.imshow("Calibrate PAN", frame)
            key = cv2.waitKey(20) & 0xFF

            if key == 27:
                break
            elif key == ord('d'):
                last_sps = JOG_SPS
                send(f"P{JOG_SPS}\n")
            elif key == ord('a'):
                last_sps = -JOG_SPS
                send(f"P{-JOG_SPS}\n")
            elif key == ord(' '):
                last_sps = 0
                send("P0\n")
            elif key == ord('z'):
                pan_pos = 0.0
                print("[CAL] set vi tri = 0")
            elif key == ord('1'):
                mark_left = pan_pos
                print(f"[CAL] mark TRAI = {int(pan_pos)}")
            elif key == ord('2'):
                mark_right = pan_pos
                print(f"[CAL] mark PHAI = {int(pan_pos)}")
            elif key == ord('s'):
                if mark_left is None or mark_right is None:
                    print("[!] Chua du 2 bien. Lai cham 2 cong tac (D va A) hoac bam 1/2.")
                else:
                    lo = int(min(mark_left, mark_right))
                    hi = int(max(mark_left, mark_right))
                    with open(PAN_RANGE_FILE, "w") as f:
                        f.write(f"{lo},{hi}")
                    print(f"[CAL] DA LUU pan_range.txt: min={lo}, max={hi}  (rong {hi-lo} step)")

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
