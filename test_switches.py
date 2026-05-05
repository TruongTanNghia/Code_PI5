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

# ================= YOLO MODEL =================
detector = MouseDetector()

# ================= TRACKING CONFIG =================
DEADZONE_X = 70
DEADZONE_Y = 60
SEND_INTERVAL = 0.05

last_pan_cmd = ""
last_tilt_cmd = ""
last_send_time = 0

last_dets = []
miss_count = 0

prev_t = time.time()
fps = 0.0


def send(cmd):
    ser.write(cmd.encode())


def send_pan(cmd):
    global last_pan_cmd
    if cmd != last_pan_cmd:
        send(cmd)
        last_pan_cmd = cmd


def send_tilt(cmd):
    global last_tilt_cmd
    if cmd != last_tilt_cmd:
        send(cmd)
        last_tilt_cmd = cmd


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

        if display_dets:
            det = max(display_dets, key=lambda d: d.get("conf", 0))

            x1, y1, x2, y2 = det["box"]
            obj_cx, obj_cy = det["center"]
            conf = det["conf"]

            dx = obj_cx - frame_cx
            dy = obj_cy - frame_cy

            target_found = True

            color = (0, 255, 0) if fresh else (0, 200, 200)

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.circle(frame, (obj_cx, obj_cy), 5, (0, 0, 255), -1)
            cv2.circle(frame, (frame_cx, frame_cy), 6, (255, 0, 0), -1)
            cv2.line(frame, (frame_cx, frame_cy), (obj_cx, obj_cy), (255, 255, 0), 2)

            cv2.putText(
                frame,
                f"mouse {conf:.2f} dx={dx} dy={dy}",
                (x1, max(20, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                color,
                2
            )

            now_send = time.time()
            if now_send - last_send_time >= SEND_INTERVAL:
                # PAN
                if dx > DEADZONE_X:
                    send_pan("d")
                elif dx < -DEADZONE_X:
                    send_pan("a")
                else:
                    send_pan("h")

                # TILT
                if dy > DEADZONE_Y:
                    send_tilt("s")
                elif dy < -DEADZONE_Y:
                    send_tilt("w")
                else:
                    send_tilt("v")

                last_send_time = now_send

        if not target_found:
            send_pan("h")
            send_tilt("v")

        # Vung chet o giua frame
        cv2.rectangle(
            frame,
            (frame_cx - DEADZONE_X, frame_cy - DEADZONE_Y),
            (frame_cx + DEADZONE_X, frame_cy + DEADZONE_Y),
            (255, 255, 255),
            1
        )

        # FPS
        now = time.time()
        dt = now - prev_t
        if dt > 0:
            fps = 0.9 * fps + 0.1 * (1.0 / dt)
        prev_t = now

        info = f"FPS: {fps:.1f} conf>={DET_CONF} detected:{len(display_dets)}"
        cv2.putText(frame, info, (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        cv2.imshow("Mouse Auto Tracking - RealSense", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

finally:
    send("x")
    time.sleep(0.2)
    ser.close()
    pipeline.stop()
    cv2.destroyAllWindows()