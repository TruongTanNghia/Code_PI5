# -*- coding: utf-8 -*-
"""
TEST CONG TAC HANH TRINH - don gian, KHONG can camera/YOLO/motor.

Muc dich: kiem tra Arduino co NHAN duoc cong tac khong (phan cung hay phan mem).

CACH DUNG:
  py test_limit.py
  -> Chuong trinh in MOI dong Arduino gui ve.
  -> Lay tay BAM tung cong tac (tren/duoi/trai/phai).
  -> Neu thay dong "LIM:..." doi so (0->1) khi bam  => CONG TAC + DAY OK.
     Neu BAM ma KHONG co gi nhay                    => HU PHAN CUNG (day long/cong tac).
  -> Ctrl+C de thoat.

4 cong tac (theo thu tu Arduino gui a0,a1,a2,a3):
  TREN  (tilt len)
  DUOI  (tilt xuong)
  TRAI  (pan)
  PHAI  (pan)
Khi bam, chuong trinh in ro vd:
  TREN =nha   DUOI =nha   TRAI =NHAN  PHAI =nha    <<< VUA BAM: TRAI
"""
import sys
import time

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("[!] Chua cai pyserial. Chay: pip install pyserial")
    sys.exit(1)

IS_WINDOWS = sys.platform.startswith("win")


def find_port():
    if IS_WINDOWS:
        ports = [p for p in serial.tools.list_ports.comports()
                 if p.device.upper() != "COM1"]
        for p in ports:
            d = (p.description or "").lower()
            if any(k in d for k in ("arduino", "ch340", "ch9102", "cp210",
                                    "ftdi", "silicon labs", "usb-serial", "usb serial")):
                return p.device
        return ports[0].device if ports else None
    import glob
    c = sorted(glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*"))
    return c[0] if c else None


def main():
    port = find_port()
    if not port:
        print("[!] Khong tim thay Arduino. Cam day + cai driver CH340 chua?")
        sys.exit(1)
    print(f"[INFO] Ket noi: {port} @ 9600")

    ser = serial.Serial(port, 9600, timeout=0.1)
    ser.setDTR(False)          # khong cho Arduino reset
    time.sleep(2)
    ser.reset_input_buffer()
    ser.write(b"M\n")          # bat che do bao cong tac (machine-report)
    ser.flush()
    print("[INFO] Da bat bao cong tac. GIO LAY TAY BAM TUNG CONG TAC...")
    print("[INFO] Thay 'LIM:...' doi so khi bam = OK. Khong co gi = hu day/cong tac.")
    print("[INFO] Ctrl+C de thoat.\n")

    # Ten 4 cong tac theo thu tu a0,a1,a2,a3 Arduino gui
    TEN = ["TREN ", "DUOI ", "TRAI ", "PHAI "]

    buf = ""
    last_m = time.time()
    prev = [None, None, None, None]   # trang thai lan truoc cua 4 cong tac
    try:
        while True:
            n = ser.in_waiting
            if n:
                buf += ser.read(n).decode(errors="ignore")
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("LIM:"):
                        try:
                            vals = [int(x) for x in line[4:].split(",")[:4]]
                        except Exception:
                            continue
                        # Dong trang thai: TREN=nha DUOI=NHAN TRAI=nha PHAI=nha
                        trangthai = "  ".join(
                            f"{TEN[i]}={'NHAN' if vals[i] else 'nha '}"
                            for i in range(4)
                        )
                        # Bao ro cong tac nao VUA DUOC BAM (0 -> 1)
                        moi_bam = [TEN[i].strip() for i in range(4)
                                   if prev[i] == 0 and vals[i] == 1]
                        if moi_bam:
                            print(f"  {trangthai}   <<< VUA BAM: {', '.join(moi_bam)}")
                        elif any(p != v for p, v in zip(prev, vals)):
                            print(f"  {trangthai}")
                        prev = vals
                    else:
                        print(f"  [ARD] {line}")
            # Gui lai M moi 2s (phong Arduino reset)
            if time.time() - last_m >= 2.0:
                ser.write(b"M\n")
                ser.flush()
                last_m = time.time()
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\n[INFO] Thoat.")
    finally:
        ser.close()


if __name__ == "__main__":
    main()
