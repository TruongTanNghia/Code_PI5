import cv2
import time
import serial
import numpy as np

from detector import MouseDetector
from config import DET_PERSIST_FRAMES, DET_CONF

# ================= SERIAL ARDUINO =================
# Windows: "COM3", "COM4"... (xem trong Device Manager > Ports)
# Linux/Pi: "/dev/ttyUSB0", "/dev/ttyACM0"...
import sys as _sys
if _sys.platform.startswith("win"):
    PORT = "COM3"          # <<< DOI sang COM that cua Arduino tren Windows
else:
    PORT = "/dev/ttyUSB0"  # tren Raspberry Pi
BAUD = 9600

ser = serial.Serial(PORT, BAUD, timeout=0.1)
ser.setDTR(False)
time.sleep(2)
ser.write(b"M")   # bat che do Arduino bao trang thai limit (LIM:...) cho Python
ser.flush()

# ================= WEBCAM (OBSBOT Meet SE - UVC) =================
# Cam UVC thuong -> dung OpenCV. Tu chon backend theo HE DIEU HANH:
#   Windows -> CAP_DSHOW (hoac CAP_MSMF)
#   Linux/Pi -> CAP_V4L2
import sys
CAM_INDEX = 0   # neu khong mo duoc, thu 1, 2...
FRAME_W = 640
FRAME_H = 480

if sys.platform.startswith("win"):
    cam_backend = cv2.CAP_DSHOW      # Windows
else:
    cam_backend = cv2.CAP_V4L2       # Linux / Raspberry Pi

cap = cv2.VideoCapture(CAM_INDEX, cam_backend)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_W)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_H)
cap.set(cv2.CAP_PROP_FPS, 30)
# Giảm buffer để frame không bị trễ (lag) - quan trọng cho tracking
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

if not cap.isOpened():
    raise RuntimeError(
        f"Khong mo duoc webcam o index {CAM_INDEX}. "
        f"Thu doi CAM_INDEX sang 1, 2..."
    )

# ================= YOLO =================
detector = MouseDetector()

# ================= TRACKING CONFIG =================
# Vùng "đứng yên" - vào trong vùng này thì motor dừng hẳn + laser bật.
# Nhỏ hơn = laser ngắm chính xác hơn vào giữa con chuột, nhưng motor khó vào tâm.
DEADZONE_X = 35
DEADZONE_Y = 40

# ===== LASER OFFSET (CALIBRATE) =====
# Laser gắn LỆCH so với camera -> điểm laser chiếu trên frame KHÔNG phải tâm frame.
# Hai số này là vị trí laser thực sự, tính từ tâm frame.
# Khi chương trình chạy, dùng phím I/J/K/L để dịch aim point cho đến khi
# crosshair vàng trùng với chấm laser đỏ thật, rồi copy giá trị in trên console
# vào đây cho lần chạy sau.
LASER_OFFSET_X = 0
LASER_OFFSET_Y = 0

# Bước dịch khi nhấn phím calibrate
CAL_STEP = 2

# ===== TOC DO STEPPER (step/s) =====
# Khi vat o ngay mep deadzone -> chay cham (MIN_SPS).
# Khi vat o xa (>= MAX_ERROR) -> chay nhanh (MAX_SPS).
# O giua -> noi suy tuyen tinh -> bam muot, gan tam tu cham lai (khong overshoot).
MAX_ERROR_X = 300     # pixel: xa hon nay thi pan chay het toc
MAX_ERROR_Y = 240     # pixel: xa hon nay thi tilt chay het toc

PAN_MAX_SPS  = 3500   # step/s toi da cho pan (bam nhanh)
PAN_MIN_SPS  = 250    # step/s toi thieu khi sat deadzone (bo cham vao tam)
TILT_MAX_SPS = 3000   # tilt cho cham hon chut vi truoc bi qua da
TILT_MIN_SPS = 200

# Chi gui lenh toc do moi khi thay doi du lon -> do spam serial.
SPS_SEND_STEP = 80     # step/s: chenh nho hon nay thi khong gui lai
SEND_THROTTLE = 0.02   # giay: toi thieu giua 2 lan gui cua 1 truc


class StepperAxis:
    """
    Dieu khien 1 truc stepper bang TOC DO (step/s).
    Tinh toc do ti le voi sai so -> chay muot, tu cham lai khi gan tam.
    Gui lenh "P<sps>\n" (pan) hoac "T<sps>\n" (tilt) toi Arduino.
    """

    def __init__(self, axis_letter, deadzone, max_error,
                 max_sps, min_sps):
        self.axis = axis_letter        # 'P' cho pan, 'T' cho tilt
        self.deadzone = deadzone
        self.max_error = max_error
        self.max_sps = max_sps
        self.min_sps = min_sps

        self.last_sps_sent = None
        self.last_send_t = 0.0
        self.current_sps = 0           # de debug

    def _sps_from_error(self, error):
        """Tra ve toc do co dau (am/duong) theo huong va do lon sai so."""
        abs_err = abs(error)
        if abs_err <= self.deadzone:
            return 0
        if abs_err >= self.max_error:
            mag = self.max_sps
        else:
            ratio = (abs_err - self.deadzone) / (self.max_error - self.deadzone)
            mag = self.min_sps + (self.max_sps - self.min_sps) * ratio
        sps = int(mag)
        return sps if error > 0 else -sps

    def update(self, error, send_raw, force_stop=False,
               block_pos=False, block_neg=False):
        now = time.time()
        sps = 0 if force_stop else self._sps_from_error(error)

        # ===== CHAN KEP: neu da cham limit huong dang muon di -> ep dung huong do =====
        # block_pos: da cham limit phia duong (P/T > 0)
        # block_neg: da cham limit phia am   (P/T < 0)
        if sps > 0 and block_pos:
            sps = 0
        elif sps < 0 and block_neg:
            sps = 0

        self.current_sps = sps

        # Chi gui khi thay doi dang ke (hoac khi can dung han / khoi dong lai).
        changed_enough = (
            self.last_sps_sent is None
            or (sps == 0 and self.last_sps_sent != 0)        # vua moi dung
            or (sps != 0 and self.last_sps_sent == 0)        # vua moi chay
            or abs(sps - self.last_sps_sent) >= SPS_SEND_STEP
        )
        if changed_enough and (now - self.last_send_t) >= SEND_THROTTLE:
            send_raw(f"{self.axis}{sps}\n")
            self.last_sps_sent = sps
            self.last_send_t = now


def send_raw(s):
    """Gửi chuỗi thẳng tới Arduino (dùng cho lệnh tốc độ P/T)."""
    ser.write(s.encode())
    ser.flush()


def send(cmd):
    print("[SEND]", cmd)
    ser.write(cmd.encode())
    ser.flush()


# ================= LIMIT SWITCH STATE (doc tu Arduino) =================
# Thu tu Arduino gui "LIM:up,down,left,right" = A0,A1,A2,A3
#   A0 = len   (tilt am)   -> lim_tilt_neg
#   A1 = xuong (tilt duong)-> lim_tilt_pos
#   A2 = trai  (pan am)    -> lim_pan_neg
#   A3 = phai  (pan duong) -> lim_pan_pos
lim_tilt_neg = False
lim_tilt_pos = False
lim_pan_neg = False
lim_pan_pos = False
_serial_buf = ""

def poll_limits():
    """Doc cac dong Arduino gui, cap nhat trang thai limit. Khong block."""
    global _serial_buf, lim_tilt_neg, lim_tilt_pos, lim_pan_neg, lim_pan_pos
    try:
        n = ser.in_waiting
    except Exception:
        return
    if n:
        _serial_buf += ser.read(n).decode(errors="ignore")
        # xu ly tung dong hoan chinh
        while "\n" in _serial_buf:
            line, _serial_buf = _serial_buf.split("\n", 1)
            line = line.strip()
            if line.startswith("LIM:"):
                try:
                    parts = line[4:].split(",")
                    a0, a1, a2, a3 = (int(p) for p in parts[:4])
                    lim_tilt_neg = bool(a0)
                    lim_tilt_pos = bool(a1)
                    lim_pan_neg = bool(a2)
                    lim_pan_pos = bool(a3)
                except Exception:
                    pass


# ================= LASER =================
laser_on = False

def set_laser(on):
    """Chỉ gửi serial khi trạng thái laser thật sự đổi."""
    global laser_on
    if on and not laser_on:
        send("L")
        laser_on = True
    elif (not on) and laser_on:
        send("K")
        laser_on = False


# Trục ngang (pan): dx > 0 -> đối tượng ở bên phải -> camera quay phải (P dương)
axis_x = StepperAxis(
    axis_letter="P", deadzone=DEADZONE_X, max_error=MAX_ERROR_X,
    max_sps=PAN_MAX_SPS, min_sps=PAN_MIN_SPS
)
# Trục dọc (tilt): dy > 0 -> đối tượng ở phía dưới -> camera cúi xuống (T dương)
axis_y = StepperAxis(
    axis_letter="T", deadzone=DEADZONE_Y, max_error=MAX_ERROR_Y,
    max_sps=TILT_MAX_SPS, min_sps=TILT_MIN_SPS
)

last_dets = []
miss_count = 0
prev_t = time.time()
fps = 0.0

# Offset runtime, init từ config, có thể chỉnh bằng I/J/K/L
laser_offset_x = LASER_OFFSET_X
laser_offset_y = LASER_OFFSET_Y


try:
    print("[INFO] Webcam + YOLO tracking ready. ESC de thoat.")

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            print("[WARN] Khong doc duoc frame, thu lai...")
            continue
        h, w = frame.shape[:2]
        frame_cx = w // 2
        frame_cy = h // 2

        # Điểm "đích ngắm" thực tế = vị trí laser chiếu trên frame
        aim_x = frame_cx + laser_offset_x
        aim_y = frame_cy + laser_offset_y

        detections = detector.detect(frame)

        if detections:
            last_dets = detections
            miss_count = 0
            display_dets = detections
            fresh = True
        else:
            miss_count += 1
            if miss_count <= DET_PERSIST_FRAMES:
                display_dets = last_dets
                fresh = False
            else:
                display_dets = []
                fresh = False

        target_found = False
        dx = 0
        dy = 0
        center_in_deadzone = False

        if display_dets:
            det = max(display_dets, key=lambda d: d.get("conf", 0))
            x1, y1, x2, y2 = det["box"]
            obj_cx, obj_cy = det["center"]
            conf = det["conf"]

            target_found = True

            # ===== ERROR THEO TÂM BOX vs AIM POINT (laser thực tế) =====
            # Laser gắn lệch -> phải kéo tâm con chuột về điểm laser chiếu,
            # KHÔNG phải về tâm frame.
            dx = obj_cx - aim_x
            dy = obj_cy - aim_y

            center_in_deadzone = (abs(dx) <= DEADZONE_X and abs(dy) <= DEADZONE_Y)

            color = (0, 255, 0) if fresh else (0, 200, 200)

            # Vẽ mask seg (tô màu vùng con chuột) nếu có
            seg_mask = det.get("mask")
            if seg_mask is not None:
                overlay = frame.copy()
                overlay[seg_mask] = color
                cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.circle(frame, (obj_cx, obj_cy), 5, (0, 0, 255), -1)
            cv2.line(frame, (aim_x, aim_y),
                     (obj_cx, obj_cy), (255, 255, 0), 2)
            cv2.putText(
                frame,
                f"mouse {conf:.2f} dx={dx} dy={dy}",
                (x1, max(20, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2
            )

        # ===== Doc trang thai limit tu Arduino (chac kep) =====
        poll_limits()

        # ===== Điều khiển motor theo tốc độ, có chặn theo limit =====
        # PAN (P): duong = phai (pan_pos), am = trai (pan_neg)
        # TILT (T): duong = xuong (tilt_pos), am = len (tilt_neg)
        axis_x.update(dx, send_raw, force_stop=not target_found,
                      block_pos=lim_pan_pos, block_neg=lim_pan_neg)
        axis_y.update(dy, send_raw, force_stop=not target_found,
                      block_pos=lim_tilt_pos, block_neg=lim_tilt_neg)

        # ===== Laser: bật khi tâm con chuột đã vào deadzone =====
        in_target = target_found and center_in_deadzone
        set_laser(in_target)

        # ===== Vẽ vùng deadzone quanh AIM POINT (xanh = trúng, trắng = chưa) =====
        dz_color = (0, 255, 0) if (target_found and center_in_deadzone) else (255, 255, 255)
        cv2.rectangle(
            frame,
            (aim_x - DEADZONE_X, aim_y - DEADZONE_Y),
            (aim_x + DEADZONE_X, aim_y + DEADZONE_Y),
            dz_color, 1
        )

        # Crosshair vàng đánh dấu AIM POINT (vị trí laser thực tế)
        # Khi calibrate đúng, crosshair này phải trùng với chấm laser thật trên frame.
        cv2.drawMarker(frame, (aim_x, aim_y), (0, 255, 255),
                       markerType=cv2.MARKER_CROSS, markerSize=20, thickness=2)
        # Chấm xanh dương = tâm frame thật (tham chiếu)
        cv2.circle(frame, (frame_cx, frame_cy), 3, (255, 0, 0), -1)

        # ===== FPS =====
        now = time.time()
        dt = now - prev_t
        if dt > 0:
            fps = 0.9 * fps + 0.1 * (1.0 / dt)
        prev_t = now

        info = f"FPS: {fps:.1f} conf>={DET_CONF} det:{len(display_dets)}"
        cv2.putText(frame, info, (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        # Debug motor: toc do step/s dang gui
        dbg = (f"PAN sps={axis_x.current_sps}  "
               f"TILT sps={axis_y.current_sps}")
        cv2.putText(frame, dbg, (10, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        # Debug limit: hien cong tac nao dang cham (mau do)
        lim_txt = "LIM:"
        lim_txt += " LEN" if lim_tilt_neg else ""
        lim_txt += " XUONG" if lim_tilt_pos else ""
        lim_txt += " TRAI" if lim_pan_neg else ""
        lim_txt += " PHAI" if lim_pan_pos else ""
        if lim_txt != "LIM:":
            cv2.putText(frame, lim_txt, (10, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        # Hiển thị offset hiện tại để calibrate
        cv2.putText(frame,
                    f"OFFSET x={laser_offset_x} y={laser_offset_y}  [I/J/K/L=move, R=reset]",
                    (10, h - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        # Chỉ báo trạng thái laser
        if laser_on:
            cv2.putText(frame, "LASER ON", (10, 55),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.circle(frame, (w - 30, 30), 12, (0, 0, 255), -1)

        cv2.imshow("Mouse Auto Tracking", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:    # ESC
            break
        elif key == ord('i'):
            laser_offset_y -= CAL_STEP
            print(f"[CAL] OFFSET = ({laser_offset_x}, {laser_offset_y})")
        elif key == ord('k'):
            laser_offset_y += CAL_STEP
            print(f"[CAL] OFFSET = ({laser_offset_x}, {laser_offset_y})")
        elif key == ord('j'):
            laser_offset_x -= CAL_STEP
            print(f"[CAL] OFFSET = ({laser_offset_x}, {laser_offset_y})")
        elif key == ord('l'):
            laser_offset_x += CAL_STEP
            print(f"[CAL] OFFSET = ({laser_offset_x}, {laser_offset_y})")
        elif key == ord('r'):
            laser_offset_x = 0
            laser_offset_y = 0
            print(f"[CAL] OFFSET reset = (0, 0)")

finally:
    set_laser(False)
    send("x")
    time.sleep(0.2)
    ser.close()
    cap.release()
    cv2.destroyAllWindows()