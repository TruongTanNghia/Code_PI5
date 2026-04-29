# Arduino Motor Test

## Phần cứng

- **Arduino Uno** (5V logic - giải quyết vấn đề Pi 3.3V không đủ dòng)
- **PC817 4-channel module** (cách ly tín hiệu)
- **2× Driver MD5-HD14** (Autonics)
- **2× Stepper Autonics A16K-M569** (5-phase, 0.72°/step)
- **Nguồn DC 24V ≥2A** cho driver

## Sơ đồ đấu nối

### Arduino → PC817 (input side)

| Arduino Pin | PC817 |
|---|---|
| Pin 2 | IN1 |
| Pin 3 | IN2 |
| Pin 4 | IN3 |
| Pin 5 | IN4 |
| 5V | Vcc (input side) |
| GND | G (input side) |

### PC817 → Driver (output side)

| PC817 OUT | Driver MD5-HD14 |
|---|---|
| U1 | Driver 1 — CW− |
| U2 | Driver 1 — CCW− |
| U3 | Driver 2 — CW− |
| U4 | Driver 2 — CCW− |
| G (output side) | GND của driver (chân `−` của 20-35V) |

### Driver → Motor + Nguồn

| Driver | Nối |
|---|---|
| CW+, CCW+ | +24V (chung với + của 20-35V) |
| 20-35V `+`/`−` | Nguồn DC 24V |
| BLUE/RED/ORANGE/GREEN/BLACK | 5 dây màu của motor |

### DIP switch trên driver
- **TEST = OFF** (không tự test)
- **1/2 CLK = OFF** (chế độ 2-pulse: CW + CCW riêng)
- **C/D = OFF** (chiều mặc định)

## Cách dùng

1. Mở Arduino IDE
2. Mở file `motor_test/motor_test.ino`
3. Chọn board **Arduino Uno**, cổng COM
4. Upload
5. Mở **Serial Monitor** (Tools → Serial Monitor) — đặt baud **9600**
6. Gõ ký tự lệnh:

| Phím | Tác dụng |
|---|---|
| `1` | Quay channel U1 (motor 1 thuận) |
| `2` | Quay channel U2 (motor 1 ngược) |
| `3` | Quay channel U3 (motor 2 thuận) |
| `4` | Quay channel U4 (motor 2 ngược) |
| `s` | Dừng |
| `v` | Rất chậm (5 step/s) |
| `l` | Chậm (50 step/s) |
| `m` | Vừa (200 step/s — mặc định) |
| `f` | Nhanh (1000 step/s) |

## Quy trình test

1. Upload code, mở Serial Monitor
2. Gõ `m` (set tốc độ vừa)
3. Gõ `1` → motor 1 phải bắt đầu quay
4. Gõ `s` → dừng
5. Gõ `2` → motor 1 quay ngược
6. Tương tự với `3`, `4` cho motor 2
