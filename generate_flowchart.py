# -*- coding: utf-8 -*-
"""
Ve LUU DO THUAT TOAN (ban GON, DE HIEU) cua he thong turret bam + ban laser.
Chay:  py generate_flowchart.py
Ket qua: SODO_THUAT_TOAN.png
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon

plt.rcParams["font.family"] = "DejaVu Sans"   # ho tro tieng Viet co dau

# Mau
C_START = "#455A64"   # xam (bat dau / ket thuc)
C_PROC = "#1565C0"    # xanh duong (buoc xu ly)
C_DEC = "#EF6C00"     # cam (cau hoi re nhanh)
C_TRACK = "#2E7D32"   # xanh la (bam theo)
C_SCAN = "#F9A825"    # vang (quet tim)
C_WAIT = "#78909C"    # xam nhat (cho)
C_FIRE = "#C62828"    # do (ban laser)
RET = "#9E9E9E"       # mui ten quay lai vong lap

fig, ax = plt.subplots(figsize=(11, 15))
ax.set_xlim(0, 100)
ax.set_ylim(34, 200)
ax.axis("off")


def box(x, y, w, h, text, color, fs=11, tc="white", shape="round"):
    if shape == "diamond":
        pts = [(x, y + h / 2), (x + w / 2, y), (x, y - h / 2), (x - w / 2, y)]
        ax.add_patch(Polygon(pts, closed=True, lw=1.5,
                             edgecolor="black", facecolor=color, zorder=2))
    else:
        ax.add_patch(FancyBboxPatch(
            (x - w / 2, y - h / 2), w, h,
            boxstyle="round,pad=0.3,rounding_size=1.5",
            lw=1.6, edgecolor="black", facecolor=color, zorder=2))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs,
            color=tc, weight="bold", zorder=3)


def arrow(x1, y1, x2, y2, color="black", rad=0.0, lw=1.8):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=20,
        lw=lw, color=color, connectionstyle=f"arc3,rad={rad}", zorder=1))


def label(x, y, t, color="black"):
    ax.text(x, y, t, ha="center", va="center", fontsize=10, color=color,
            weight="bold", zorder=4,
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=color, lw=1))


# ===== TIEU DE =====
ax.text(50, 197, "LƯU ĐỒ THUẬT TOÁN",
        ha="center", fontsize=18, weight="bold", color="#1A237E")
ax.text(50, 193.5, "Camera tự bám con chuột và bắn laser",
        ha="center", fontsize=12, color="#37474F")

# ===== TRUC CHINH (x = 38) =====
box(38, 189, 48, 6, "BẮT ĐẦU\nMở camera • Arduino • nạp YOLO", C_START, 11)
box(38, 180, 42, 5.5, "Đọc 1 hình từ camera", C_PROC, 11)
box(38, 171, 42, 5.5, "YOLO tìm con chuột trong hình", C_PROC, 11)
box(38, 159, 30, 11, "Có thấy\ncon chuột?", C_DEC, 11, shape="diamond")
box(38, 147, 46, 6.5, "Tính độ lệch dx, dy\n(chuột cách tâm ngắm bao xa)", C_PROC, 10)
box(38, 134, 30, 11, "Chuột đã vào\nô ngắm giữa?", C_DEC, 10, shape="diamond")
box(38, 120, 32, 11, "Động cơ đã dừng\nhẳn ≥ 0.4 giây?", C_DEC, 10, shape="diamond")
box(38, 107, 44, 7, "BẮN LASER 3.5 giây", C_FIRE, 12)

# ===== NHANH BEN PHAI (x = 74) =====
box(74, 159, 34, 11, "QUÉT TUẦN TRA\nxoay trái ↔ phải tìm chuột\nchạm CÔNG TẮC HÀNH TRÌNH\n→ đảo chiều", C_SCAN, 9, tc="#212121")
box(74, 134, 33, 9, "XOAY ĐỘNG CƠ\npan/tilt bám\ntheo con chuột", C_TRACK, 10)
box(74, 120, 30, 7, "Chờ động cơ\ndừng ổn định", C_WAIT, 10)

# ===== MUI TEN TRUC CHINH =====
arrow(38, 186, 38, 183)
arrow(38, 177.2, 38, 174)
arrow(38, 168, 38, 165)
arrow(38, 153.5, 38, 150.5); label(34, 152, "CÓ", C_TRACK)
arrow(38, 143.5, 38, 139.5)
arrow(38, 128.5, 38, 125.7); label(34, 127, "RỒI", C_FIRE)
arrow(38, 114.5, 38, 110.7); label(34, 112.5, "RỒI", C_FIRE)

# ===== MUI TEN RE NHANH (phai) =====
arrow(53, 159, 57.5, 159); label(55.5, 162.5, "KHÔNG", "#888")
arrow(53, 134, 57.5, 134); label(55, 137.5, "CHƯA", "#888")
arrow(54, 120, 59, 120); label(56.5, 123.5, "CHƯA", "#888")

# ===== DUONG QUAY LAI VONG LAP (riser ben phai x = 93) =====
# 3 nhanh phai gop vao riser
arrow(90.5, 159, 93, 159, RET)
arrow(90.5, 134, 93, 134, RET)
arrow(89, 120, 93, 120, RET)
# laser xong cung quay lai
arrow(38, 103.5, 38, 100); arrow(38, 100, 93, 100, RET)
# riser di len
ax.plot([93, 93], [100, 185], color=RET, lw=2.2, zorder=1)
ax.plot([38, 93], [185, 185], color=RET, lw=2.2, zorder=1)
arrow(38, 185, 38, 182.8, RET)
label(65, 185, "Lặp lại vòng lặp", RET)

# ===== GHI CHU =====
ax.text(50, 92, "Nhấn ESC để thoát chương trình",
        ha="center", fontsize=10, style="italic", color="#616161")

# ===== CHU THICH MAU =====
leg = [(C_PROC, "Bước xử lý"), (C_DEC, "Câu hỏi rẽ nhánh"),
       (C_TRACK, "Bám theo chuột"), (C_SCAN, "Quét tìm chuột"),
       (C_FIRE, "Bắn laser")]
for i, (c, t) in enumerate(leg):
    yy = 189 - i * 3
    ax.add_patch(FancyBboxPatch((6, yy - 1), 3, 2,
                 boxstyle="round,pad=0.1", fc=c, ec="black", lw=1, zorder=5))
    ax.text(10, yy, t, ha="left", va="center", fontsize=9, color="#263238", zorder=5)

# ===== KHOI CHI TIET: TUAN TRA DUNG CONG TAC HANH TRINH =====
ax.plot([3, 97], [82, 82], color="#BDBDBD", lw=1.2, ls="--")
ax.text(50, 77, "CHI TIẾT CHẾ ĐỘ TUẦN TRA (dùng CÔNG TẮC HÀNH TRÌNH)",
        ha="center", fontsize=12.5, weight="bold", color="#E65100")

# 3 khoi: Quay 1 huong -> Cham cong tac? -> CO: dao chieu
box(16, 62, 22, 9, "Quay 1 hướng\n(trái / phải)", C_SCAN, 9.5, tc="#212121")
box(50, 62, 28, 13, "Chạm CÔNG TẮC\nHÀNH TRÌNH?", C_DEC, 10, shape="diamond")
box(85, 62, 24, 10, "ĐẢO CHIỀU\nquay ngược\nlại", C_SCAN, 9.5, tc="#212121")

arrow(27.5, 62, 35.5, 62)                       # Quay -> Cham?
arrow(64, 62, 72.5, 62); label(68, 66, "CÓ", C_FIRE)   # Cham? -> Dao chieu

# KHONG: chua cham -> quay tiep (vong xuong duoi ve lai "Quay 1 huong")
ax.plot([50, 50, 16, 16], [55.5, 50, 50, 57.5], color="#888", lw=1.8, zorder=1)
arrow(16, 51, 16, 57.5, "#888")
label(33, 50, "KHÔNG: quay tiếp", "#888")

# Dao chieu xong -> quet tiep huong nguoc (vong ve "Quay 1 huong")
ax.plot([85, 85, 16, 16], [67, 72, 72, 66.5], color=C_SCAN, lw=1.8, zorder=1)
arrow(16, 68, 16, 66.5, C_SCAN)
label(50, 72, "đảo xong → quét tiếp hướng ngược lại", C_SCAN)

plt.tight_layout()
out = "SODO_THUAT_TOAN.png"
plt.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
print(f"[OK] Da luu {out}")
