import torch

# Patch torch.load: PyTorch 2.6+ doi default weights_only=True khien YOLO khong load duoc.
# Day la model do chinh anh train nen tin tuong, set weights_only=False.
_orig_torch_load = torch.load
def _patched_load(*args, **kwargs):
    kwargs["weights_only"] = False
    return _orig_torch_load(*args, **kwargs)
torch.load = _patched_load

from ultralytics import YOLO


class MouseDetector:
    def __init__(self, model_path="./results-mouse/best.pt"):
        self.model = YOLO(model_path)

    def detect(self, frame):
        results = self.model.predict(
            frame,
            imgsz=320,
            conf=0.35,
            device="cpu",
            max_det=10,
            verbose=False,
        )

        detections = []
        if not results or results[0].boxes is None:
            return detections

        for box in results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            detections.append({
                "center": (cx, cy),
                "box": (x1, y1, x2, y2),
                "conf": float(box.conf[0]),
            })

        return detections
