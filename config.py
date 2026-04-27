CAMERA_ID = 4           # RealSense D435: video4 = RGB. USB webcam thuong: 0. Dat -1 de auto-detect
USE_PICAMERA = False    # True neu dung Pi Camera Module (cap CSI ribbon)
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FPS = 30


PAN_CHANNEL = 0
TILT_CHANNEL = 1

PAN_MIN, PAN_MAX = 30, 150
TILT_MIN, TILT_MAX = 50, 130

KP = 0.025
DEAD_ZONE = 20

# ===== STEPPER (Autonics A16K-M569 + MD5-HD14 qua PC817 4-kenh) =====
# Sap xep theo so do thuc te tren Pi5:
#   Motor 1 = PAN (trai/phai)
PIN_M1_CW         = 17   # GPIO17 -> PC817 IN1 -> driver 1 CW-
PIN_M1_CCW        = 27   # GPIO27 -> PC817 IN2 -> driver 1 CCW-
PIN_M1_LIMIT_MIN  = 5    # GPIO5  <- cong tac MIN (cham khi quay CCW het co)
PIN_M1_LIMIT_MAX  = 6    # GPIO6  <- cong tac MAX (cham khi quay CW het co)

#   Motor 2 = TILT (len/xuong)
PIN_M2_CW         = 22   # GPIO22 -> PC817 IN3 -> driver 2 CW-
PIN_M2_CCW        = 23   # GPIO23 -> PC817 IN4 -> driver 2 CCW-
PIN_M2_LIMIT_MIN  = 13   # GPIO13 <- cong tac MIN
PIN_M2_LIMIT_MAX  = 19   # GPIO19 <- cong tac MAX

# Loai cong tac:
#   True  = NC (Normally Closed) - sai-an-toan, day dut = coi nhu cham
#   False = NO (Normally Open)   - dong khi cham (HW thuc te dang dung)
SWITCH_NC = False

STEPPER_PULSE_HIGH = 0.0005   # 500us cao
STEPPER_PULSE_LOW  = 0.0005   # 500us thap -> 1000 step/s
STEPPER_STEP_DEG   = 0.72     # A16K-M569: 0.72 deg/step (fullstep)

# ===== DETECTOR =====
MODEL_PATH = "./results-mouse/best_ncnn_model"  # NCNN nhanh hon .pt 3-5x tren Pi5
                                                # Neu chua convert, doi sang "./results-mouse/best.pt"
DET_CONF = 0.25         # confidence threshold (thap = it rot detect, cao = it false positive)
DET_IMGSZ = 320         # giam xuong 256 hoac 192 neu can nhanh hon nua
DET_PERSIST_FRAMES = 5  # giu hien thi box them N frame sau khi mat detect (chong nhay)

# ===== LASER =====
LASER_PIN = 18              # GPIO18 -> PC817 rieng -> module laser
LOCK_THRESHOLD = 25         # khoang cach px tu tam camera de coi la "khoa muc tieu"
LOCK_FRAMES_REQUIRED = 3    # so frame lien tuc trong vung khoa truoc khi ban
LASER_BURST_TIME = 0.4      # thoi gian ban moi lan (giay)
LASER_COOLDOWN = 1.0        # thoi gian nghi giua 2 phat ban (giay) - an toan
