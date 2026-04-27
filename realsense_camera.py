"""
RealSense camera wrapper: dong thoi lay RGB + depth da align.
Yeu cau: pip install pyrealsense2  (xem README cho cach cai tren Pi5)
"""
import threading
import time
import numpy as np

try:
    import pyrealsense2 as rs
    _RS_OK = True
except ImportError as _e:
    _RS_OK = False
    _IMPORT_ERR = _e


class RealSenseCamera:
    def __init__(self, width=640, height=480, fps=30):
        if not _RS_OK:
            raise RuntimeError(
                f"Chua cai pyrealsense2 ({_IMPORT_ERR}).\n"
                f"Cai bang: pip install pyrealsense2\n"
                f"Neu pip fail tren Pi5 Python 3.13, build tu source (xem README)."
            )

        self.pipeline = rs.pipeline()
        cfg = rs.config()
        cfg.enable_stream(rs.stream.color, width, height, rs.format.bgr8, fps)
        cfg.enable_stream(rs.stream.depth, width, height, rs.format.z16, fps)

        self.profile = self.pipeline.start(cfg)

        # Align depth -> color: depth pixel (x,y) trung khop voi color pixel (x,y)
        self.align = rs.align(rs.stream.color)

        # Lay depth scale (D435 ~0.001 = mm -> m)
        depth_sensor = self.profile.get_device().first_depth_sensor()
        self.depth_scale = depth_sensor.get_depth_scale()
        print(f"[RealSense] Depth scale = {self.depth_scale:.4f} (m/unit)")

        # Buffer dung chung
        self._lock = threading.Lock()
        self._color = None
        self._depth = None
        self._depth_frame = None  # giu lai object rs.depth_frame de dung get_distance()
        self._running = True

        self._thread = threading.Thread(target=self._update, daemon=True)
        self._thread.start()
        time.sleep(0.5)

    def _update(self):
        while self._running:
            try:
                frames = self.pipeline.wait_for_frames(timeout_ms=1000)
                aligned = self.align.process(frames)
                color = aligned.get_color_frame()
                depth = aligned.get_depth_frame()
                if not color or not depth:
                    continue
                with self._lock:
                    self._color = np.asanyarray(color.get_data())
                    self._depth = np.asanyarray(depth.get_data())  # uint16
                    self._depth_frame = depth
            except Exception as e:
                print(f"[RealSense] frame error: {e}")
                time.sleep(0.05)

    def read(self):
        with self._lock:
            if self._color is None:
                return False, None
            return True, self._color.copy()

    def get_distance_at(self, x, y):
        """Tra ve khoang cach (met) tai pixel (x,y). 0.0 neu khong do duoc."""
        with self._lock:
            df = self._depth_frame
        if df is None:
            return 0.0
        try:
            return float(df.get_distance(int(x), int(y)))
        except Exception:
            return 0.0

    def get_distance_in_box(self, x1, y1, x2, y2):
        """Tra ve khoang cach trung binh trong box (loc bo cac diem 0/loi). Met."""
        with self._lock:
            d = self._depth
        if d is None:
            return 0.0
        x1 = max(0, x1); y1 = max(0, y1)
        x2 = min(d.shape[1], x2); y2 = min(d.shape[0], y2)
        roi = d[y1:y2, x1:x2]
        if roi.size == 0:
            return 0.0
        # Loai diem 0 (khong co data) va outlier
        valid = roi[roi > 0]
        if valid.size == 0:
            return 0.0
        median = float(np.median(valid)) * self.depth_scale  # ra met
        return median

    def release(self):
        self._running = False
        time.sleep(0.1)
        try:
            self.pipeline.stop()
        except Exception:
            pass
