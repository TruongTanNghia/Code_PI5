import cv2
import math
from camera import Camera
from detector import MouseDetector
from servo import ServoController
from tracker import Tracker
from laser import LaserController
from config import (
    FRAME_WIDTH, FRAME_HEIGHT, KP,
    LOCK_THRESHOLD, LOCK_FRAMES_REQUIRED,
)

cam = Camera()
detector = MouseDetector("./results-mouse/best.pt")
servo = ServoController()
tracker = Tracker()
laser = LaserController()

last_target_pos = None
lost_frames = 0
MAX_LOST_FRAMES = 10

lock_count = 0  # so frame lien tuc muc tieu nam trong vung khoa

try:
    while True:
        ret, frame = cam.read()
        if not ret:
            continue

        center_x, center_y = FRAME_WIDTH // 2, FRAME_HEIGHT // 2

        # Vong tron khoa muc tieu (theo LOCK_THRESHOLD)
        cv2.circle(frame, (center_x, center_y), LOCK_THRESHOLD, (0, 255, 255), 1)
        # Khung ngam phu de de nhin
        sight_size = 150
        cv2.rectangle(frame,
                      (center_x - sight_size // 2, center_y - sight_size // 2),
                      (center_x + sight_size // 2, center_y + sight_size // 2),
                      (255, 0, 255), 1)
        cv2.drawMarker(frame, (center_x, center_y), (255, 255, 255),
                       cv2.MARKER_CROSS, 20, 1)

        detections = detector.detect(frame)

        # Chon muc tieu: uu tien con gan vi tri cu (persistence), khong thi gan tam nhat
        best_target = None
        min_dist = float('inf')
        for det in detections:
            x, y = det['center']
            if last_target_pos is not None:
                d_last = math.hypot(x - last_target_pos[0], y - last_target_pos[1])
                if d_last < 80:
                    best_target = det
                    break
            d_center = math.hypot(x - center_x, y - center_y)
            if d_center < min_dist:
                min_dist = d_center
                best_target = det

        if best_target:
            last_target_pos = best_target['center']
            lost_frames = 0
        else:
            lost_frames += 1
            if lost_frames > MAX_LOST_FRAMES:
                last_target_pos = None
                lock_count = 0  # mat muc tieu thi reset bo dem khoa

        # Ve UI + dieu khien servo + ban laser
        for det in detections:
            x, y = det['center']
            x1, y1, x2, y2 = det['box']

            if det is best_target:
                dx, dy = tracker.compute(x, y)
                if dx != 0:
                    servo.set_pan(servo.pan_angle - dx * KP)
                if dy != 0:
                    servo.set_tilt(servo.tilt_angle + dy * KP)

                # Tinh khoang cach den tam thuc te (khong dung dead_zone)
                dist_center = math.hypot(x - center_x, y - center_y)
                in_lock_zone = dist_center <= LOCK_THRESHOLD

                if in_lock_zone:
                    lock_count += 1
                else:
                    lock_count = 0

                # Khoa du lau -> ban
                fired_now = False
                if lock_count >= LOCK_FRAMES_REQUIRED and laser.can_fire():
                    fired_now = laser.fire_burst()

                # UI muc tieu
                color = (0, 0, 255)
                label = "TARGET LOCK"
                if laser.is_firing() or fired_now:
                    color = (0, 255, 255)
                    label = "FIRING!"
                elif in_lock_zone:
                    color = (0, 165, 255)
                    label = f"LOCKING {lock_count}/{LOCK_FRAMES_REQUIRED}"

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.line(frame, (center_x, center_y), (x, y), color, 2)
                cv2.putText(frame, label, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            else:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)
                cv2.putText(frame, "Mouse", (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

        # Status bar
        status = f"PAN:{int(servo.pan_angle)}  TILT:{int(servo.tilt_angle)}  " \
                 f"LASER:{'ON' if laser.is_firing() else 'OFF'}  LOCK:{lock_count}"
        cv2.putText(frame, status, (10, FRAME_HEIGHT - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        cv2.imshow("Mouse Tracking Pi5 - Laser", frame)
        if cv2.waitKey(1) == 27:  # ESC de thoat
            break

finally:
    laser.cleanup()
    cam.release()
    cv2.destroyAllWindows()
