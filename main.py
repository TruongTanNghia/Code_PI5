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
# Lon hon chut -> motor de "dung han" o tam, do rung qua lai quanh tam.
DEADZONE_X = 45
DEADZONE_Y = 45

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
# O giua -> noi suy tuyen tinh -> bam muot, gan tam tu cham lai.
#
# ===== CHONG QUAY LO (OVERSHOOT) =====
# MAX_ERROR LON -> motor phai lech RAT xa moi chay het toc -> gan tam rat cham.
# MAX_SPS VUA PHAI -> khong vot qua tam.
# MIN_SPS NHO -> sat tam thi bo tung ti -> dung dung cho.
MAX_ERROR_X = 450     # pixel: keo dai -> pan cham lai som hon khi gan tam
MAX_ERROR_Y = 380     # pixel: tilt tuong tu

PAN_MAX_SPS  = 1800   # ha tu 3500 -> 1800: cham hon, khong vot qua tam
PAN_MIN_SPS  = 120    # sat tam bo rat cham -> vao chinh xac
TILT_MAX_SPS = 1500   # tilt cham hon chut
TILT_MIN_SPS = 100

# Chi gui lenh toc do moi khi thay doi du lon -> do spam serial.
SPS_SEND_STEP = 60     # step/s: chenh nho hon nay thi khong gui lai
SEND_THROTTLE = 0.02   # giay: toi thieu giua 2 lan gui cua 1 truc

# ===== CHE DO QUET (khi khong thay muc tieu) =====
# Quet hinh chu S: pan qua lai trai-phai, moi lan doi chieu thi tilt nhich 1 buoc.
# Khi phat hien chuot lai -> tu dong dung quet, chuyen sang bam.
SCAN_PAN_SPS    = 800     # toc do pan luc quet (cham vua phai de detect kip)
SCAN_TILT_SPS   = 600     # toc do tilt luc nhich len/xuong
SCAN_TILT_STEP_TIME = 0.3 # giay: thoi gian nhich tilt moi khi doi chieu pan
SCAN_START_DELAY = 0.5    # giay: cho bao lau khi mat target moi bat dau quet


class Scanner:
    """
    Quet hinh chu S de tim muc tieu.
    Pan qua lai, moi lan cham limit (hoac lat chieu) thi tilt nhich 1 chut.
    Khi tilt cham limit ca 2 dau -> dao chieu nhich tilt.
    """
    def __init__(self):
        self.active = False
        self.pan_dir = +1       # +1 = phai, -1 = trai
        self.tilt_dir = +1      # +1 = xuong, -1 = len
        self.tilt_nudge_until = 0.0   # tilt chay den thoi diem nay thi dung
        self.lost_since = None        # thoi diem mat target
        self.last_flip_t = 0.0

    def on_target_found(self):
        """Co target lai -> tat quet."""
        self.active = False
        self.lost_since = None

    def on_target_lost(self):
        """Mat target -> chuan bi quet sau SCAN_START_DELAY giay."""
        if self.lost_since is None:
            self.lost_since = time.time()

    def should_scan(self):
        """Co nen quet luc nay khong?"""
        if self.lost_since is None:
            return False
        return (time.time() - self.lost_since) >= SCAN_START_DELAY

    def compute(self, now, lim_pan_neg, lim_pan_pos, lim_tilt_neg, lim_tilt_pos):
        """
        Tinh toc do pan/tilt de quet.
        - Cham limit huong dang quet -> LAT CHIEU (tu quay nguoc lai).
        - Khi lat chieu pan -> kich tilt nhich len/xuong 1 chut.
        - Cham limit tilt dang nhich -> lat chieu tilt.
        """
        self.active = True

        # ===== PAN: cham limit huong dang di -> lat chieu =====
        if (self.pan_dir > 0 and lim_pan_pos) or (self.pan_dir < 0 and lim_pan_neg):
            self.pan_dir = -self.pan_dir
            self.tilt_nudge_until = now + SCAN_TILT_STEP_TIME  # tilt nhich 1 buoc
            self.last_flip_t = now

        # Sau khi lat, huong moi nguoc lai -> KHONG con cham limit -> chay binh thuong
        pan_sps = SCAN_PAN_SPS * self.pan_dir

        # ===== TILT: dang trong cua so nhich? =====
        if now < self.tilt_nudge_until:
            # Cham limit huong tilt dang di -> lat chieu
            if (self.tilt_dir > 0 and lim_tilt_pos) or (self.tilt_dir < 0 and lim_tilt_neg):
                self.tilt_dir = -self.tilt_dir
            tilt_sps = SCAN_TILT_SPS * self.tilt_dir
        else:
            tilt_sps = 0

        return pan_sps, tilt_sps


scanner = Scanner()


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

    def send_sps(self, sps, send_raw,
                 block_pos=False, block_neg=False):
        """Gui toc do thang (dung cho Scanner). Co chan limit."""
        now = time.time()
        sps = int(sps)
        if sps > 0 and block_pos:
            sps = 0
        elif sps < 0 and block_neg:
            sps = 0
        self.current_sps = sps

        changed_enough = (
            self.last_sps_sent is None
            or (sps == 0 and self.last_sps_sent != 0)
            or (sps != 0 and self.last_sps_sent == 0)
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
            # Chon target GAN TAM CAMERA NHAT (uu tien khi co nhieu muc tieu)
            def _dist_to_aim(d):
                cx, cy = d["center"]
                return (cx - aim_x) ** 2 + (cy - aim_y) ** 2
            det = min(display_dets, key=_dist_to_aim)
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

        # ===== Điều khiển motor: BAM hoac QUET =====
        if target_found:
            # Co target -> bam theo. Bao Arduino BAT che do TRACK (chan cung limit).
            if scanner.active or scanner.lost_since is not None:
                send_raw("F")  # F = Follow/track mode -> chan limit
            scanner.on_target_found()
            axis_x.update(dx, send_raw, force_stop=False,
                          block_pos=lim_pan_pos, block_neg=lim_pan_neg)
            axis_y.update(dy, send_raw, force_stop=False,
                          block_pos=lim_tilt_pos, block_neg=lim_tilt_neg)
        else:
            # Mat target -> chuyen sang quet sau SCAN_START_DELAY.
            scanner.on_target_lost()
            if scanner.should_scan():
                # Lan dau vao quet -> bao Arduino TAT chan limit (S = Scan mode)
                if not scanner.active:
                    send_raw("S")
                # Scanner TU XU LY limit (lat chieu khi cham)
                pan_scan, tilt_scan = scanner.compute(
                    time.time(),
                    lim_pan_neg, lim_pan_pos,
                    lim_tilt_neg, lim_tilt_pos,
                )
                axis_x.send_sps(pan_scan, send_raw)
                axis_y.send_sps(tilt_scan, send_raw)
            else:
                # Vua moi mat target, cho them chut moi quet -> tam dung
                axis_x.send_sps(0, send_raw)
                axis_y.send_sps(0, send_raw)

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

        # Trang thai: SCANNING / TRACKING
        mode_txt = "SCANNING" if scanner.active else ("TRACKING" if target_found else "WAITING")
        mode_color = (0, 165, 255) if scanner.active else ((0, 255, 0) if target_found else (200, 200, 200))
        cv2.putText(frame, mode_txt, (w - 140, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, mode_color, 2)

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