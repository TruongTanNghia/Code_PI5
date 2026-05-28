import cv2
import numpy as np
import torch
from ultralytics import YOLO

from config import DET_CONF

# ===== FIX PyTorch 2.6+ weights_only =====
# PyTorch 2.6 đổi mặc định weights_only=True -> không load được model YOLO.
# Cho phép các class của ultralytics vào allowlist để torch.load chạy được.
try:
    from ultralytics.nn.tasks import (
        SegmentationModel, DetectionModel, PoseModel, ClassificationModel,
    )
    torch.serialization.add_safe_globals([
        SegmentationModel, DetectionModel, PoseModel, ClassificationModel,
    ])
except Exception as e:
    print("[WARN] khong them duoc safe_globals:", e)


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

    def __init__(self, model_path="best_seg_ncnn_model", conf=DET_CONF, imgsz=320):
        # model_path:
        #   - "best_seg_ncnn_model"  -> NCNN (NHANH NHAT tren Pi, export truoc)
        #   - "best_seg.onnx"        -> ONNX (nhanh vua)
        #   - "best_seg.pt"          -> PyTorch goc (CHAM nhat tren Pi)
        # imgsz: kich thuoc input. 320 nhanh gap ~4 lan so voi 640, do chinh xac giam chut.
        #   Thu 320 truoc, neu detect kem thi tang len 416 hoac 512.
        self.model = YOLO(model_path)
        self.conf = conf
        self.imgsz = imgsz

    def detect(self, frame):
        # verbose=False để khỏi spam log mỗi frame
        results = self.model(frame, conf=self.conf, imgsz=self.imgsz, verbose=False)
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