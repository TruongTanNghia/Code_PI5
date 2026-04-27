"""
CHAN DOAN MOTOR - Kiem tra tung tang ket noi:
  Pi GPIO -> PC817 -> Driver MD5-HD14 -> Motor

Chay TUNG BUOC, in to ro, dung cho chua thay motor quay.

Cach dung:
    python motor_diagnostic.py        # mac dinh motor 1
    python motor_diagnostic.py 2      # motor 2
"""
import sys
import time
from gpiozero import OutputDevice
from gpiozero.pins.lgpio import LGPIOFactory
from gpiozero import Device
Device.pin_factory = LGPIOFactory()

from config import (
    PIN_M1_CW, PIN_M1_CCW,
    PIN_M2_CW, PIN_M2_CCW,
    STEPPER_STEP_DEG,
)

motor_arg = sys.argv[1] if len(sys.argv) > 1 else "1"
if motor_arg == "1":
    PIN_CW, PIN_CCW = PIN_M1_CW, PIN_M1_CCW
    name = "MOTOR 1 (PAN)"
elif motor_arg == "2":
    PIN_CW, PIN_CCW = PIN_M2_CW, PIN_M2_CCW
    name = "MOTOR 2 (TILT)"
else:
    print("Usage: python motor_diagnostic.py [1|2]")
    sys.exit(1)

cw  = OutputDevice(PIN_CW,  initial_value=False)
ccw = OutputDevice(PIN_CCW, initial_value=False)


def banner(title, n, total):
    print()
    print("#" * 62)
    print(f"#  TEST {n}/{total}: {title}")
    print("#" * 62)


def wait_user(prompt="Nhan ENTER de tiep tuc..."):
    try:
        input(f"\n>>> {prompt}")
    except (KeyboardInterrupt, EOFError):
        cleanup_and_exit()


def cleanup_and_exit():
    cw.off(); ccw.off()
    print("\n[!] Thoat. GPIO da tat.")
    sys.exit(0)


# ============================================================
print()
print("=" * 62)
print(f"  CHAN DOAN: {name}")
print("=" * 62)
print(f"  CW pin  = GPIO{PIN_CW}")
print(f"  CCW pin = GPIO{PIN_CCW}")
print()
print("CHUAN BI TRUOC KHI BAT DAU:")
print("  [ ] 1. Dan bang keo / sticker len TRUC MOTOR (de thay xoay)")
print("  [ ] 2. Cap nguon 24V cho driver MD5-HD14")
print("         -> POWER LED (do) cua driver PHAI sang")
print("  [ ] 3. Dat module PC817 trong tam mat de nhin LED")
print("  [ ] 4. So nhe truc motor: phai THAY CUNG (co holding torque)")
print("         vi driver dang giu motor")
print()
wait_user("Da chuan bi xong, nhan ENTER de bat dau...")

try:
    # ============================================================
    banner("KEO GPIO CW LEN HIGH 5 GIAY (kiem tra LED chain)", 1, 4)
    print()
    print("Trong 5 giay toi:")
    print(f"  - GPIO{PIN_CW} se LUON HIGH (3.3V)")
    print("  - LED IN1 cua PC817 PHAI sang")
    print("  - LED OUT/U1 cua PC817 PHAI sang (dao do PC817)")
    print("  - Driver MD5-HD14: chua step, chi giu motor")
    print()
    wait_user("Nhan ENTER de bat dau 5 giay...")
    cw.on()
    for i in range(5, 0, -1):
        print(f"  >>> CW HIGH...   {i} giay con lai", end="\r", flush=True)
        time.sleep(1)
    cw.off()
    print(f"  >>> CW da TAT.                              ")
    print()
    print("CAU HOI:")
    print("  [a] LED PC817 IN1 co SANG trong 5 giay khong?")
    print("  [b] LED PC817 OUT (U1) co SANG trong 5 giay khong?")
    wait_user("Tra loi xong, ENTER de tiep tuc test 2...")

    # ============================================================
    banner("PHAT 1 XUNG CW DUY NHAT (kiem tra driver nhan xung)", 2, 4)
    print()
    print("Sap phat 1 xung 1ms len GPIO CW.")
    print("  - LED RUN cua driver MD5-HD14 PHAI nhay 1 cai (rat nhanh)")
    print("  - Truc motor PHAI dich 0.72 deg (kho nhin, ~1mm tren mep truc)")
    print()
    wait_user("Nhan ENTER de phat 1 xung...")
    cw.on()
    time.sleep(0.001)
    cw.off()
    print()
    print(">>> DA PHAT 1 XUNG.")
    print()
    print("CAU HOI: LED RUN co nhay khong?")
    wait_user("Tra loi xong, ENTER de tiep tuc test 3...")

    # ============================================================
    banner("30 XUNG CHAM (1 step/giay - DE NHIN BANG KEO)", 3, 4)
    print()
    print("Sap step 30 lan, MOI LAN 1 GIAY.")
    print(f"  - Tong xoay: 30 x 0.72 = {30 * STEPPER_STEP_DEG:.1f} deg (~1/16 vong)")
    print("  - Bang keo tren truc PHAI nhich tung chut moi giay")
    print("  - LED RUN nhay 1 cai moi step")
    print()
    wait_user("Nhan ENTER de bat dau (30 giay)...")
    for i in range(1, 31):
        cw.on()
        time.sleep(0.001)
        cw.off()
        print(f"   <<< STEP {i:2d}/30  (tong = {i * STEPPER_STEP_DEG:5.1f} deg) >>>")
        time.sleep(0.999)
    print()
    print(">>> DA XONG 30 STEP.")
    print()
    print("CAU HOI: BANG KEO co XOAY tung nhip moi giay khong?")
    wait_user("Tra loi xong, ENTER de tiep tuc test 4...")

    # ============================================================
    banner("100 XUNG CCW (toc do 50 step/s - dao chieu)", 4, 4)
    print()
    print("Sap step 100 lan theo CCW (chieu nguoc lai), 50 step/s.")
    print(f"  - Tong: 100 x 0.72 = {100 * STEPPER_STEP_DEG:.1f} deg trong 2 giay")
    print("  - Bang keo PHAI xoay nguoc chieu test 3")
    print()
    wait_user("Nhan ENTER de bat dau (2 giay)...")
    for i in range(100):
        ccw.on()
        time.sleep(0.01)
        ccw.off()
        time.sleep(0.01)
    print()
    print(">>> DA XONG 100 STEP CCW.")
    print()

    # ============================================================
    print()
    print("=" * 62)
    print("  TONG KET CHAN DOAN")
    print("=" * 62)
    print()
    print("DUA TREN QUAN SAT CUA ANH:")
    print()
    print("[A] LED PC817 SANG (test 1) + Truc motor QUAY (test 3 + 4)")
    print("    => MOTOR HOAN TOAN OK. Quay lai chay test_stepper.py.")
    print()
    print("[B] LED PC817 KHONG SANG (test 1)")
    print("    => Pi -> PC817 sai. Kiem tra:")
    print(f"         * Day Pi GPIO{PIN_CW} -> IN1 cua PC817 noi chua?")
    print("         * GND chung Pi <-> G (ben trai PC817) noi chua?")
    print("         * Module PC817 co nguon Vcc 3.3V/5V chua?")
    print()
    print("[C] LED PC817 SANG nhung LED RUN driver KHONG nhay (test 2)")
    print("    => PC817 -> Driver sai. Kiem tra:")
    print("         * Day OUT (U1) cua PC817 -> CW- driver noi chua?")
    print("         * Chan CW+ driver da noi +24V chua?")
    print()
    print("[D] LED RUN nhay nhung Truc motor KHONG quay")
    print("    => Driver -> Motor sai. Kiem tra:")
    print("         * 5 day BLUE/RED/ORANGE/GREEN/BLACK noi dung mau driver chua?")
    print("         * Driver co cap du 24V khong (POWER LED do sang manh)?")
    print("         * Vat dong NUM dong tren driver tang dong (vd 1.4A)")
    print("         * DIP switch driver dat dung mode (TEST OFF, 1/2 CLK OFF)")

except KeyboardInterrupt:
    print("\n[!] DUNG (Ctrl+C).")
finally:
    cw.off()
    ccw.off()
    print("\nGPIO cleanup done.")
