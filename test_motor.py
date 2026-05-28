"""
TEST MOTOR STEPPER (gui lenh P/T thang toi Arduino)

Dung CHUNG voi 'arduino_stepper_laser.ino'.
Khong can camera, chi test motor quay + chieu + limit.

CACH DUNG:
1. Nap 'arduino_stepper_laser.ino' vao Arduino.
2. DAM BAO da cap nguon dong luc (24-70V) cho driver HBS57!
3. DONG Serial Monitor neu dang mo.
4. Sua PORT cho dung (COM3... tren Windows).
5. Chay: py test_motor.py
6. Go lenh:
     p 1000   -> pan quay PHAI 1000 step/s
     p -1000  -> pan quay TRAI
     p 0      -> dung pan
     t 800    -> tilt quay XUONG
     t -800   -> tilt quay LEN
     t 0      -> dung tilt
     L        -> bat laser
     K        -> tat laser
     ?        -> in trang thai 4 cong tac
     x        -> dung het + tat laser
     q        -> thoat chuong trinh
"""

import sys
import time
import serial

if sys.platform.startswith("win"):
    PORT = "COM3"
else:
    PORT = "/dev/ttyUSB0"
BAUD = 9600


def main():
    try:
        ser = serial.Serial(PORT, BAUD, timeout=0.2)
    except serial.SerialException as e:
        print(f"[LOI] Khong mo duoc {PORT}: {e}")
        return

    time.sleep(2)
    ser.reset_input_buffer()
    print(f"[OK] Da ket noi {PORT}.")
    print("Lenh: 'p <sps>' pan | 't <sps>' tilt | L/K laser | ? limit | x dung | q thoat")
    print("Vd: p 1000 (pan phai), p -1000 (trai), p 0 (dung)\n")

    try:
        while True:
            # In bat ky gi Arduino gui ve (vd trang thai limit)
            while ser.in_waiting:
                line = ser.readline().decode(errors="ignore").strip()
                if line:
                    print("  [ARDUINO]", line)

            cmd = input(">> ").strip()
            if not cmd:
                continue

            if cmd == "q":
                break
            elif cmd == "x":
                ser.write(b"x"); ser.flush()
                print("  -> dung het")
            elif cmd == "L":
                ser.write(b"L"); ser.flush()
                print("  -> laser ON")
            elif cmd == "K":
                ser.write(b"K"); ser.flush()
                print("  -> laser OFF")
            elif cmd == "?":
                ser.write(b"?"); ser.flush()
                time.sleep(0.1)
            elif cmd.startswith("p"):
                # p <so>
                parts = cmd.split()
                sps = parts[1] if len(parts) > 1 else "0"
                msg = f"P{sps}\n"
                ser.write(msg.encode()); ser.flush()
                print(f"  -> gui {msg.strip()}")
            elif cmd.startswith("t"):
                parts = cmd.split()
                sps = parts[1] if len(parts) > 1 else "0"
                msg = f"T{sps}\n"
                ser.write(msg.encode()); ser.flush()
                print(f"  -> gui {msg.strip()}")
            else:
                print("  Lenh khong hieu. Vd: p 1000 | t -800 | x | q")

    except KeyboardInterrupt:
        pass
    finally:
        ser.write(b"x"); ser.flush()   # dung het khi thoat
        time.sleep(0.2)
        ser.close()
        print("\n[THOAT] Da dung het motor.")


if __name__ == "__main__":
    main()
