import cv2
import numpy as np
from ultralytics import YOLO

from config import DET_CONF


class MouseDetector:
    """
    Detector dùng YOLOv11-seg (best_seg.pt).
    Trả về list dict, mỗi dict gồm:
        - box:    (x1, y1, x2, y2)  toạ độ int
        - center: (cx, cy)          tâm tính theo MASK (chính xác hơn box)
        - conf:   float
        - mask:   np.ndarray bool (HxW) hoặc None nếu model không có mask
    Tương thích ngược với main.py cũ (vẫn có box/center/conf).
    """

    def __init__(self, model_path="best_seg.pt", conf=DET_CONF):
        self.model = YOLO(model_path)
        self.conf = conf

    def detect(self, frame):
        # verbose=False để khỏi spam log mỗi frame
        results = self.model(frame, conf=self.conf, verbose=False)
        dets = []

        if not results:
            return dets

        r = results[0]
        if r.boxes is None or len(r.boxes) == 0:
            return dets

        h, w = frame.shape[:2]

        # Lấy mask nếu có (seg model). r.masks.data: (N, mh, mw) tensor 0..1
        masks = None
        if r.masks is not None:
            masks = r.masks.data.cpu().numpy()  # (N, mh, mw)

        boxes = r.boxes.xyxy.cpu().numpy()       # (N, 4)
        confs = r.boxes.conf.cpu().numpy()       # (N,)

        for i in range(len(boxes)):
            x1, y1, x2, y2 = boxes[i]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            conf = float(confs[i])

            mask_bool = None
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2  # fallback: tâm box

            if masks is not None and i < len(masks):
                m = masks[i]
                # Mask của YOLO thường ở kích thước khác frame -> resize về frame
                if m.shape[:2] != (h, w):
                    m = cv2.resize(m, (w, h), interpolation=cv2.INTER_NEAREST)
                mask_bool = m > 0.5

                # Tâm theo centroid của mask (chính giữa thân con chuột)
                ys, xs = np.where(mask_bool)
                if len(xs) > 0:
                    cx = int(xs.mean())
                    cy = int(ys.mean())

            dets.append({
                "box": (x1, y1, x2, y2),
                "center": (cx, cy),
                "conf": conf,
                "mask": mask_bool,
            })

        return dets
