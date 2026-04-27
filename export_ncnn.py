"""
Convert .pt -> NCNN (chay 1 lan duy nhat tren Pi5).
NCNN nhanh hon PyTorch CPU 3-5 lan, dung cho ARM (Pi5/Pi4).

Cach dung:
    python export_ncnn.py

Sau khi xong se tao thu muc results-mouse/best_ncnn_model/
Code se tu dong dung no neu MODEL_PATH trong config.py tro toi.
"""
import torch

_orig_torch_load = torch.load
def _patched_load(*args, **kwargs):
    kwargs["weights_only"] = False
    return _orig_torch_load(*args, **kwargs)
torch.load = _patched_load

from ultralytics import YOLO

SRC = "./results-mouse/best.pt"

print(f"Loading {SRC}...")
model = YOLO(SRC)

print("Exporting to NCNN (co the mat 1-3 phut tren Pi5)...")
model.export(format="ncnn", imgsz=320)

print("\n[OK] Da convert xong.")
print("Model NCNN nam o: ./results-mouse/best_ncnn_model/")
print("Bay gio chay lai: python detect_only.py")
