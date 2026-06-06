# -*- coding: utf-8 -*-
"""
RoboflowDetector - goi Roboflow (CLOUD) phat hien doi tuong theo TUNG KHUNG HINH.

Tra ve CUNG dinh dang voi MouseDetector (detector.py) de main.py dung lai duoc:
    list[dict] moi cai gom:
        - box:    (x1, y1, x2, y2)
        - center: (cx, cy)
        - conf:   float
        - mask:   None   (Roboflow detection khong co mask)

!!! LUU Y QUAN TRONG:
 - Day la CLOUD -> moi khung hinh phai gui anh len mang -> co do TRE
   (~200-500ms/khung) -> tracking se CHAM/giat hon model local.
 - Can INTERNET + thu vien: pip install inference-sdk
 - API KEY KHONG hardcode. main.py doc key tu:
     + bien moi truong ROBOFLOW_API_KEY, hoac
     + file roboflow_key.txt (da gitignore)
   roi truyen vao day.
"""


class RoboflowDetector:
    def __init__(self, api_key, workspace, workflow_id,
                 api_url="https://serverless.roboflow.com",
                 image_input="image", conf=0.40, box_scale=1.0):
        # import o trong __init__ de neu chua cai inference-sdk thi main.py
        # van chay duoc (no se bat Exception va dung model local thay the).
        from inference_sdk import InferenceHTTPClient
        self.client = InferenceHTTPClient(api_url=api_url, api_key=api_key)
        self.workspace = workspace
        self.workflow_id = workflow_id
        self.image_input = image_input
        self.conf = conf            # main.py dung de hien thi + loc them
        self.box_scale = box_scale  # thu nho box quanh tam neu can

    def detect(self, frame):
        """Goi Roboflow cho 1 khung hinh, tra ve list detection."""
        try:
            result = self.client.run_workflow(
                workspace_name=self.workspace,
                workflow_id=self.workflow_id,
                images={self.image_input: frame},
                use_cache=True,
            )
        except Exception as e:
            print(f"[ROBOFLOW] loi infer (mang/key/workflow?): {e}")
            return []

        preds = _extract_predictions(result)
        dets = []
        for p in preds:
            try:
                conf = float(p.get("confidence", p.get("conf", 0)))
            except Exception:
                conf = 0.0
            if conf < self.conf:
                continue
            try:
                # Roboflow tra ve: x,y = TAM box; width,height = kich thuoc (pixel)
                cx = float(p["x"]); cy = float(p["y"])
                bw = float(p["width"]) * self.box_scale
                bh = float(p["height"]) * self.box_scale
            except Exception:
                continue
            x1 = int(cx - bw / 2.0); y1 = int(cy - bh / 2.0)
            x2 = int(cx + bw / 2.0); y2 = int(cy + bh / 2.0)
            dets.append({
                "box": (x1, y1, x2, y2),
                "center": (int(cx), int(cy)),
                "conf": conf,
                "mask": None,
            })
        return dets


def _extract_predictions(result):
    """
    Tim tat ca prediction (co du x,y,width,height) trong ket qua workflow,
    du cau truc long nhau the nao (workflow Roboflow tra ve dict/list long nhau).
    """
    found = []

    def walk(o):
        if isinstance(o, dict):
            if all(k in o for k in ("x", "y", "width", "height")):
                found.append(o)
                return
            for v in o.values():
                walk(v)
        elif isinstance(o, (list, tuple)):
            for v in o:
                walk(v)

    walk(result)
    return found
