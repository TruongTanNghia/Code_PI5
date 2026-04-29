# Arduino Motor Test (Direct, KHÔNG dùng PC817)

## Phần cứng

- **Arduino Uno R3** (5V logic — đủ điện áp cho driver opto input)
- **2× Driver MD5-HD14** (Autonics)
- **2× Stepper Autonics A16K-M569** (5-phase, 0.72°/step)
- **Nguồn DC 24V ≥2A** cho driver
- *(Đã bỏ PC817 — Arduino nối thẳng vào driver)*

## Sơ đồ đấu nối

### Arduino → Driver (tín hiệu xung)

| Arduino Pin | Đến |
|---|---|
| **D2** | Driver 1 — `CW−` |
| **D3** | Driver 1 — `CCW−` |
| **D4** | Driver 2 — `CW−` |
| **D5** | Driver 2 — `CCW−` |
| **5V** | `CW+` và `CCW+` của **CẢ HAI** driver |
| **GND** | GND của cả hai driver (chân `−` của terminal `20-35V`) |

### Driver → Nguồn 24V và Motor

| Driver | Nối |
|---|---|
| `+24V` (terminal `20-35V +`) | Cực `+` của adapter 24V |
| `GND` (terminal `20-35V −`) | Cực `−` của adapter 24V |
| `BLUE/RED/ORANGE/GREEN/BLACK` | 5 dây màu của motor (đúng thứ tự) |

### DIP switch trên driver
- `TEST` = OFF
- `1/2 CLK` = OFF (chế độ 2-pulse: CW + CCW riêng)
- `C/D` = OFF

## Logic tín hiệu (QUAN TRỌNG!)

Khác với cách nối qua PC817, lần này Arduino **kéo CW- xuống GND** để tạo xung:

| Trạng thái | Arduino pin | CW- | Driver thấy |
|---|---|---|---|
| Idle | HIGH (5V) | 5V | Không có dòng → KHÔNG step |
| Pulse active | LOW (0V) | 0V | Dòng từ 5V → CW+ → LED → CW- → GND → STEP |

→ **Logic ACTIVE LOW**. Code đã xử lý sẵn trong file `motor_test.ino`.

## Cách dùng

1. Mở Arduino IDE
2. Mở file `motor_test/motor_test.ino`
3. Chọn board **Arduino Uno**, cổng COM
4. Upload
5. Mở **Serial Monitor** (baud 9600)
6. Gõ ký tự lệnh:

| Phím | Tác dụng |
|---|---|
| `1` | Quay D2 (motor 1 thuận) |
| `2` | Quay D3 (motor 1 ngược) |
| `3` | Quay D4 (motor 2 thuận) |
| `4` | Quay D5 (motor 2 ngược) |
| `s` | Dừng |
| `v` | Rất chậm (5 step/s) |
| `l` | Chậm (50 step/s) |
| `m` | Vừa (200 step/s — mặc định) |
| `f` | Nhanh (1000 step/s) |

## Quy trình test

1. Upload code, mở Serial Monitor
2. Gõ `m` (set tốc độ vừa)
3. Gõ `1` → motor 1 phải bắt đầu quay theo CW
4. Gõ `s` → dừng
5. Gõ `2` → motor 1 quay ngược (CCW)
6. Tương tự với `3`, `4` cho motor 2

## Điều khiển từ Pi5 qua UART

Sau khi upload xong, có thể điều khiển Arduino từ Pi5 bằng `arduino_motor.py` trong thư mục gốc của project. Đấu UART:
- Pi GPIO14 (TX) → Arduino D0 (RX)
- Arduino D1 (TX) → 1KΩ → Pi GPIO15 (RX) → 2KΩ → GND (voltage divider 5V→3.3V)
- Pi GND → Arduino GND
