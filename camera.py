import cv2
import threading
import time
from config import *

class Camera:
    def __init__(self):
        self.cap = cv2.VideoCapture(CAMERA_ID, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not self.cap.isOpened():
            raise RuntimeError("Kh�ng m? du?c camera")

        self.running = True
        self.ret = False
        self.frame = None

        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def _update(self):
        """�?c camera LI�N T?C, kh�ng sleep"""
        while self.running:
            ret, frame = self.cap.read()
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
        self.cap.release()
