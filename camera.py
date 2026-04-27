import cv2
import os
import threading
import time
from config import CAMERA_ID, USE_PICAMERA, FRAME_WIDTH, FRAME_HEIGHT

# Bot bot log V4L2 khi auto-detect (nhieu /dev/video* la metadata khong phai capture)
os.environ.setdefault("OPENCV_LOG_LEVEL", "ERROR")


class _USBCamera:
    """Camera USB / V4L2 voi auto-detect index, xac nhan bang frame thuc te."""

    def __init__(self):
        self.cap = None
        tried = []

        if CAMERA_ID >= 0:
            tried.append(CAMERA_ID)
            self.cap = self._try_open(CAMERA_ID)
            if self.cap is not None:
                print(f"[CAMERA] Mo /dev/video{CAMERA_ID} OK")

        # Auto-detect khi CAMERA_ID = -1 hoac mo that bai
        if self.cap is None:
            for idx in range(0, 40):
                if not os.path.exists(f"/dev/video{idx}"):
                    continue
                tried.append(idx)
                cap = self._try_open(idx)
                if cap is not None:
                    print(f"[CAMERA] Auto-detected: /dev/video{idx}")
                    self.cap = cap
                    break

            if self.cap is None:
                raise RuntimeError(
                    f"Khong mo duoc camera USB. Da thu: {tried}. "
                    f"Chay `v4l2-ctl --list-devices` de kiem tra."
                )

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    @staticmethod
    def _try_open(idx):
        """Mo + thu doc 1 frame de xac nhan device thuc su capture duoc."""
        for backend in (cv2.CAP_V4L2, cv2.CAP_ANY):
            cap = cv2.VideoCapture(idx, backend)
            if not cap.isOpened():
                cap.release()
                continue
            # Phai doc duoc frame thuc te (nhieu /dev/video* tren Pi5 la metadata)
            ok, frame = cap.read()
            if ok and frame is not None and frame.size > 0:
                return cap
            cap.release()
        return None

    def read(self):
        return self.cap.read()

    def release(self):
        if self.cap is not None:
            self.cap.release()


class _PiCamera2Wrapper:
    """Pi Camera Module qua libcamera/picamera2 (Pi5)."""

    def __init__(self):
        try:
            from picamera2 import Picamera2
        except ImportError as e:
            raise RuntimeError(
                "Chua cai picamera2. Chay: sudo apt install -y python3-picamera2"
            ) from e

        self.picam2 = Picamera2()
        cfg = self.picam2.create_video_configuration(
            main={"size": (FRAME_WIDTH, FRAME_HEIGHT), "format": "RGB888"}
        )
        self.picam2.configure(cfg)
        self.picam2.start()
        time.sleep(0.5)

    def read(self):
        frame_rgb = self.picam2.capture_array()
        # picamera2 tra ve RGB; OpenCV can BGR
        frame = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        return True, frame

    def release(self):
        try:
            self.picam2.stop()
            self.picam2.close()
        except Exception:
            pass


class Camera:
    def __init__(self):
        if USE_PICAMERA:
            print("[CAMERA] Dung Pi Camera Module (picamera2)")
            self._impl = _PiCamera2Wrapper()
        else:
            print("[CAMERA] Dung USB camera (V4L2)")
            self._impl = _USBCamera()

        self.running = True
        self.ret = False
        self.frame = None

        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def _update(self):
        while self.running:
            ret, frame = self._impl.read()
            if ret:
                self.ret = True
                self.frame = frame
            else:
                self.ret = False

    def read(self):
        if self.frame is None:
            return False, None
        return self.ret, self.frame.copy()

    def release(self):
        self.running = False
        time.sleep(0.1)
        self._impl.release()
