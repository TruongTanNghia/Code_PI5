import cv2
import time
import serial
import numpy as np
import pyrealsense2 as rs

from detector import MouseDetector
from config import DET_PERSIST_FRAMES, DET_CONF

# ================= SERIAL ARDUINO =================
PORT = "/dev/ttyUSB0"
BAUD = 9600

ser = serial.Serial(PORT, BAUD, timeout=0.1)
ser.setDTR(False)
time.sleep(2)

# ================= REALSENSE =================
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
pipeline.start(config)

# ================= YOLO =================
detector = MouseDetector()

# ================= TRACKING CONFIG =================
# Vùng "đứng yên" - vào trong vùng này thì motor dừng hẳn + laser bật.
# Nhỏ hơn = laser ngắm chính xác hơn vào giữa con chuột, nhưng motor khó vào tâm.
DEADZONE_X = 35
DEADZONE_Y = 40

# Khoảng cách (pixel) tính từ deadzone, tại đó motor chạy hết tốc (duty=1.0).
# Kéo dài thêm -> motor phải lệch rất xa mới full-speed -> chậm tổng thể.
MAX_ERROR_X = 400
MAX_ERROR_Y = 440

# Duty tối thiểu khi gần deadzone. Hạ thấp -> mỗi pulse rất ngắn -> nhích ít.
# Nếu motor không nhúc nhích được nữa thì TĂNG LẠI (lực ma sát tĩnh).
MIN_DUTY_X = 0.06
MIN_DUTY_Y = 0.05

# Chu kỳ PWM phần mềm. RÚT NGẮN -> mỗi cú nhích ngắn hơn hẳn.
# (vd duty 0.05 * cycle 0.04s = motor chỉ chạy 2ms mỗi nhịp, rồi nghỉ 38ms)
CYCLE_PERIOD = 0.04

# Throttle nhẹ tránh spam serial khi command đổi liên tục.
SEND_THROTTLE = 0.01


class AxisController:
    """
    PWM phần mềm cho 1 trục.
    Tự tính duty cycle dựa trên sai số dx (hoặc dy).
    Chỉ gửi serial khi command đổi -> không spam Arduino.
    """

    def __init__(self, pos_cmd, neg_cmd, stop_cmd,
                 deadzone, max_error,
                 min_duty,
                 cycle_period=CYCLE_PERIOD):
        self.pos_cmd = pos_cmd        # vd: 'd' (phải) hoặc 's' (xuống)
        self.neg_cmd = neg_cmd        # vd: 'a' (trái) hoặc 'w' (lên)
        self.stop_cmd = stop_cmd      # vd: 'h' hoặc 'v'
        self.deadzone = deadzone
        self.max_error = max_error
        self.min_duty = min_duty
        self.cycle_period = cycle_period

        self.last_cmd = None
        self.last_send_t = 0.0
        self.cycle_t0 = time.time()

    def _duty_from_error(self, abs_err):
        if abs_err <= self.deadzone:
            return 0.0
        if abs_err >= self.max_error:
            return 1.0
        # ramp tuyến tính từ min_duty -> 1.0
        ratio = (abs_err - self.deadzone) / (self.max_error - self.deadzone)
        return self.min_duty + (1.0 - self.min_duty) * ratio

    def update(self, error, send_fn, force_stop=False):
        now = time.time()

        if force_stop:
            duty = 0.0
        else:
            duty = self._duty_from_error(abs(error))

        if duty <= 0.0:
            target = self.stop_cmd
        else:
            # Trong mỗi chu kỳ CYCLE_PERIOD: ON trong (duty * CYCLE_PERIOD),
            # OFF phần còn lại -> tạo nhịp pulse.
            phase = (now - self.cycle_t0) % self.cycle_period
            on_window = duty * self.cycle_period
            if phase < on_window:
                target = self.pos_cmd if error > 0 else self.neg_cmd
            else:
                target = self.stop_cmd

        # Chỉ gửi khi command thực sự đổi (giảm tải serial + Arduino).
        if target != self.last_cmd and (now - self.last_send_t) >= SEND_THROTTLE:
            send_fn(target)
            self.last_cmd = target
            self.last_send_t = now


def send(cmd):
    print("[SEND]", cmd)
    ser.write(cmd.encode())
    ser.flush()


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


# Trục ngang (pan): dx > 0 -> đối tượng ở bên phải -> camera quay phải ('d')
axis_x = AxisController(
    pos_cmd="d", neg_cmd="a", stop_cmd="h",
    deadzone=DEADZONE_X, max_error=MAX_ERROR_X,
    min_duty=MIN_DUTY_X
)
# Trục dọc (tilt): dy > 0 -> đối tượng ở phía dưới -> camera cúi xuống ('s')
axis_y = AxisController(
    pos_cmd="s", neg_cmd="w", stop_cmd="v",
    deadzone=DEADZONE_Y, max_error=MAX_ERROR_Y,
    min_duty=MIN_DUTY_Y
)

last_dets = []
miss_count = 0
prev_t = time.time()
fps = 0.0


try:
    print("[INFO] RealSense + YOLO tracking ready. ESC de thoat.")

    while True:
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        if not color_frame:
            continue

        frame = np.asanyarray(color_frame.get_data())
        h, w = frame.shape[:2]
        frame_cx = w // 2
        frame_cy = h // 2

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

            # ===== ERROR THEO TÂM BOX vs TÂM FRAME =====
            # Laser gắn cố định ở tâm frame -> phải kéo tâm con chuột về đó
            # thì laser mới chiếu giữa con chuột.
            dx = obj_cx - frame_cx
            dy = obj_cy - frame_cy

            center_in_deadzone = (abs(dx) <= DEADZONE_X and abs(dy) <= DEADZONE_Y)

            color = (0, 255, 0) if fresh else (0, 200, 200)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.circle(frame, (obj_cx, obj_cy), 5, (0, 0, 255), -1)
            cv2.circle(frame, (frame_cx, frame_cy), 6, (255, 0, 0), -1)
            cv2.line(frame, (frame_cx, frame_cy),
                     (obj_cx, obj_cy), (255, 255, 0), 2)
            cv2.putText(
                frame,
                f"mouse {conf:.2f} dx={dx} dy={dy}",
                (x1, max(20, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2
            )

        # ===== Điều khiển motor: PWM phần mềm theo sai số =====
        # Khi mất target -> force_stop=True -> motor dừng ngay.
        axis_x.update(dx, send, force_stop=not target_found)
        axis_y.update(dy, send, force_stop=not target_found)

        # ===== Laser: bật khi tâm con chuột đã vào deadzone =====
        in_target = target_found and center_in_deadzone
        set_laser(in_target)

        # ===== Vẽ vùng deadzone (xanh = tâm chuột trong vùng, trắng = chưa) =====
        dz_color = (0, 255, 0) if (target_found and center_in_deadzone) else (255, 255, 255)
        cv2.rectangle(
            frame,
            (frame_cx - DEADZONE_X, frame_cy - DEADZONE_Y),
            (frame_cx + DEADZONE_X, frame_cy + DEADZONE_Y),
            dz_color, 1
        )

        # ===== FPS =====
        now = time.time()
        dt = now - prev_t
        if dt > 0:
            fps = 0.9 * fps + 0.1 * (1.0 / dt)
        prev_t = now

        info = f"FPS: {fps:.1f} conf>={DET_CONF} det:{len(display_dets)}"
        cv2.putText(frame, info, (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        # Chỉ báo trạng thái laser
        if laser_on:
            cv2.putText(frame, "LASER ON", (10, 55),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.circle(frame, (w - 30, 30), 12, (0, 0, 255), -1)

        cv2.imshow("Mouse Auto Tracking - RealSense", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

finally:
    set_laser(False)
    send("x")
    time.sleep(0.2)
    ser.close()
    pipeline.stop()
    cv2.destroyAllWindows()