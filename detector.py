# import torch
# import torch.nn as nn
# from ultralytics import YOLO
# from ultralytics.nn.tasks import DetectionModel

# # ?? M? KH�A CHECKPOINT YOLOv8 (torch >= 2.6)
# torch.serialization.add_safe_globals([
#     DetectionModel,
#     nn.Sequential,
#     nn.Conv2d,
#     nn.BatchNorm2d,
#     nn.SiLU,
# ])

# class MouseDetector:
#     def __init__(self):
#         self.model = YOLO("./best.pt")

#     def detect(self, frame):
#         results = self.model.predict(
#             frame,
#             imgsz=320,
#             conf=0.4,
#             device="cpu",
#             max_det=1,
#             verbose=False
#         )

#         if not results or results[0].boxes is None:
#             return None

#         boxes = results[0].boxes
#         if len(boxes) == 0:
#             return None

#         box = boxes[0]
#         x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
#         cx = (x1 + x2) // 2
#         cy = (y1 + y2) // 2

#         return cx, cy, (x1, y1, x2, y2)

 
import torch
import torch.nn as nn
from ultralytics import YOLO
from ultralytics.nn.tasks import DetectionModel

# ?? M? KH?A CHECKPOINT YOLOv8 (torch >= 2.6)
torch.serialization.add_safe_globals([
    DetectionModel,
    nn.Sequential,
    nn.Conv2d,
    nn.BatchNorm2d,
    nn.SiLU,
])

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
            verbose=False
        )

        detections = []
        if not results or results[0].boxes is None:
            return detections

        for box in results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            detections.append({
                'center': (cx, cy),
                'box': (x1, y1, x2, y2),
                'conf': float(box.conf[0])
            })

        return detections
 
