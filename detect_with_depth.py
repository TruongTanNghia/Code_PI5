"""
RealSense D435: phat hien chuot bang YOLO + hien khoang cach thuc te (met).
Chay: python detect_with_depth.py
ESC de thoat.
"""
import cv2
import time
from realsense_camera import RealSenseCamera
from detector import MouseDetector
from config import FRAME_WIDTH, FRAME_HEIGHT, DET_PERSIST_FRAMES, DET_CONF

cam = RealSenseCamera(width=FRAME_WIDTH, height=FRAME_HEIGHT, fps=30)
detector = MouseDetector()

print("[INFO] San sang. ESC de thoat.")

prev_t = time.time()
fps = 0.0
last_dets = []
miss_count = 0

try:
    while True:
        ret, frame = cam.read()
        if not ret:
            time.sleep(0.005)
            continue

        detections = detector.detect(frame)

        if detections:
            last_dets = detections
            miss_count = 0
            display_dets = detections
            fresh = True
        else:
            miss_count += 1
            display_dets = last_dets if miss_count <= DET_PERSIST_FRAMES else []
            fresh = False

        for det in display_dets:
            x1, y1, x2, y2 = det["box"]
            cx, cy = det["center"]
            conf = det["conf"]

            # Khoang cach: lay median trong vung center 20% cua box (chinh xac hon)
            bw, bh = x2 - x1, y2 - y1
            mx1 = cx - bw // 10
            mx2 = cx + bw // 10
            my1 = cy - bh // 10
            my2 = cy + bh // 10
            dist_m = cam.get_distance_in_box(mx1, my1, mx2, my2)

            color = (0, 255, 0) if fresh else (0, 200, 200)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)

            label = f"mouse {conf:.2f}"
            if dist_m > 0:
                label += f"  {dist_m:.2f}m"
            cv2.putText(frame, label, (x1, y1 - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

            # Vach noi tu tam frame den chuot
            cv2.line(frame,
                     (FRAME_WIDTH // 2, FRAME_HEIGHT // 2),
                     (cx, cy), color, 1)

        # FPS
        now = time.time()
        dt = now - prev_t
        if dt > 0:
            fps = 0.9 * fps + 0.1 * (1.0 / dt)
        prev_t = now

        info = f"FPS: {fps:.1f}  conf>={DET_CONF}  detected: {len(display_dets)}"
        cv2.putText(frame, info, (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        # Tam ngam
        cv2.drawMarker(frame,
                       (FRAME_WIDTH // 2, FRAME_HEIGHT // 2),
                       (255, 255, 255), cv2.MARKER_CROSS, 18, 1)

        cv2.imshow("Mouse + Distance (RealSense D435)", frame)
        if cv2.waitKey(1) == 27:
            break

finally:
    cam.release()
    cv2.destroyAllWindows()
