"""
Chan doan: liet ke tat ca COM port + thu mo camera.
Chay tren Windows hoac Linux.

Usage:
    py diagnose.py
"""
import sys
import platform

print("=" * 60)
print(f" CHAN DOAN HE THONG")
print("=" * 60)
print(f"  OS: {platform.system()} {platform.release()}")
print(f"  Python: {sys.version.split()[0]}")
print()

# ===== 1. LIET KE COM PORTS =====
print("--- 1. COM PORTS (Arduino?) ---")
try:
    import serial.tools.list_ports
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("  [!] KHONG THAY COM PORT NAO.")
    else:
        for p in ports:
            print(f"  {p.device}")
            print(f"      description: {p.description}")
            print(f"      hwid:        {p.hwid}")
            print(f"      vid:pid:     {p.vid}:{p.pid}" if p.vid else "      vid:pid:     (none)")
            print(f"      manufacturer: {p.manufacturer}")
            # Phan loai
            desc_low = (p.description or "").lower()
            if any(k in desc_low for k in ("arduino", "ch340", "ch9102", "cp210",
                                           "ftdi", "silicon labs", "usb-serial",
                                           "usb serial")):
                print(f"      >>> CO VE LA ARDUINO / USB-SERIAL <<<")
            elif "communications port" in desc_low or p.device.upper() == "COM1":
                print(f"      (cong noi bo Windows, KHONG phai Arduino)")
            print()
except ImportError:
    print("  [!] pyserial chua cai. Chay: pip install pyserial")
except Exception as e:
    print(f"  [!] Loi: {e}")

# ===== 2. THU MO CAMERA =====
print("\n--- 2. CAMERAS ---")
try:
    import cv2
    print(f"  OpenCV version: {cv2.__version__}")
    print()

    if platform.system() == "Windows":
        BACKENDS = [
            ("DSHOW", cv2.CAP_DSHOW),
            ("MSMF",  cv2.CAP_MSMF),
            ("ANY",   cv2.CAP_ANY),
        ]
    else:
        BACKENDS = [
            ("V4L2", cv2.CAP_V4L2),
            ("ANY",  cv2.CAP_ANY),
        ]

    print("  Thu mo cac index camera 0-5 voi cac backend:")
    found = []
    for idx in range(0, 6):
        for name, backend in BACKENDS:
            try:
                cap = cv2.VideoCapture(idx, backend)
                if not cap.isOpened():
                    cap.release()
                    continue
                ok, frame = cap.read()
                if ok and frame is not None and frame.size > 0:
                    h, w = frame.shape[:2]
                    print(f"    [OK]   index={idx} backend={name}: frame={w}x{h}")
                    found.append((idx, name, w, h))
                else:
                    print(f"    [open nhung khong doc duoc frame] index={idx} backend={name}")
                cap.release()
                break  # da find duoc index nay, thu index khac
            except Exception as e:
                pass

    if not found:
        print()
        print("  [!] KHONG TIM THAY CAMERA NAO.")
        print("      Anh check:")
        print("      - Webcam co cam vao PC chua?")
        print("      - Mo Windows 'Camera' app -> camera co hien khong?")
        print("      - Settings > Privacy > Camera > bat 'Allow apps to access camera'")
        print("      - Tat Zoom/Teams/OBS/Discord neu dang chay")
        print("      - Device Manager > Cameras: co thay khong?")
    else:
        print()
        print(f"  [INFO] Tim thay {len(found)} camera(s).")
        print(f"  Goi y: sua CAM_INDEX trong main.py thanh {found[0][0]} neu can.")

except ImportError:
    print("  [!] opencv-python chua cai. Chay: pip install opencv-python")
except Exception as e:
    print(f"  [!] Loi: {e}")

# ===== 3. PYTORCH / ULTRALYTICS =====
print("\n--- 3. AI LIBRARIES ---")
try:
    import torch
    print(f"  torch: {torch.__version__}")
    print(f"  CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
except ImportError:
    print("  [!] torch chua cai. Chay: pip install torch")
except Exception as e:
    print(f"  [!] Loi torch: {e}")

try:
    import ultralytics
    print(f"  ultralytics: {ultralytics.__version__}")
except ImportError:
    print("  [!] ultralytics chua cai. Chay: pip install ultralytics")
except Exception as e:
    print(f"  [!] Loi ultralytics: {e}")

# ===== 4. MODEL FILE =====
print("\n--- 4. MODEL FILE ---")
import os
for f in ("best_seg.pt", "best.pt", "results-mouse/best.pt"):
    if os.path.exists(f):
        size_mb = os.path.getsize(f) / 1e6
        print(f"  [OK]   {f}  ({size_mb:.1f} MB)")
    else:
        print(f"  [!]   {f}  KHONG TIM THAY")

print()
print("=" * 60)
print(" CHAN DOAN XONG")
print("=" * 60)
