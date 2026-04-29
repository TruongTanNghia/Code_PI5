"""
Mo serial port den Arduino MA KHONG kich hoat DTR -> Arduino KHONG reset.

DTR auto-reset la 1 trong nhung nguyen nhan kha nang gay motor twitch:
- Pi5 mo port -> DTR toggle -> Arduino reset -> setup() lai -> loop() lai
- Neu Pi5 sau do gui '1' qua nhanh -> Arduino chua kip xu ly hoac dang giua
  bootloader -> nhan duoc nhung xu ly khong dung -> twitch.

Voi script nay, Pi5 mo port nhung GIU DTR LOW (de-asserted) -> Arduino chay
binh thuong, khong reset.

Cach dung:
    python motor_no_dtr.py 1     # gui '1', motor 1 quay 5000 step (~15s)
    python motor_no_dtr.py 2
    python motor_no_dtr.py 3
    python motor_no_dtr.py 4

KHONG ho tro stop mid-spin va limit switch trong script nay - chi de kiem tra
xem motor co quay duoc hay khong sau khi loai bo DTR reset.
"""
import sys
import time
import os
import glob

try:
    import serial
except ImportError:
    print("[!] Chua cai pyserial. Chay: pip install pyserial")
    sys.exit(1)


def find_usb_port():
    candidates = sorted(glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*'))
    return candidates[0] if candidates else None


if len(sys.argv) < 2 or sys.argv[1] not in ('1', '2', '3', '4'):
    print("Usage: python motor_no_dtr.py [1|2|3|4]")
    sys.exit(1)

cmd = sys.argv[1]
port = find_usb_port()
if not port:
    print("[!] Khong tim thay /dev/ttyUSB* hoac /dev/ttyACM*")
    sys.exit(1)

print(f"=== MOTOR NO-DTR TEST ===")
print(f"Port: {port}")
print(f"Command: {cmd}")
print()

# QUAN TRONG: cau hinh DTR=False / RTS=False TRUOC khi open port
# de tranh Arduino auto-reset
ser = serial.Serial()
ser.port = port
ser.baudrate = 9600
ser.timeout = 0.5
ser.dtr = False    # tat DTR
ser.rts = False    # tat RTS

print("[INFO] Mo port voi DTR=False, RTS=False (Arduino KHONG reset)...")
ser.open()

# Bao dam chac chan
ser.dtr = False
ser.rts = False

print("[INFO] Cho 1s cho on dinh...")
time.sleep(1.0)

# Drain bat ky byte gi co san
while ser.in_waiting:
    ser.read(ser.in_waiting)

print(f"[INFO] Gui lenh '{cmd}' -> Arduino quay 5000 step (~15s)...")
ser.write(cmd.encode())

# Cho motor quay xong (~15-20 giay)
print("[INFO] Doi motor quay xong (Ctrl+C de huy som)...")
try:
    for i in range(20):
        time.sleep(1)
        # Doc bat cu phan hoi nao tu Arduino
        if ser.in_waiting:
            data = ser.read(ser.in_waiting)
            print(f"   [ARDUINO] {data}")
        print(f"   ... {i+1}s elapsed", end="\r", flush=True)
except KeyboardInterrupt:
    print("\n[INFO] Ctrl+C - thoat.")

print()
ser.close()
print("[INFO] Done.")
