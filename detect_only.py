"""
Test camera + YOLO detection real-time (khong dung servo/laser).
Chay: python detect_only.py
ESC de thoat.
"""
import cv2
import time
from camera import Camera
from detector import MouseDetector
from config import DET_PERSIST_FRAMES, DET_CONF

cam = Camera()
detector = MouseDetector()  # dung MODEL_PATH trong config.py

print("[INFO] San sang. Nhan ESC trong cua so video de thoat.")

prev_t = time.time()
fps = 0.0

# Smoothing: giu lai box gan nhat them DET_PERSIST_FRAMES frame de chong nhay
last_dets = []
miss_count = 0

try:
    while True:
        ret, frame = cam.read()
        if not ret:
            continue

        detections = detector.detect(frame)

        if detections:
            last_dets = detections
            miss_count = 0
            display_dets = detections
            fresh = True
        else:
            miss_count += 1
            if miss_count <= DET_PERSIST_FRAMES:
                display_dets = last_dets  # giu box cu, tranh nhay
                fresh = False
            else:
                display_dets = []
                fresh = False

        for det in display_dets:
            x1, y1, x2, y2 = det["box"]
            cx, cy = det["center"]
            conf = det["conf"]

            # Box mau xanh khi fresh, vang nhat khi giu lai (persist)
            color = (0, 255, 0) if fresh else (0, 200, 200)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)
            cv2.putText(frame, f"mouse {conf:.2f}", (x1, y1 - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # FPS smoothed
        now = time.time()
        dt = now - prev_t
        if dt > 0:
            fps = 0.9 * fps + 0.1 * (1.0 / dt)
        prev_t = now

        info = f"FPS: {fps:.1f}  conf>={DET_CONF}  detected: {len(display_dets)}"
        cv2.putText(frame, info, (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        cv2.imshow("Mouse Detection - Pi5", frame)
        if cv2.waitKey(1) == 27:  # ESC
            break

finally:
    cam.release()
    cv2.destroyAllWindows()
