/*
 * 2 STEPPER closed-loop HBS57 (STEP/DIR) + 4 limit switch + laser
 *
 * ====== DAU DAY ======
 *  PAN  (ngang): STEP=D2, DIR=D3   -> HBS57 #1 (PUL-, DIR-)
 *  TILT (doc)  : STEP=D5, DIR=D6   -> HBS57 #2 (PUL-, DIR-)
 *  PUL+/DIR+ cua ca 2 driver -> 5V Arduino
 *  ENA: de trong
 *
 *  LASER = D7
 *
 *  LIMIT SWITCH (dung INPUT_PULLUP, cong tac noi GND):
 *    Ngang trai  = A0
 *    Ngang phai  = A1
 *    Doc tren    = A2
 *    Doc duoi    = A3
 *
 * ====== GIAO THUC LENH (tu Python, giu giong code cu) ======
 *  'a' = PAN quay trai (-)      'd' = PAN quay phai (+)    'h' = dung PAN
 *  'w' = TILT quay len (-)      's' = TILT quay xuong (+)  'v' = dung TILT
 *  'L' = bat laser              'K' = tat laser
 *  'x' = dung het + tat laser
 *
 * Stepper chay lien tuc theo huong nhan duoc, dung khi nhan lenh stop
 * hoac khi cham limit switch o huong do.
 */

// ===== CHAN STEP/DIR =====
#define PAN_STEP   2
#define PAN_DIR    3
#define TILT_STEP  5
#define TILT_DIR   6

#define LASER      7

// ===== CHAN LIMIT SWITCH =====
#define LIM_PAN_NEG   A0   // trai
#define LIM_PAN_POS   A1   // phai
#define LIM_TILT_NEG  A2   // tren (w)
#define LIM_TILT_POS  A3   // duoi (s)

// ===== TOC DO STEPPER =====
// Nua chu ky xung, microseconds. NHO hon = NHANH hon.
// 150us -> ~3300 step/s (nhanh, bam kip chuot).
// Neu stepper rung/keu/mat buoc (khong quay) -> TANG len 200, 300, 500...
// Closed-loop HBS57 chiu toc do cao tot, nhung con tuy tai + nguon.
unsigned int STEP_HALF_US = 150;

// Trang thai chay: 0 = dung, 1 = chieu duong (d/s), -1 = chieu am (a/w)
int pan_dir  = 0;
int tilt_dir = 0;

// Thoi diem step cuoi (de tao xung khong-blocking)
unsigned long pan_last_us  = 0;
unsigned long tilt_last_us = 0;
bool pan_pin_state  = false;
bool tilt_pin_state = false;

void setup() {
  Serial.begin(9600);

  pinMode(PAN_STEP, OUTPUT);
  pinMode(PAN_DIR, OUTPUT);
  pinMode(TILT_STEP, OUTPUT);
  pinMode(TILT_DIR, OUTPUT);
  pinMode(LASER, OUTPUT);

  pinMode(LIM_PAN_NEG, INPUT_PULLUP);
  pinMode(LIM_PAN_POS, INPUT_PULLUP);
  pinMode(LIM_TILT_NEG, INPUT_PULLUP);
  pinMode(LIM_TILT_POS, INPUT_PULLUP);

  digitalWrite(PAN_STEP, LOW);
  digitalWrite(TILT_STEP, LOW);
  digitalWrite(LASER, LOW);   // neu laser active LOW thi doi thanh HIGH
}

// Limit nhan (cham) khi doc LOW (vi INPUT_PULLUP + cong tac noi GND)
bool panNegHit()  { return digitalRead(LIM_PAN_NEG)  == LOW; }
bool panPosHit()  { return digitalRead(LIM_PAN_POS)  == LOW; }
bool tiltNegHit() { return digitalRead(LIM_TILT_NEG) == LOW; }
bool tiltPosHit() { return digitalRead(LIM_TILT_POS) == LOW; }

void loop() {
  // ===== Doc lenh tu Python =====
  while (Serial.available()) {
    char c = Serial.read();

    if (c == 'a') { digitalWrite(PAN_DIR, LOW);  pan_dir = -1; }   // trai
    else if (c == 'd') { digitalWrite(PAN_DIR, HIGH); pan_dir = +1; }  // phai
    else if (c == 'h') { pan_dir = 0; }                                // dung pan

    else if (c == 'w') { digitalWrite(TILT_DIR, LOW);  tilt_dir = -1; } // len
    else if (c == 's') { digitalWrite(TILT_DIR, HIGH); tilt_dir = +1; } // xuong
    else if (c == 'v') { tilt_dir = 0; }                                // dung tilt

    else if (c == 'L') digitalWrite(LASER, HIGH);  // bat laser
    else if (c == 'K') digitalWrite(LASER, LOW);   // tat laser

    else if (c == 'x') {
      pan_dir = 0;
      tilt_dir = 0;
      digitalWrite(LASER, LOW);
    }
  }

  unsigned long now = micros();

  // ===== PAN: phat xung neu dang chay va chua cham limit huong do =====
  bool pan_blocked = (pan_dir < 0 && panNegHit()) ||
                     (pan_dir > 0 && panPosHit());
  if (pan_dir != 0 && !pan_blocked) {
    if (now - pan_last_us >= STEP_HALF_US) {
      pan_pin_state = !pan_pin_state;
      digitalWrite(PAN_STEP, pan_pin_state);
      pan_last_us = now;
    }
  }

  // ===== TILT: tuong tu =====
  bool tilt_blocked = (tilt_dir < 0 && tiltNegHit()) ||
                      (tilt_dir > 0 && tiltPosHit());
  if (tilt_dir != 0 && !tilt_blocked) {
    if (now - tilt_last_us >= STEP_HALF_US) {
      tilt_pin_state = !tilt_pin_state;
      digitalWrite(TILT_STEP, tilt_pin_state);
      tilt_last_us = now;
    }
  }
}
