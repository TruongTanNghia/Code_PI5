"""
Test camera + YOLO detection real-time (khong dung servo/laser).
Chay: python detect_only.py
ESC de thoat.
"""
import cv2
import time
from camera import Camera
from detector import MouseDetector
from config import FRAME_WIDTH, FRAME_HEIGHT

cam = Camera()
detector = MouseDetector("./results-mouse/best.pt")

print("[INFO] San sang. Nhan ESC trong cua so video de thoat.")

prev_t = time.time()
fps = 0.0

try:
    while True:
        ret, frame = cam.read()
        if not ret:
            continue

        detections = detector.detect(frame)

        # Ve bounding box cho moi con chuot phat hien duoc
        for det in detections:
            x1, y1, x2, y2 = det["box"]
            cx, cy = det["center"]
            conf = det["conf"]

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)
            cv2.putText(frame, f"mouse {conf:.2f}", (x1, y1 - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # FPS
        now = time.time()
        dt = now - prev_t
        if dt > 0:
            fps = 0.9 * fps + 0.1 * (1.0 / dt)
        prev_t = now

        cv2.putText(frame, f"FPS: {fps:.1f}  |  detected: {len(detections)}",
                    (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        cv2.imshow("Mouse Detection - Pi5", frame)
        if cv2.waitKey(1) == 27:  # ESC
            break

finally:
    cam.release()
    cv2.destroyAllWindows()
