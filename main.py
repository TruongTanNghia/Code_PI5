# import cv2
# import time
# import serial
# import numpy as np

# from detector import MouseDetector
# from config import DET_PERSIST_FRAMES, DET_CONF

# # ================= SERIAL ARDUINO =================
# # Windows: "COM3", "COM4"... (xem trong Device Manager > Ports)
# # Linux/Pi: "/dev/ttyUSB0", "/dev/ttyACM0"...
# import sys as _sys
# if _sys.platform.startswith("win"):
#     PORT = "COM3"          # <<< DOI sang COM that cua Arduino tren Windows
# else:
#     PORT = "/dev/ttyUSB0"  # tren Raspberry Pi
# BAUD = 9600

# ser = serial.Serial(PORT, BAUD, timeout=0.1)
# ser.setDTR(False)
# time.sleep(2)
# ser.write(b"M")   # bat che do Arduino bao trang thai limit (LIM:...) cho Python
# ser.flush()

# # ================= WEBCAM (OBSBOT Meet SE - UVC) =================
# # Cam UVC thuong -> dung OpenCV. Tu chon backend theo HE DIEU HANH:
# #   Windows -> CAP_DSHOW (hoac CAP_MSMF)
# #   Linux/Pi -> CAP_V4L2
# import sys
# CAM_INDEX = 0   # neu khong mo duoc, thu 1, 2...
# FRAME_W = 640
# FRAME_H = 480

# if sys.platform.startswith("win"):
#     cam_backend = cv2.CAP_DSHOW      # Windows
# else:
#     cam_backend = cv2.CAP_V4L2       # Linux / Raspberry Pi

# cap = cv2.VideoCapture(CAM_INDEX, cam_backend)
# cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_W)
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_H)
# cap.set(cv2.CAP_PROP_FPS, 30)
# # Giảm buffer để frame không bị trễ (lag) - quan trọng cho tracking
# cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

# if not cap.isOpened():
#     raise RuntimeError(
#         f"Khong mo duoc webcam o index {CAM_INDEX}. "
#         f"Thu doi CAM_INDEX sang 1, 2..."
#     )

# # ================= YOLO =================
# detector = MouseDetector()

# # ================= TRACKING CONFIG =================
# # Vùng "đứng yên" - vào trong vùng này thì motor dừng hẳn + laser bật.
# # Nhỏ hơn = laser ngắm chính xác hơn vào giữa con chuột, nhưng motor khó vào tâm.
# # Lon hon chut -> motor de "dung han" o tam, do rung qua lai quanh tam.
# DEADZONE_X = 45
# DEADZONE_Y = 45

# # ===== LASER OFFSET (CALIBRATE) =====
# # Laser gắn LỆCH so với camera -> điểm laser chiếu trên frame KHÔNG phải tâm frame.
# # Hai số này là vị trí laser thực sự, tính từ tâm frame.
# # Khi chương trình chạy, dùng phím I/J/K/L để dịch aim point cho đến khi
# # crosshair vàng trùng với chấm laser đỏ thật, rồi copy giá trị in trên console
# # vào đây cho lần chạy sau.
# LASER_OFFSET_X = 0
# LASER_OFFSET_Y = 0

# # Bước dịch khi nhấn phím calibrate
# CAL_STEP = 2

# # ===== TOC DO STEPPER (step/s) =====
# # Khi vat o ngay mep deadzone -> chay cham (MIN_SPS).
# # Khi vat o xa (>= MAX_ERROR) -> chay nhanh (MAX_SPS).
# # O giua -> noi suy tuyen tinh -> bam muot, gan tam tu cham lai.
# #
# # ===== CHONG QUAY LO (OVERSHOOT) =====
# # MAX_ERROR LON -> motor phai lech RAT xa moi chay het toc -> gan tam rat cham.
# # MAX_SPS VUA PHAI -> khong vot qua tam.
# # MIN_SPS NHO -> sat tam thi bo tung ti -> dung dung cho.
# MAX_ERROR_X = 450     # pixel: keo dai -> pan cham lai som hon khi gan tam
# MAX_ERROR_Y = 380     # pixel: tilt tuong tu

# PAN_MAX_SPS  = 1800   # ha tu 3500 -> 1800: cham hon, khong vot qua tam
# PAN_MIN_SPS  = 120    # sat tam bo rat cham -> vao chinh xac
# TILT_MAX_SPS = 1500   # tilt cham hon chut
# TILT_MIN_SPS = 100

# # Chi gui lenh toc do moi khi thay doi du lon -> do spam serial.
# SPS_SEND_STEP = 60     # step/s: chenh nho hon nay thi khong gui lai
# SEND_THROTTLE = 0.02   # giay: toi thieu giua 2 lan gui cua 1 truc

# # ===== CHE DO QUET (khi khong thay muc tieu) =====
# # Quet hinh chu S: pan qua lai trai-phai, moi lan doi chieu thi tilt nhich 1 buoc.
# # Khi phat hien chuot lai -> tu dong dung quet, chuyen sang bam.
# SCAN_PAN_SPS    = 800     # toc do pan luc quet (cham vua phai de detect kip)
# SCAN_TILT_SPS   = 600     # toc do tilt luc nhich len/xuong
# SCAN_TILT_STEP_TIME = 0.3 # giay: thoi gian nhich tilt moi khi doi chieu pan
# SCAN_START_DELAY = 0.5    # giay: cho bao lau khi mat target moi bat dau quet


# class Scanner:
#     """
#     Quet hinh chu S de tim muc tieu.
#     Pan qua lai, moi lan cham limit (hoac lat chieu) thi tilt nhich 1 chut.
#     Khi tilt cham limit ca 2 dau -> dao chieu nhich tilt.
#     """
#     def __init__(self):
#         self.active = False
#         self.pan_dir = +1       # +1 = phai, -1 = trai
#         self.tilt_dir = +1      # +1 = xuong, -1 = len
#         self.tilt_nudge_until = 0.0   # tilt chay den thoi diem nay thi dung
#         self.lost_since = None        # thoi diem mat target
#         self.last_flip_t = 0.0

#     def on_target_found(self):
#         """Co target lai -> tat quet."""
#         self.active = False
#         self.lost_since = None

#     def on_target_lost(self):
#         """Mat target -> chuan bi quet sau SCAN_START_DELAY giay."""
#         if self.lost_since is None:
#             self.lost_since = time.time()

#     def should_scan(self):
#         """Co nen quet luc nay khong?"""
#         if self.lost_since is None:
#             return False
#         return (time.time() - self.lost_since) >= SCAN_START_DELAY

#     def compute(self, now, lim_pan_neg, lim_pan_pos, lim_tilt_neg, lim_tilt_pos):
#         """
#         Tinh toc do pan/tilt de quet.
#         - Cham limit huong dang quet -> LAT CHIEU (tu quay nguoc lai).
#         - Khi lat chieu pan -> kich tilt nhich len/xuong 1 chut.
#         - Cham limit tilt dang nhich -> lat chieu tilt.
#         """
#         self.active = True

#         # ===== PAN: cham limit huong dang di -> lat chieu =====
#         if (self.pan_dir > 0 and lim_pan_pos) or (self.pan_dir < 0 and lim_pan_neg):
#             self.pan_dir = -self.pan_dir
#             self.tilt_nudge_until = now + SCAN_TILT_STEP_TIME  # tilt nhich 1 buoc
#             self.last_flip_t = now

#         # Sau khi lat, huong moi nguoc lai -> KHONG con cham limit -> chay binh thuong
#         pan_sps = SCAN_PAN_SPS * self.pan_dir

#         # ===== TILT: dang trong cua so nhich? =====
#         if now < self.tilt_nudge_until:
#             # Cham limit huong tilt dang di -> lat chieu
#             if (self.tilt_dir > 0 and lim_tilt_pos) or (self.tilt_dir < 0 and lim_tilt_neg):
#                 self.tilt_dir = -self.tilt_dir
#             tilt_sps = SCAN_TILT_SPS * self.tilt_dir
#         else:
#             tilt_sps = 0

#         return pan_sps, tilt_sps


# scanner = Scanner()


# class StepperAxis:
#     """
#     Dieu khien 1 truc stepper bang TOC DO (step/s).
#     Tinh toc do ti le voi sai so -> chay muot, tu cham lai khi gan tam.
#     Gui lenh "P<sps>\n" (pan) hoac "T<sps>\n" (tilt) toi Arduino.
#     """

#     def __init__(self, axis_letter, deadzone, max_error,
#                  max_sps, min_sps):
#         self.axis = axis_letter        # 'P' cho pan, 'T' cho tilt
#         self.deadzone = deadzone
#         self.max_error = max_error
#         self.max_sps = max_sps
#         self.min_sps = min_sps

#         self.last_sps_sent = None
#         self.last_send_t = 0.0
#         self.current_sps = 0           # de debug

#     def _sps_from_error(self, error):
#         """Tra ve toc do co dau (am/duong) theo huong va do lon sai so."""
#         abs_err = abs(error)
#         if abs_err <= self.deadzone:
#             return 0
#         if abs_err >= self.max_error:
#             mag = self.max_sps
#         else:
#             ratio = (abs_err - self.deadzone) / (self.max_error - self.deadzone)
#             mag = self.min_sps + (self.max_sps - self.min_sps) * ratio
#         sps = int(mag)
#         return sps if error > 0 else -sps

#     def update(self, error, send_raw, force_stop=False,
#                block_pos=False, block_neg=False):
#         now = time.time()
#         sps = 0 if force_stop else self._sps_from_error(error)

#         # ===== CHAN KEP: neu da cham limit huong dang muon di -> ep dung huong do =====
#         # block_pos: da cham limit phia duong (P/T > 0)
#         # block_neg: da cham limit phia am   (P/T < 0)
#         if sps > 0 and block_pos:
#             sps = 0
#         elif sps < 0 and block_neg:
#             sps = 0

#         self.current_sps = sps

#         # Chi gui khi thay doi dang ke (hoac khi can dung han / khoi dong lai).
#         changed_enough = (
#             self.last_sps_sent is None
#             or (sps == 0 and self.last_sps_sent != 0)        # vua moi dung
#             or (sps != 0 and self.last_sps_sent == 0)        # vua moi chay
#             or abs(sps - self.last_sps_sent) >= SPS_SEND_STEP
#         )
#         if changed_enough and (now - self.last_send_t) >= SEND_THROTTLE:
#             send_raw(f"{self.axis}{sps}\n")
#             self.last_sps_sent = sps
#             self.last_send_t = now

#     def send_sps(self, sps, send_raw,
#                  block_pos=False, block_neg=False):
#         """Gui toc do thang (dung cho Scanner). Co chan limit."""
#         now = time.time()
#         sps = int(sps)
#         if sps > 0 and block_pos:
#             sps = 0
#         elif sps < 0 and block_neg:
#             sps = 0
#         self.current_sps = sps

#         changed_enough = (
#             self.last_sps_sent is None
#             or (sps == 0 and self.last_sps_sent != 0)
#             or (sps != 0 and self.last_sps_sent == 0)
#             or abs(sps - self.last_sps_sent) >= SPS_SEND_STEP
#         )
#         if changed_enough and (now - self.last_send_t) >= SEND_THROTTLE:
#             send_raw(f"{self.axis}{sps}\n")
#             self.last_sps_sent = sps
#             self.last_send_t = now


# def send_raw(s):
#     """Gửi chuỗi thẳng tới Arduino (dùng cho lệnh tốc độ P/T)."""
#     ser.write(s.encode())
#     ser.flush()


# def send(cmd):
#     print("[SEND]", cmd)
#     ser.write(cmd.encode())
#     ser.flush()


# # ================= LIMIT SWITCH STATE (doc tu Arduino) =================
# # Thu tu Arduino gui "LIM:up,down,left,right" = A0,A1,A2,A3
# #   A0 = len   (tilt am)   -> lim_tilt_neg
# #   A1 = xuong (tilt duong)-> lim_tilt_pos
# #   A2 = trai  (pan am)    -> lim_pan_neg
# #   A3 = phai  (pan duong) -> lim_pan_pos
# lim_tilt_neg = False
# lim_tilt_pos = False
# lim_pan_neg = False
# lim_pan_pos = False
# _serial_buf = ""

# def poll_limits():
#     """Doc cac dong Arduino gui, cap nhat trang thai limit. Khong block.
#     Cac dong khac (MODE:, OK ..., READY...) in ra console de debug."""
#     global _serial_buf, lim_tilt_neg, lim_tilt_pos, lim_pan_neg, lim_pan_pos
#     try:
#         n = ser.in_waiting
#     except Exception:
#         return
#     if n:
#         _serial_buf += ser.read(n).decode(errors="ignore")
#         # xu ly tung dong hoan chinh
#         while "\n" in _serial_buf:
#             line, _serial_buf = _serial_buf.split("\n", 1)
#             line = line.strip()
#             if not line:
#                 continue
#             if line.startswith("LIM:"):
#                 try:
#                     parts = line[4:].split(",")
#                     a0, a1, a2, a3 = (int(p) for p in parts[:4])
#                     lim_tilt_neg = bool(a0)
#                     lim_tilt_pos = bool(a1)
#                     lim_pan_neg = bool(a2)
#                     lim_pan_pos = bool(a3)
#                 except Exception:
#                     pass
#             else:
#                 # Cac thong bao khac tu Arduino: MODE:, OK ..., READY...
#                 print(f"[ARD] {line}")


# # ================= LASER =================
# laser_on = False

# def set_laser(on):
#     """Chỉ gửi serial khi trạng thái laser thật sự đổi."""
#     global laser_on
#     if on and not laser_on:
#         send("L")
#         laser_on = True
#     elif (not on) and laser_on:
#         send("K")
#         laser_on = False


# # Trục ngang (pan): dx > 0 -> đối tượng ở bên phải -> camera quay phải (P dương)
# axis_x = StepperAxis(
#     axis_letter="P", deadzone=DEADZONE_X, max_error=MAX_ERROR_X,
#     max_sps=PAN_MAX_SPS, min_sps=PAN_MIN_SPS
# )
# # Trục dọc (tilt): dy > 0 -> đối tượng ở phía dưới -> camera cúi xuống (T dương)
# axis_y = StepperAxis(
#     axis_letter="T", deadzone=DEADZONE_Y, max_error=MAX_ERROR_Y,
#     max_sps=TILT_MAX_SPS, min_sps=TILT_MIN_SPS
# )

# last_dets = []
# miss_count = 0
# prev_t = time.time()
# fps = 0.0

# # Offset runtime, init từ config, có thể chỉnh bằng I/J/K/L
# laser_offset_x = LASER_OFFSET_X
# laser_offset_y = LASER_OFFSET_Y


# try:
#     print("[INFO] Webcam + YOLO tracking ready. ESC de thoat.")

#     while True:
#         ret, frame = cap.read()
#         if not ret or frame is None:
#             print("[WARN] Khong doc duoc frame, thu lai...")
#             continue
#         h, w = frame.shape[:2]
#         frame_cx = w // 2
#         frame_cy = h // 2

#         # Điểm "đích ngắm" thực tế = vị trí laser chiếu trên frame
#         aim_x = frame_cx + laser_offset_x
#         aim_y = frame_cy + laser_offset_y

#         detections = detector.detect(frame)

#         if detections:
#             last_dets = detections
#             miss_count = 0
#             display_dets = detections
#             fresh = True
#         else:
#             miss_count += 1
#             if miss_count <= DET_PERSIST_FRAMES:
#                 display_dets = last_dets
#                 fresh = False
#             else:
#                 display_dets = []
#                 fresh = False

#         target_found = False
#         dx = 0
#         dy = 0
#         center_in_deadzone = False

#         if display_dets:
#             # Chon target GAN TAM CAMERA NHAT (uu tien khi co nhieu muc tieu)
#             def _dist_to_aim(d):
#                 cx, cy = d["center"]
#                 return (cx - aim_x) ** 2 + (cy - aim_y) ** 2
#             det = min(display_dets, key=_dist_to_aim)
#             x1, y1, x2, y2 = det["box"]
#             obj_cx, obj_cy = det["center"]
#             conf = det["conf"]

#             target_found = True

#             # ===== ERROR THEO TÂM BOX vs AIM POINT (laser thực tế) =====
#             # Laser gắn lệch -> phải kéo tâm con chuột về điểm laser chiếu,
#             # KHÔNG phải về tâm frame.
#             dx = obj_cx - aim_x
#             dy = obj_cy - aim_y

#             center_in_deadzone = (abs(dx) <= DEADZONE_X and abs(dy) <= DEADZONE_Y)

#             color = (0, 255, 0) if fresh else (0, 200, 200)

#             # Vẽ mask seg (tô màu vùng con chuột) nếu có
#             seg_mask = det.get("mask")
#             if seg_mask is not None:
#                 overlay = frame.copy()
#                 overlay[seg_mask] = color
#                 cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)

#             cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
#             cv2.circle(frame, (obj_cx, obj_cy), 5, (0, 0, 255), -1)
#             cv2.line(frame, (aim_x, aim_y),
#                      (obj_cx, obj_cy), (255, 255, 0), 2)
#             cv2.putText(
#                 frame,
#                 f"mouse {conf:.2f} dx={dx} dy={dy}",
#                 (x1, max(20, y1 - 8)),
#                 cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2
#             )

#         # ===== Doc trang thai limit tu Arduino (chac kep) =====
#         poll_limits()

#         # ===== Điều khiển motor: BAM hoac QUET =====
#         if target_found:
#             # Co target -> bam theo. Bao Arduino BAT che do TRACK (chan cung limit).
#             if scanner.active or scanner.lost_since is not None:
#                 send_raw("F")  # F = Follow/track mode -> chan limit
#             scanner.on_target_found()
#             axis_x.update(dx, send_raw, force_stop=False,
#                           block_pos=lim_pan_pos, block_neg=lim_pan_neg)
#             axis_y.update(dy, send_raw, force_stop=False,
#                           block_pos=lim_tilt_pos, block_neg=lim_tilt_neg)
#         else:
#             # Mat target -> chuyen sang quet sau SCAN_START_DELAY.
#             scanner.on_target_lost()
#             if scanner.should_scan():
#                 # Lan dau vao quet -> bao Arduino TAT chan limit (S = Scan mode)
#                 if not scanner.active:
#                     send_raw("S")
#                 # Scanner TU XU LY limit (lat chieu khi cham)
#                 pan_scan, tilt_scan = scanner.compute(
#                     time.time(),
#                     lim_pan_neg, lim_pan_pos,
#                     lim_tilt_neg, lim_tilt_pos,
#                 )
#                 axis_x.send_sps(pan_scan, send_raw)
#                 axis_y.send_sps(tilt_scan, send_raw)
#             else:
#                 # Vua moi mat target, cho them chut moi quet -> tam dung
#                 axis_x.send_sps(0, send_raw)
#                 axis_y.send_sps(0, send_raw)

#         # ===== Laser: bật khi tâm con chuột đã vào deadzone =====
#         in_target = target_found and center_in_deadzone
#         set_laser(in_target)

#         # ===== Vẽ vùng deadzone quanh AIM POINT (xanh = trúng, trắng = chưa) =====
#         dz_color = (0, 255, 0) if (target_found and center_in_deadzone) else (255, 255, 255)
#         cv2.rectangle(
#             frame,
#             (aim_x - DEADZONE_X, aim_y - DEADZONE_Y),
#             (aim_x + DEADZONE_X, aim_y + DEADZONE_Y),
#             dz_color, 1
#         )

#         # Crosshair vàng đánh dấu AIM POINT (vị trí laser thực tế)
#         # Khi calibrate đúng, crosshair này phải trùng với chấm laser thật trên frame.
#         cv2.drawMarker(frame, (aim_x, aim_y), (0, 255, 255),
#                        markerType=cv2.MARKER_CROSS, markerSize=20, thickness=2)
#         # Chấm xanh dương = tâm frame thật (tham chiếu)
#         cv2.circle(frame, (frame_cx, frame_cy), 3, (255, 0, 0), -1)

#         # ===== FPS =====
#         now = time.time()
#         dt = now - prev_t
#         if dt > 0:
#             fps = 0.9 * fps + 0.1 * (1.0 / dt)
#         prev_t = now

#         info = f"FPS: {fps:.1f} conf>={DET_CONF} det:{len(display_dets)}"
#         cv2.putText(frame, info, (10, 25),
#                     cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

#         # Debug motor: toc do step/s dang gui
#         dbg = (f"PAN sps={axis_x.current_sps}  "
#                f"TILT sps={axis_y.current_sps}")
#         cv2.putText(frame, dbg, (10, 80),
#                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

#         # Trang thai: SCANNING / TRACKING
#         mode_txt = "SCANNING" if scanner.active else ("TRACKING" if target_found else "WAITING")
#         mode_color = (0, 165, 255) if scanner.active else ((0, 255, 0) if target_found else (200, 200, 200))
#         cv2.putText(frame, mode_txt, (w - 140, 25),
#                     cv2.FONT_HERSHEY_SIMPLEX, 0.6, mode_color, 2)

#         # Debug limit: hien cong tac nao dang cham (mau do)
#         lim_txt = "LIM:"
#         lim_txt += " LEN" if lim_tilt_neg else ""
#         lim_txt += " XUONG" if lim_tilt_pos else ""
#         lim_txt += " TRAI" if lim_pan_neg else ""
#         lim_txt += " PHAI" if lim_pan_pos else ""
#         if lim_txt != "LIM:":
#             cv2.putText(frame, lim_txt, (10, 100),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

#         # Hiển thị offset hiện tại để calibrate
#         cv2.putText(frame,
#                     f"OFFSET x={laser_offset_x} y={laser_offset_y}  [I/J/K/L=move, R=reset]",
#                     (10, h - 15),
#                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

#         # Chỉ báo trạng thái laser
#         if laser_on:
#             cv2.putText(frame, "LASER ON", (10, 55),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
#             cv2.circle(frame, (w - 30, 30), 12, (0, 0, 255), -1)

#         cv2.imshow("Mouse Auto Tracking", frame)
#         key = cv2.waitKey(1) & 0xFF
#         if key == 27:    # ESC
#             break
#         elif key == ord('i'):
#             laser_offset_y -= CAL_STEP
#             print(f"[CAL] OFFSET = ({laser_offset_x}, {laser_offset_y})")
#         elif key == ord('k'):
#             laser_offset_y += CAL_STEP
#             print(f"[CAL] OFFSET = ({laser_offset_x}, {laser_offset_y})")
#         elif key == ord('j'):
#             laser_offset_x -= CAL_STEP
#             print(f"[CAL] OFFSET = ({laser_offset_x}, {laser_offset_y})")
#         elif key == ord('l'):
#             laser_offset_x += CAL_STEP
#             print(f"[CAL] OFFSET = ({laser_offset_x}, {laser_offset_y})")
#         elif key == ord('r'):
#             laser_offset_x = 0
#             laser_offset_y = 0
#             print(f"[CAL] OFFSET reset = (0, 0)")

# finally:
#     set_laser(False)
#     send("x")
#     time.sleep(0.2)
#     ser.close()
#     cap.release()
#     cv2.destroyAllWindows()

import cv2
import time
import serial
import numpy as np

from detector import MouseDetector
from config import DET_PERSIST_FRAMES, DET_CONF

# ============= OVERRIDE NGUONG PHAT HIEN (uu tien hon config.py) =============
# DET_CONF cang CAO -> can chac chan hon moi tinh la chuot (it nham, nhung
# co the bo lo). Cang THAP -> de phat hien hon (nhung de nham vat khac).
# Khuyen nghi: 0.5 - 0.7 cho ngoai canh thuc te.
DET_CONF = 0.5             # <<< CHINH NGUONG TAI DAY (cu = 0.25, gio = 0.5)

# So frame "nho" detection cu khi YOLO bo lo 1-2 frame (chong nhap nhay).
# Cang LON -> bam on dinh hon, khong scan loan khi YOLO mat 1 vai frame.
# Cang NHO -> phan ung nhanh khi chuot di mat (nhung dieu de scan loan).
DET_PERSIST_FRAMES = 15    # <<< Tang tu mac dinh (thuong 5-10) len 15

# ================= SERIAL ARDUINO =================
# Windows: "COM3", "COM4"... (xem trong Device Manager > Ports)
# Linux/Pi: "/dev/ttyUSB0", "/dev/ttyACM0"...
import sys as _sys
if _sys.platform.startswith("win"):
    PORT = "COM5"          # <<< DOI sang COM that cua Arduino tren Windows
else:
    PORT = "/dev/ttyUSB0"  # tren Raspberry Pi
BAUD = 9600

ser = serial.Serial(PORT, BAUD, timeout=0.1)
ser.setDTR(False)
time.sleep(2)                       # cho Arduino reset xong
ser.reset_input_buffer()            # clear bo dem (bo cac dong READY ban dau)
ser.write(b"M\n")                   # bat machine-report (LIM:...)
ser.flush()
time.sleep(0.1)
ser.write(b"F\n")                   # mac dinh TRACK mode (chan cung cham limit)
ser.flush()
print(f"[INFO] Da gui M (machine-report) va F (track mode) toi Arduino.")
print(f"[INFO] Anh quan sat terminal: phai thay '[ARD] LIM:...' khi cham cong tac.")

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

# ================= YOLO: HAI MO HINH (bat/tat de DEMO) =================
# Co 2 mo hinh:
#   - CHUOT GIA : mo hinh cu (segmentation) - bat chuot gia/do choi
#   - CHUOT THAT: mo hinh moi (YOLO12n)      - bat chuot that
# Luc chay, nhan phim 'M' de doi qua lai giua 2 mo hinh.
MODEL_GIA  = "best_seg.pt"        # chuot GIA (segmentation) - GIU NGUYEN TEN
MODEL_THAT = "best_chuotthat.pt"  # chuot THAT (YOLO12n)

# Box model chuot THAT: co/gian QUANH TAM con chuot.
#   So CANG LON -> box CANG TO (om het con chuot). So nho -> box nho lai.
#   1.0 = giu nguyen box model (truoc bi to gap doi), 0.7 = vua om giua con chuot.
BOX_SCALE_THAT = 0.7

# Model chuot THAT kho nhan hon (chuot nau tren nen be tong xam) -> rieng no:
#   CONF_THAT  thap hon  -> de phat hien hon (nhung de nham hon)
#   IMGSZ_THAT lon hon   -> anh vao net hon -> detect chuan hon (cham hon chut)
CONF_THAT  = 0.25   # ha xuong 0.25 cho DE PHAT HIEN. Neu nham vat khac thi tang len.
IMGSZ_THAT = 640    # tu 320 -> 640. Neu lag thi ha xuong 512 hoac 416.

print(f"[INFO] Nap mo hinh CHUOT GIA : {MODEL_GIA}")
detector_gia = MouseDetector(model_path=MODEL_GIA, conf=DET_CONF)

# ----- CHUOT THAT: uu tien Roboflow CLOUD, khong duoc thi dung model local -----
# USE_ROBOFLOW_THAT = True -> chuot that goi Roboflow tung khung hinh.
#   LUU Y: cloud co do TRE -> tracking cham hon (~2-5 FPS). Can internet.
#   API KEY: KHONG hardcode. Dat 1 trong 2:
#     - bien moi truong ROBOFLOW_API_KEY, hoac
#     - file roboflow_key.txt (cung thu muc, da gitignore) chua API key.
USE_ROBOFLOW_THAT  = False   # False = dung model LOCAL best_chuotthat.pt (realtime)
ROBOFLOW_WORKSPACE = "ngo-van-phat"
ROBOFLOW_WORKFLOW  = "track-objects-in-video"
ROBOFLOW_IMG_INPUT = "image"
ROBOFLOW_CONF      = 0.40

def _load_roboflow_key():
    k = _osm.environ.get("ROBOFLOW_API_KEY")
    if k and k.strip():
        return k.strip()
    if _osm.path.exists("roboflow_key.txt"):
        try:
            with open("roboflow_key.txt") as _fk:
                return _fk.read().strip()
        except Exception:
            pass
    return None

detector_that = None
if USE_ROBOFLOW_THAT:
    _rf_key = _load_roboflow_key()
    if not _rf_key:
        print("[WARN] Chua co API key Roboflow -> dung model local thay the.")
        print("       Tao file roboflow_key.txt (chua API key) hoac dat bien ROBOFLOW_API_KEY.")
    else:
        try:
            from roboflow_detector import RoboflowDetector
            detector_that = RoboflowDetector(
                api_key=_rf_key,
                workspace=ROBOFLOW_WORKSPACE,
                workflow_id=ROBOFLOW_WORKFLOW,
                image_input=ROBOFLOW_IMG_INPUT,
                conf=ROBOFLOW_CONF,
            )
            print("[INFO] CHUOT THAT = Roboflow CLOUD (track-objects-in-video)")
        except Exception as _erf:
            print(f"[WARN] Khong dung duoc Roboflow ({_erf}) -> dung model local.")

if detector_that is None:
    print(f"[INFO] CHUOT THAT = model local {MODEL_THAT}")
    detector_that = MouseDetector(model_path=MODEL_THAT, conf=CONF_THAT,
                                  imgsz=IMGSZ_THAT, box_scale=BOX_SCALE_THAT)

# Ten hien thi cho chuot that (cloud hay local)
MODEL_THAT_LABEL = "CHUOT THAT" if isinstance(detector_that, MouseDetector) else "CHUOT THAT (cloud)"

# Mac dinh dung mo hinh CHUOT GIA. Nhan 'M' luc chay de doi.
detector = detector_gia
model_name = "CHUOT GIA"

# ================= TRACKING CONFIG =================
# Vùng "đứng yên" - vào trong vùng này thì motor dừng hẳn -> san sang BAN.
# NHO -> tam camera trung sat tam chuot hon. LON -> motor de "dung han" hon.
DEADZONE_X = 15   # nho -> tam vang bam SAT cham do. Neu lac qua -> tang len 20-25
DEADZONE_Y = 15   # da co EMA lam muot nen giam deadzone van it lac

# ===== DAO CHIEU TRACKING =====
# Neu camera quay NGUOC LAI so voi con chuot -> doi True<->False cho truc do.
#   INVERT_PAN  = lat chieu PAN  (trai/phai)
#   INVERT_TILT = lat chieu TILT (len/xuong)
# Cach chinh: chay main.py, dua chuot sang PHAI khung hinh.
#   - Neu camera quay sang PHAI (dung) -> giu nguyen.
#   - Neu camera quay sang TRAI (sai)  -> doi INVERT_PAN.
# Tuong tu cho tilt: dua chuot XUONG duoi, camera phai cui XUONG.
INVERT_PAN  = False   # da test: chuot ben PHAI -> phai pan PHAI -> INVERT_PAN=False
INVERT_TILT = False   # neu tilt nguoc (chuot duoi ma cam nguoc len) -> doi True

# ===== DIEM NGAM LASER (AIM POINT) - offset pixel so voi TAM frame =====
# Tam vang (crosshair) = noi laser THUC SU chieu len anh.
# Tracking se keo TAM con chuot ve dung diem nay -> laser trung chuot.
# CALIBRATE LUC CHAY: dung phim
#   I = len, K = xuong, J = trai, L = phai  (dich tam vang)
#   R = reset ve giua,  O = LUU offset ra file aim_offset.txt
# Keo tam vang den khi NO TRUNG cham laser do that tren tuong, roi bam O de luu.
AIM_OFFSET_FILE = "aim_offset.txt"
AIM_OFFSET_X = 0      # se nap tu file neu co
AIM_OFFSET_Y = 0
AIM_CAL_STEP = 3      # moi lan bam phim dich bao nhieu pixel

# ===== NGAM VAO CANH TREN BOX (thay vi tam box) =====
# True -> tam ngam bam vao CANH TREN giua box con chuot (de laser trung dau).
# AIM_TOP_MARGIN = nhich them xuong duoi canh tren bao nhieu px (0 = dung canh tren,
#   duong = thap xuong 1 chut vao trong box, am = cao hon canh tren).
AIM_AT_TOP = True
AIM_TOP_MARGIN = 0

import os as _os2
if _os2.path.exists(AIM_OFFSET_FILE):
    try:
        with open(AIM_OFFSET_FILE) as _f2:
            _ax, _ay = _f2.read().strip().split(",")
            AIM_OFFSET_X = int(_ax)
            AIM_OFFSET_Y = int(_ay)
            print(f"[INFO] Loaded aim offset pixel: x={AIM_OFFSET_X}, y={AIM_OFFSET_Y}")
    except Exception as _e2:
        print(f"[WARN] khong doc duoc {AIM_OFFSET_FILE}: {_e2}")

# ===== LASER FIRE CONFIG =====
# Sau khi vao deadzone (tam cam vao tam chuot), motor quay them OFFSET buoc
# de laser truc tiep chieu vao chuot, BAN 1 phat, roi quay nguoc lai.
# OFFSET nay calibrate truoc bang 'calibrate_laser.py' va luu vao file
# laser_offset.txt. Day la GOC LECH co dinh giua tam cam va tia laser.
LASER_OFFSET_FILE = "laser_offset.txt"
LASER_OFFSET_PAN_STEPS = 0    # se overwrite tu file neu co
LASER_OFFSET_TILT_STEPS = 0

# Toc do step/s khi quay den vi tri ban (vua phai, dut khoat)
AIM_SPS = 1200

# Thoi gian laser sang khi ban (giay)
LASER_ON_TIME = 3.0

# Sau khi ban xong, doi bao lau roi moi cho ban tiep lan nua (giay)
# (giua 2 phat ban, chuot phai ra khoi deadzone roi vao lai)
FIRE_COOLDOWN = 0.5

# Load offset tu file (neu co)
import os as _os
if _os.path.exists(LASER_OFFSET_FILE):
    try:
        with open(LASER_OFFSET_FILE) as _f:
            _line = _f.read().strip()
            _p, _t = _line.split(",")
            LASER_OFFSET_PAN_STEPS = int(_p)
            LASER_OFFSET_TILT_STEPS = int(_t)
            print(f"[INFO] Loaded laser offset: pan={LASER_OFFSET_PAN_STEPS}, "
                  f"tilt={LASER_OFFSET_TILT_STEPS} steps")
    except Exception as _e:
        print(f"[WARN] khong doc duoc {LASER_OFFSET_FILE}: {_e}")
else:
    print(f"[WARN] Khong tim thay {LASER_OFFSET_FILE}.")
    print(f"       Chay 'calibrate_laser.py' truoc de calibrate.")
    print(f"       Hien tai offset = (0, 0) -> laser se chieu vao TAM camera.")


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
PAN_MIN_SPS  = 160    # sat san Arduino (150): bo CHAM khi gan tam -> bam khit, it vot
TILT_MAX_SPS = 1500   # tilt cham hon chut
TILT_MIN_SPS = 160    # sat san: bo cham khi gan tam

# Chi gui lenh toc do moi khi thay doi du lon -> do spam serial.
SPS_SEND_STEP = 60     # step/s: chenh nho hon nay thi khong gui lai
SEND_THROTTLE = 0.02   # giay: toi thieu giua 2 lan gui cua 1 truc

# ===== CHE DO QUET (khi khong thay muc tieu) =====
# Quet hinh chu S: pan qua lai trai-phai, moi lan doi chieu thi tilt nhich 1 buoc.
# Khi phat hien chuot lai -> tu dong dung quet, chuyen sang bam.
SCAN_PAN_SPS    = 400     # toc do pan luc quet (giam nua: 800 -> 400, detect ky hon)
SCAN_TILT_SPS   = 300     # toc do tilt luc nhich len/xuong (giam nua: 600 -> 300)
SCAN_TILT_STEP_TIME = 0.3 # giay: thoi gian nhich tilt moi khi doi chieu pan
SCAN_START_DELAY = 2.0    # giay: doi LAU hon truoc khi quet (tu 0.5 -> 2.0)
                          # giup khong scan loan khi YOLO nhap nhay 1-2 frame

# Sau khi DAO CHIEU, BO QUA cong tac trong khoang thoi gian nay (giay).
# -> camera chay han 1 doan moi nhan cong tac tiep -> CONG TAC NHIEU (chatter)
#    khong lam camera ket/dao loan tai cho nua.
# TANG len neu van bi ket (vd 2.0); GIAM neu muon dao nhanh hon (vd 1.0).
SCAN_FLIP_BLACKOUT = 1.5

# LUOI AN TOAN: quet 1 huong qua lau ma CHUA cham cong tac -> TU DAO CHIEU.
# -> cong tac co hut/khong an thi camera van khong bao gio ket cung.
# Dat LON hon thoi gian quet het 1 ben de CONG TAC la cai dao chinh
# (luoi chi du phong). Vung rong thi tang them; vung hep co the giam.
SCAN_MAX_SWEEP_TIME = 8.0

# ===== CHE DO QUET (TUAN TRA) =====
# USE_COORD_SCAN = False -> QUET THEO CONG TAC HANH TRINH (yeu cau de bai):
#     Pan quay 1 huong, CHAM cong tac -> DAO CHIEU quay nguoc lai.
#     (dau cheo: quay phai cham cong tac trai -> ve trai, va nguoc lai;
#      phan Arduino da map san A2/A3 nen logic chi can dung lim_pan_pos/neg)
# USE_COORD_SCAN = True  -> quet theo toa do [PAN_LIMIT_MIN, MAX] (khong dung cong tac).
USE_COORD_SCAN = False
PAN_SCAN_RANGE = 3000              # mac dinh neu chua dat vung
PAN_LIMIT_MIN = -PAN_SCAN_RANGE    # mep TRAI vung tuan tra (step)
PAN_LIMIT_MAX = +PAN_SCAN_RANGE    # mep PHAI vung tuan tra (step)
PAN_RANGE_FILE = "pan_range.txt"
if _os2.path.exists(PAN_RANGE_FILE):
    try:
        with open(PAN_RANGE_FILE) as _fpr:
            _lo, _hi = _fpr.read().strip().split(",")
            PAN_LIMIT_MIN, PAN_LIMIT_MAX = int(_lo), int(_hi)
            print(f"[INFO] Vung tuan tra: {PAN_LIMIT_MIN}..{PAN_LIMIT_MAX} step")
    except Exception as _e:
        print(f"[WARN] khong doc duoc {PAN_RANGE_FILE}: {_e}")


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
        self.tilt_nudge_until = 0.0
        self.lost_since = None
        self.last_flip_t = 0.0
        # Bien EDGE detect: nho trang thai limit lan truoc de chi LAT 1 LAN
        # khi cham, khong lat lien tuc khi limit con dinh.
        self._prev_lim_pan_pos = False
        self._prev_lim_pan_neg = False
        self._prev_lim_tilt_pos = False
        self._prev_lim_tilt_neg = False
        # Cooldown sau khi lat -> 0.3s khong lat lai (tranh rung)
        self._pan_flip_lock_until = 0.0
        # Thoi diem bat dau quay theo huong hien tai (de FAILSAFE theo thoi gian)
        self._dir_start_t = None
        # ARMED: san sang nhan cong tac de dao chieu.
        # Sau khi dao -> DISARM, chi ARM lai khi cong tac da NHA (camera roi cong tac)
        # -> chong dao loan/dao nham do tin hieu cong tac cu con dinh.
        self._armed = True

    def on_target_found(self):
        """Co target lai -> tat quet."""
        self.active = False
        self.lost_since = None
        self._dir_start_t = None   # reset timer huong quet cho lan scan sau
        self._armed = True

    def on_target_lost(self):
        """Mat target -> chuan bi quet sau SCAN_START_DELAY giay."""
        if self.lost_since is None:
            self.lost_since = time.time()

    def should_scan(self):
        """Co nen quet luc nay khong?"""
        if self.lost_since is None:
            return False
        return (time.time() - self.lost_since) >= SCAN_START_DELAY

    def compute(self, now, pan_hit_latched, pan_pressed_now,
                lim_tilt_neg, lim_tilt_pos, pan_pos=0.0):
        """
        Quet pan qua lai. Dao chieu khi:
          - (CHE DO CONG TAC) cham BAT KY cong tac pan -> dao, roi PHAI thay
            cong tac NHA ra moi cho dao lan ke (chong dao loan/dao nham).
          - (CHE DO TOA DO) pan_pos ra ngoai vung [MIN, MAX].
        Co LUOI AN TOAN theo thoi gian: di 1 huong qua lau -> tu dao.
        """
        self.active = True

        # Bat dau dem thoi gian cho huong quet hien tai
        if self._dir_start_t is None:
            self._dir_start_t = now

        flip = False
        if USE_COORD_SCAN:
            # ===== QUET THEO TOA DO =====
            if self.pan_dir > 0 and pan_pos >= PAN_LIMIT_MAX:
                flip = True
            elif self.pan_dir < 0 and pan_pos <= PAN_LIMIT_MIN:
                flip = True
        else:
            # ===== QUET THEO CONG TAC HANH TRINH (yeu cau de bai) =====
            # ARM lai khi cong tac da NHA + qua thoi gian toi thieu sau lan dao truoc.
            # -> dam bao camera da ROI khoi cong tac vua cham moi nhan cham tiep.
            if not self._armed:
                if (not pan_pressed_now) and (now - self.last_flip_t >= SCAN_FLIP_BLACKOUT):
                    self._armed = True
            # Dang ARMED + co cham cong tac (latch) -> DAO CHIEU
            if self._armed and pan_hit_latched:
                flip = True

        # ===== LUOI AN TOAN: di 1 huong qua lau ma chua dao -> tu dao =====
        if (now - self._dir_start_t) >= SCAN_MAX_SWEEP_TIME:
            flip = True
            print("[SCAN] failsafe: quet qua lau chua dao -> tu dao chieu")

        if flip:
            self.pan_dir = -self.pan_dir
            self.tilt_nudge_until = now + SCAN_TILT_STEP_TIME
            self.last_flip_t = now
            self._dir_start_t = now      # reset timer cho huong moi
            self._armed = False          # cho cong tac NHA ra moi armed lai
            print(f"[SCAN] DAO CHIEU -> gio quay {'PHAI' if self.pan_dir > 0 else 'TRAI'}")

        # LUON chay theo huong hien tai (Arduino khong chan pan luc scan).
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
# LATCH (chot): he nhin thay cong tac pan CHAM (du chi thoang qua giua 2 vong loop)
# thi GHI NHO lai -> khong bo lo cu cham ngan khi quet nhanh.
# Scanner doc xong se xoa (= False).
pan_lim_latch = False
_serial_buf = ""

def poll_limits():
    """Doc cac dong Arduino gui, cap nhat trang thai limit. Khong block.
    Cac dong khac (MODE:, OK ..., READY...) in ra console de debug."""
    global _serial_buf, lim_tilt_neg, lim_tilt_pos, lim_pan_neg, lim_pan_pos
    global pan_lim_latch
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
            if not line:
                continue
            if line.startswith("LIM:"):
                try:
                    parts = line[4:].split(",")
                    a0, a1, a2, a3 = (int(p) for p in parts[:4])
                    new_state = (bool(a0), bool(a1), bool(a2), bool(a3))
                    old_state = (lim_tilt_neg, lim_tilt_pos, lim_pan_neg, lim_pan_pos)
                    if new_state != old_state:
                        print(f"[LIM] LEN={a0} XUONG={a1} ngat-tr={a2} ngat-ph={a3}")
                    lim_tilt_neg = bool(a0)
                    lim_tilt_pos = bool(a1)
                    lim_pan_neg = bool(a2)
                    lim_pan_pos = bool(a3)
                    # CHOT cu cham pan: chi can 1 lan thay 1 -> ghi nho (khong bo lo)
                    if a2 or a3:
                        pan_lim_latch = True
                except Exception:
                    pass
            else:
                # Cac thong bao khac tu Arduino: MODE:, OK ..., READY...
                print(f"[ARD] {line}")


# ================= LASER =================
laser_on = False

def set_laser(on):
    """Chi gui serial khi trang thai laser that su doi."""
    global laser_on
    if on and not laser_on:
        send("L")
        laser_on = True
    elif (not on) and laser_on:
        send("K")
        laser_on = False


# ================= FIRE SEQUENCE =================
# Khi vao deadzone, thuc hien tuan tu:
#   1. Quay them OFFSET_PAN_STEPS + OFFSET_TILT_STEPS de laser ngam trung chuot.
#   2. Bat laser LASER_ON_TIME giay -> ban.
#   3. Tat laser, quay nguoc lai ve vi tri cu (tam cam ngam vao tam chuot).
#   4. Doi FIRE_COOLDOWN, va doi chuot ra khoi deadzone -> moi cho ban lan sau.
#
# Cach hoat dong: gui lenh toc do AIM_SPS theo chieu OFFSET, giu trong khoang
# thoi gian = |offset_steps| / AIM_SPS giay -> dung. Sau do quay nguoc lai.

fire_state = "idle"        # idle / aim / shoot / return / cooldown
fire_t0 = 0.0              # thoi diem bat dau giai doan hien tai
fire_target_pan = False    # con can quay them pan/tilt khong
fire_target_tilt = False
fire_already_in_dz = False # da vao deadzone tu lan truoc chua (de tranh ban lien tuc)


def fire_axis_move(axis_letter, steps_to_move):
    """Tinh toc do gui cho 1 truc de quay 'steps_to_move' buoc (co dau)."""
    if steps_to_move == 0:
        return 0, 0.0
    sps = AIM_SPS if steps_to_move > 0 else -AIM_SPS
    duration = abs(steps_to_move) / AIM_SPS
    send_raw(f"{axis_letter}{sps}\n")
    return sps, duration


def fire_step(target_in_deadzone):
    """
    Cap nhat may trang thai ban moi vong loop.
    Tra ve True neu dang ban (block tracking).
    target_in_deadzone: tam chuot co dang trong deadzone khong.

    !!! NEU OFFSET = 0 (chua calibrate) -> KHONG kich hoat ban.
        He thong chay nhu cu: tracking + scan, KHONG ban.
        Chi sau khi chay calibrate_laser.py va luu offset thi moi ban.
    """
    global fire_state, fire_t0, fire_already_in_dz

    # An toan: chua calibrate -> tat ban hoan toan, khong dung tracking
    if LASER_OFFSET_PAN_STEPS == 0 and LASER_OFFSET_TILT_STEPS == 0:
        return False

    now = time.time()

    if fire_state == "idle":
        # Co dieu kien ban: target trong deadzone + chua vao deadzone trong lan truoc
        if target_in_deadzone and not fire_already_in_dz:
            # Bat dau ban: quay den vi tri laser-aim
            fire_already_in_dz = True
            fire_state = "aim"
            fire_t0 = now
            # Gui lenh quay pan + tilt voi so buoc offset
            fire_axis_move("P", LASER_OFFSET_PAN_STEPS)
            fire_axis_move("T", LASER_OFFSET_TILT_STEPS)
            return True
        # Khi target ra khoi deadzone -> san sang ban lan sau
        if not target_in_deadzone:
            fire_already_in_dz = False
        return False

    if fire_state == "aim":
        # Cho cho den khi quay du so buoc
        aim_duration = max(
            abs(LASER_OFFSET_PAN_STEPS) / AIM_SPS,
            abs(LASER_OFFSET_TILT_STEPS) / AIM_SPS,
        )
        if now - fire_t0 >= aim_duration:
            # Dung motor, bat laser
            send_raw("P0\n")
            send_raw("T0\n")
            send("L")
            global laser_on
            laser_on = True
            fire_state = "shoot"
            fire_t0 = now
        return True

    if fire_state == "shoot":
        # Giu laser sang trong LASER_ON_TIME
        if now - fire_t0 >= LASER_ON_TIME:
            send("K")
            laser_on = False
            fire_state = "return"
            fire_t0 = now
            # Gui lenh quay NGUOC LAI ve vi tri cu (tam cam vao tam chuot)
            fire_axis_move("P", -LASER_OFFSET_PAN_STEPS)
            fire_axis_move("T", -LASER_OFFSET_TILT_STEPS)
        return True

    if fire_state == "return":
        return_duration = max(
            abs(LASER_OFFSET_PAN_STEPS) / AIM_SPS,
            abs(LASER_OFFSET_TILT_STEPS) / AIM_SPS,
        )
        if now - fire_t0 >= return_duration:
            send_raw("P0\n")
            send_raw("T0\n")
            fire_state = "cooldown"
            fire_t0 = now
        return True

    if fire_state == "cooldown":
        if now - fire_t0 >= FIRE_COOLDOWN:
            fire_state = "idle"
            # Chua reset fire_already_in_dz -> phai cho target ra khoi deadzone
            # roi vao lai moi ban tiep
        # COOLDOWN KHONG block tracking -> motor di lai chuot ngay,
        # khong khung sau khi ban (truoc day return True lam cam dung 0.5s)
        return False

    return False


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

# Tam muc tieu da LAM MUOT (EMA) -> chong box YOLO nhay tung frame -> het lac.
# SMOOTH cang NHO -> muot hon nhung tre hon. 0.4-0.6 la vua.
smooth_cx = None
smooth_cy = None
SMOOTH_ALPHA = 0.5

# Vi tri uoc luong truc PAN (step). + = phai, - = trai. Tich phan tu toc do.
pan_pos_steps = 0.0

# ===== LASER BURST: ban bao nhieu giay moi lan =====
LASER_BURST = 3.5          # giay
SETTLE_TIME = 0.4          # giay: chuot phai o yen trong vung + motor DUNG HAN
                           # bao lau roi moi ban (tang -> chac chan dung hon)
laser_armed = True
laser_fire_until = 0.0
dz_enter_t = None          # thoi diem chuot bat dau vao vung (de tinh settle)

# Theo doi mode hien tai de chi gui F/S khi DOI mode, khong spam
_current_mode = None     # "TRACK" hoac "SCAN", None luc dau

# Gui lai lenh "M" (bat bao cong tac) dinh ky -> neu Arduino lo reset thi
# cong tac van duoc bao lai (khong bi "het nhan tin hieu cong tac").
_last_m_resend = 0.0
M_RESEND_EVERY = 2.0     # giay


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
        # Diem ngam laser = tam frame + offset pixel (calibrate bang phim I/J/K/L)
        aim_x = frame_cx + AIM_OFFSET_X
        aim_y = frame_cy + AIM_OFFSET_Y

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
                return (cx - frame_cx) ** 2 + (cy - frame_cy) ** 2
            det = min(display_dets, key=_dist_to_aim)
            x1, y1, x2, y2 = det["box"]
            conf = det["conf"]

            # Diem muc tieu = CANH TREN giua box cho CA 2 model.
            # (laser gan LECH -> ngam vao mep tren box thi laser moi trung)
            if AIM_AT_TOP:
                raw_cx = (x1 + x2) // 2
                raw_cy = y1 + AIM_TOP_MARGIN
            else:
                raw_cx, raw_cy = det["center"]

            # ===== LAM MUOT tam (EMA) -> chong lac do box nhay =====
            if smooth_cx is None:
                smooth_cx, smooth_cy = float(raw_cx), float(raw_cy)
            else:
                smooth_cx = SMOOTH_ALPHA * raw_cx + (1 - SMOOTH_ALPHA) * smooth_cx
                smooth_cy = SMOOTH_ALPHA * raw_cy + (1 - SMOOTH_ALPHA) * smooth_cy
            obj_cx, obj_cy = int(smooth_cx), int(smooth_cy)

            target_found = True

            # ===== ERROR THEO TÂM BOX vs TAM CAMERA =====
            # Error TU NHIEN:
            #   dx > 0 = chuot ben PHAI tam  -> can pan PHAI (sps duong)
            #   dy > 0 = chuot phia DUOI tam -> can tilt XUONG (sps duong)
            # Neu camera quay nguoc -> doi INVERT_PAN / INVERT_TILT o tren.
            dx = obj_cx - aim_x
            dy = obj_cy - aim_y
            if INVERT_PAN:
                dx = -dx
            if INVERT_TILT:
                dy = -dy

            center_in_deadzone = (abs(dx) <= DEADZONE_X and abs(dy) <= DEADZONE_Y)

            # === LOG debug huong: in moi 10 frame ===
            if miss_count == 0 and (int(time.time() * 5) % 5 == 0):
                print(f"[TRACK] chuot tai ({obj_cx},{obj_cy}), tam cam ({frame_cx},{frame_cy}), "
                      f"dx={dx} dy={dy}  -> motor nen quay: "
                      f"pan={'PHAI' if dx > 0 else 'TRAI' if dx < 0 else '-'}, "
                      f"tilt={'XUONG' if dy > 0 else 'LEN' if dy < 0 else '-'}")

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

        # Mat target hoan toan -> quen tam muot cu (lan sau bat lai khong bi keo)
        if not display_dets:
            smooth_cx = None
            smooth_cy = None

        # ===== Doc trang thai limit tu Arduino (chac kep) =====
        poll_limits()

        # Gui lai "M" dinh ky -> Arduino lo reset van bat lai bao cong tac.
        if time.time() - _last_m_resend >= M_RESEND_EVERY:
            send_raw("M\n")
            _last_m_resend = time.time()

        # ===== LASER: chi ban khi DA DUNG HAN tren muc tieu =====
        # Dieu kien ban: chuot trong deadzone + motor DUNG (sps=0) + on dinh SETTLE_TIME.
        # Phai RA khoi vung roi VAO lai moi ban phat tiep.
        target_in_deadzone = target_found and center_in_deadzone
        _now_laser = time.time()
        motor_stopped = (axis_x.current_sps == 0 and axis_y.current_sps == 0)

        if target_in_deadzone:
            if dz_enter_t is None:
                dz_enter_t = _now_laser
            # Da o yen trong vung + motor dung du lau chua?
            settled = motor_stopped and (_now_laser - dz_enter_t >= SETTLE_TIME)

            if laser_armed and settled:
                laser_fire_until = _now_laser + LASER_BURST
                laser_armed = False
                set_laser(True)
            elif (not laser_armed) and _now_laser < laser_fire_until:
                set_laser(True)      # dang trong burst -> giu sang
            else:
                set_laser(False)     # chua settle, hoac het burst -> tat
            # Neu motor dang chay lai (chuot nhuc nhich) -> reset settle timer
            if not motor_stopped:
                dz_enter_t = _now_laser
        else:
            set_laser(False)         # ra khoi vung -> tat
            laser_armed = True       # nap lai cho phat sau
            dz_enter_t = None
        is_firing = False

        # ===== Điều khiển motor =====
        if target_found:
            # Co target -> bam theo. Chi gui F khi DOI MODE sang TRACK
            if _current_mode != "TRACK":
                send_raw("F")
                _current_mode = "TRACK"
            scanner.on_target_found()
            axis_x.update(dx, send_raw, force_stop=False,
                          block_pos=lim_pan_pos, block_neg=lim_pan_neg)
            axis_y.update(dy, send_raw, force_stop=False,
                          block_pos=lim_tilt_pos, block_neg=lim_tilt_neg)
        else:
            # Mat target -> chuyen sang quet sau SCAN_START_DELAY.
            scanner.on_target_lost()
            if scanner.should_scan():
                # Chi gui S khi DOI MODE sang SCAN
                if _current_mode != "SCAN":
                    send_raw("S")
                    _current_mode = "SCAN"
                # pan_hit_latched: co cu cham pan (ke ca thoang qua, nho LATCH).
                # pan_pressed_now: cong tac pan dang nhan NGAY LUC NAY (live) ->
                #   de biet camera da NHA cong tac chua (arm lai).
                pan_hit_latched = lim_pan_pos or lim_pan_neg or pan_lim_latch
                pan_pressed_now = lim_pan_pos or lim_pan_neg
                pan_scan, tilt_scan = scanner.compute(
                    time.time(),
                    pan_hit_latched, pan_pressed_now,
                    lim_tilt_neg, lim_tilt_pos,
                    pan_pos=pan_pos_steps,
                )
                pan_lim_latch = False   # da tieu thu chot -> xoa
                axis_x.send_sps(pan_scan, send_raw)
                axis_y.send_sps(tilt_scan, send_raw)
            else:
                # Vua moi mat target, cho them chut moi quet -> tam dung
                axis_x.send_sps(0, send_raw)
                axis_y.send_sps(0, send_raw)

        # Laser giu nguyen, fire_step lo bat/tat. Khong dung set_laser cu nua.

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

        # ===== DEM TOA DO PAN (tich phan toc do) =====
        if dt > 0:
            pan_pos_steps += axis_x.current_sps * dt
        # KHONG snap theo cong tac nua (cong tac chap chon lam pin toa do -> ket).
        # Neu sau nay cong tac on dinh, co the bat lai snap o day.

        prev_t = now

        info = f"FPS: {fps:.1f} conf>={detector.conf} det:{len(display_dets)}"
        cv2.putText(frame, info, (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        # Debug motor: toc do step/s dang gui
        dbg = (f"PAN sps={axis_x.current_sps}  "
               f"TILT sps={axis_y.current_sps}")
        cv2.putText(frame, dbg, (10, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        # Ten mo hinh dang dung (demo) + huong dan doi
        model_color = (0, 255, 0) if detector is detector_gia else (255, 0, 255)
        cv2.putText(frame, f"MODEL: {model_name}  [M=doi mo hinh]", (10, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, model_color, 2)

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

        # Hien thi offset laser (step) - co dinh, chinh trong calibrate_laser.py
        cv2.putText(frame,
                    f"LASER OFFSET steps: pan={LASER_OFFSET_PAN_STEPS} tilt={LASER_OFFSET_TILT_STEPS}",
                    (10, h - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 0), 1)

        # Chi bao trang thai laser / fire state
        if fire_state != "idle":
            cv2.putText(frame, f"FIRING: {fire_state.upper()}", (10, 55),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.circle(frame, (w - 30, 30), 12, (0, 0, 255), -1)
        elif laser_on:
            cv2.putText(frame, "LASER ON", (10, 55),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.circle(frame, (w - 30, 30), 12, (0, 0, 255), -1)

        # ===== Hien vung tuan tra + vi tri pan =====
        cv2.putText(frame,
                    f"PATROL: {PAN_LIMIT_MIN}..{PAN_LIMIT_MAX}  PANpos={int(pan_pos_steps)}  "
                    f"[H=set0  [=mep trai  ]=mep phai]",
                    (10, h - 58),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
        # ===== Hien huong dan calibrate tam ngam =====
        cv2.putText(frame,
                    f"AIM offset x={AIM_OFFSET_X} y={AIM_OFFSET_Y}  "
                    f"[I/K J/L R=reset O=luu]",
                    (10, h - 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)

        cv2.imshow("Mouse Auto Tracking", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:    # ESC
            break
        elif key == ord('i'):       # tam vang LEN
            AIM_OFFSET_Y -= AIM_CAL_STEP
            print(f"[AIM] offset = ({AIM_OFFSET_X}, {AIM_OFFSET_Y})")
        elif key == ord('k'):       # tam vang XUONG
            AIM_OFFSET_Y += AIM_CAL_STEP
            print(f"[AIM] offset = ({AIM_OFFSET_X}, {AIM_OFFSET_Y})")
        elif key == ord('j'):       # tam vang TRAI
            AIM_OFFSET_X -= AIM_CAL_STEP
            print(f"[AIM] offset = ({AIM_OFFSET_X}, {AIM_OFFSET_Y})")
        elif key == ord('l'):       # tam vang PHAI
            AIM_OFFSET_X += AIM_CAL_STEP
            print(f"[AIM] offset = ({AIM_OFFSET_X}, {AIM_OFFSET_Y})")
        elif key == ord('r'):       # reset ve giua
            AIM_OFFSET_X = 0
            AIM_OFFSET_Y = 0
            print(f"[AIM] offset reset = (0, 0)")
        elif key == ord('o'):       # LUU ra file
            try:
                with open(AIM_OFFSET_FILE, "w") as _fw:
                    _fw.write(f"{AIM_OFFSET_X},{AIM_OFFSET_Y}")
                print(f"[AIM] DA LUU offset ({AIM_OFFSET_X}, {AIM_OFFSET_Y}) "
                      f"-> {AIM_OFFSET_FILE}")
            except Exception as _ew:
                print(f"[AIM] luu that bai: {_ew}")
        elif key == ord('h'):       # HOME: set vi tri pan hien tai = 0 (tam tuan tra)
            pan_pos_steps = 0.0
            print("[PAN] set vi tri hien tai = 0 (tam tuan tra)")
        elif key == ord('['):       # dat MEP TRAI vung tuan tra = vi tri hien tai
            PAN_LIMIT_MIN = int(pan_pos_steps)
            print(f"[PATROL] mep TRAI = {PAN_LIMIT_MIN}")
            try:
                with open(PAN_RANGE_FILE, "w") as _fp:
                    _fp.write(f"{PAN_LIMIT_MIN},{PAN_LIMIT_MAX}")
                print(f"[PATROL] da luu {PAN_LIMIT_MIN}..{PAN_LIMIT_MAX}")
            except Exception as _e:
                print(f"[PATROL] luu loi: {_e}")
        elif key == ord(']'):       # dat MEP PHAI vung tuan tra = vi tri hien tai
            PAN_LIMIT_MAX = int(pan_pos_steps)
            print(f"[PATROL] mep PHAI = {PAN_LIMIT_MAX}")
            try:
                with open(PAN_RANGE_FILE, "w") as _fp:
                    _fp.write(f"{PAN_LIMIT_MIN},{PAN_LIMIT_MAX}")
                print(f"[PATROL] da luu {PAN_LIMIT_MIN}..{PAN_LIMIT_MAX}")
            except Exception as _e:
                print(f"[PATROL] luu loi: {_e}")
        elif key == ord('m'):       # DOI MO HINH (demo: chuot GIA <-> chuot THAT)
            if detector is detector_gia:
                detector = detector_that
                model_name = MODEL_THAT_LABEL
            else:
                detector = detector_gia
                model_name = "CHUOT GIA"
            # Xoa detection cu + tam muot de khong bi keo theo mo hinh truoc
            last_dets = []
            miss_count = DET_PERSIST_FRAMES + 1
            smooth_cx = None
            smooth_cy = None
            print(f"[MODEL] >>> Da chuyen sang mo hinh: {model_name}")

finally:
    set_laser(False)
    send("x")
    time.sleep(0.2)
    ser.close()
    cap.release()
    cv2.destroyAllWindows()