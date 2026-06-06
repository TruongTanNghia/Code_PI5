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

Y nghia LIM:a0,a1,a2,a3
  a0 = cong tac TREN (tilt len)
  a1 = cong tac DUOI (tilt xuong)
  a2 = cong tac (pan) - ngat-tr
  a3 = cong tac (pan) - ngat-ph
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

    buf = ""
    last_m = time.time()
    last_lim = None
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
                        if line != last_lim:        # chi in khi DOI -> de thay ro
                            print(f"  >>> {line}   <-- CONG TAC DOI TRANG THAI")
                            last_lim = line
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
