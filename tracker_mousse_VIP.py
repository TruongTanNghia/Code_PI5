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

# VĂ¹ng "Ä‘á»©ng yĂªn" - vĂ o trong vĂ¹ng nĂ y thĂ¬ motor dá»«ng háº³n + laser báº­t.

# Nhá» hÆ¡n = laser ngáº¯m chĂ­nh xĂ¡c hÆ¡n vĂ o giá»¯a con chuá»™t, nhÆ°ng motor khĂ³ vĂ o tĂ¢m.

DEADZONE_X = 35

DEADZONE_Y = 40



# Khoáº£ng cĂ¡ch (pixel) tĂ­nh tá»« deadzone, táº¡i Ä‘Ă³ motor cháº¡y háº¿t tá»‘c (duty=1.0).

# KĂ©o dĂ i thĂªm -> motor pháº£i lá»‡ch ráº¥t xa má»›i full-speed -> cháº­m tá»•ng thá»ƒ.

MAX_ERROR_X = 400

MAX_ERROR_Y = 440



# Duty tá»‘i thiá»ƒu khi gáº§n deadzone. Háº¡ tháº¥p -> má»—i pulse ráº¥t ngáº¯n -> nhĂ­ch Ă­t.

# Náº¿u motor khĂ´ng nhĂºc nhĂ­ch Ä‘Æ°á»£c ná»¯a thĂ¬ TÄ‚NG Láº I (lá»±c ma sĂ¡t tÄ©nh).

MIN_DUTY_X = 0.06

MIN_DUTY_Y = 0.05



# Chu ká»³ PWM pháº§n má»m. RĂT NGáº®N -> má»—i cĂº nhĂ­ch ngáº¯n hÆ¡n háº³n.

# (vd duty 0.05 * cycle 0.04s = motor chá»‰ cháº¡y 2ms má»—i nhá»‹p, rá»“i nghá»‰ 38ms)

CYCLE_PERIOD = 0.04



# Throttle nháº¹ trĂ¡nh spam serial khi command Ä‘á»•i liĂªn tá»¥c.

SEND_THROTTLE = 0.01





class AxisController:

    """

    PWM pháº§n má»m cho 1 trá»¥c.

    Tá»± tĂ­nh duty cycle dá»±a trĂªn sai sá»‘ dx (hoáº·c dy).

    Chá»‰ gá»­i serial khi command Ä‘á»•i -> khĂ´ng spam Arduino.

    """



    def __init__(self, pos_cmd, neg_cmd, stop_cmd,

                 deadzone, max_error,

                 min_duty,

                 cycle_period=CYCLE_PERIOD):

        self.pos_cmd = pos_cmd        # vd: 'd' (pháº£i) hoáº·c 's' (xuá»‘ng)

        self.neg_cmd = neg_cmd        # vd: 'a' (trĂ¡i) hoáº·c 'w' (lĂªn)

        self.stop_cmd = stop_cmd      # vd: 'h' hoáº·c 'v'

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

        # ramp tuyáº¿n tĂ­nh tá»« min_duty -> 1.0

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

            # Trong má»—i chu ká»³ CYCLE_PERIOD: ON trong (duty * CYCLE_PERIOD),

            # OFF pháº§n cĂ²n láº¡i -> táº¡o nhá»‹p pulse.

            phase = (now - self.cycle_t0) % self.cycle_period

            on_window = duty * self.cycle_period

            if phase < on_window:

                target = self.pos_cmd if error > 0 else self.neg_cmd

            else:

                target = self.stop_cmd



        # Chá»‰ gá»­i khi command thá»±c sá»± Ä‘á»•i (giáº£m táº£i serial + Arduino).

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

    """Chá»‰ gá»­i serial khi tráº¡ng thĂ¡i laser tháº­t sá»± Ä‘á»•i."""

    global laser_on

    if on and not laser_on:

        send("L")

        laser_on = True

    elif (not on) and laser_on:

        send("K")

        laser_on = False





# Trá»¥c ngang (pan): dx > 0 -> Ä‘á»‘i tÆ°á»£ng á»Ÿ bĂªn pháº£i -> camera quay pháº£i ('d')

axis_x = AxisController(

    pos_cmd="d", neg_cmd="a", stop_cmd="h",

    deadzone=DEADZONE_X, max_error=MAX_ERROR_X,

    min_duty=MIN_DUTY_X

)

# Trá»¥c dá»c (tilt): dy > 0 -> Ä‘á»‘i tÆ°á»£ng á»Ÿ phĂ­a dÆ°á»›i -> camera cĂºi xuá»‘ng ('s')

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



            # ===== ERROR THEO TĂ‚M BOX vs TĂ‚M FRAME =====

            # Laser gáº¯n cá»‘ Ä‘á»‹nh á»Ÿ tĂ¢m frame -> pháº£i kĂ©o tĂ¢m con chuá»™t vá» Ä‘Ă³

            # thĂ¬ laser má»›i chiáº¿u giá»¯a con chuá»™t.

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



        # ===== Äiá»u khiá»ƒn motor: PWM pháº§n má»m theo sai sá»‘ =====

        # Khi máº¥t target -> force_stop=True -> motor dá»«ng ngay.

        axis_x.update(dx, send, force_stop=not target_found)

        axis_y.update(dy, send, force_stop=not target_found)



        # ===== Laser: báº­t khi tĂ¢m con chuá»™t Ä‘Ă£ vĂ o deadzone =====

        in_target = target_found and center_in_deadzone

        set_laser(in_target)



        # ===== Váº½ vĂ¹ng deadzone (xanh = tĂ¢m chuá»™t trong vĂ¹ng, tráº¯ng = chÆ°a) =====

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



        # Chá»‰ bĂ¡o tráº¡ng thĂ¡i laser

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