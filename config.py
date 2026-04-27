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

# ===== LASER =====
LASER_PIN = 17              # GPIO BCM (chan vat ly 11) - dung GPIO Pi5
LOCK_THRESHOLD = 25         # khoang cach px tu tam camera de coi la "khoa muc tieu"
LOCK_FRAMES_REQUIRED = 3    # so frame lien tuc trong vung khoa truoc khi ban
LASER_BURST_TIME = 0.4      # thoi gian ban moi lan (giay)
LASER_COOLDOWN = 1.0        # thoi gian nghi giua 2 phat ban (giay) - an toan
