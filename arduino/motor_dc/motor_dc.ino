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
 * ====== GIAO THUC LENH (tu Python) ======
 *  Dieu khien co TOC DO (moi truc):
 *    "P<so>\n"  -> dat toc do PAN.  so > 0 quay phai, < 0 quay trai, = 0 dung.
 *                  |so| = step/s (vd P2000 = pan phai 2000 step/s, P-800 = trai)
 *    "T<so>\n"  -> dat toc do TILT. so > 0 xuong, < 0 len, = 0 dung.
 *
 *  Laser / khac:
 *    'L' = bat laser     'K' = tat laser
 *    'x' = dung het + tat laser
 *
 *  (Van giu tuong thich lenh cu a/d/h/w/s/v neu can, xem cuoi file)
 *
 * Stepper chay lien tuc & MUOT theo toc do nhan duoc, tu dung khi cham limit.
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
#define LIM_TILT_NEG  A2   // tren
#define LIM_TILT_POS  A3   // duoi

// ===== GIOI HAN TOC DO =====
// step/s toi da cho phep (chong dat toc do qua cao gay mat buoc).
// Neu stepper manh + nguon cao co the tang. Neu mat buoc thi giam.
const long MAX_SPS = 4000;
const long MIN_SPS = 150;   // duoi nguong nay coi nhu dung (tranh buoc qua cham)

// Toc do hien tai (step/s, co dau). 0 = dung.
long pan_sps  = 0;
long tilt_sps = 0;

// Trang thai xung
unsigned long pan_last_us  = 0;
unsigned long tilt_last_us = 0;
bool pan_pin_state  = false;
bool tilt_pin_state = false;

// Doc so nguyen (co the am) tu serial cho lenh P/T
long readLong() {
  return Serial.parseInt();  // doc so, tu xu ly dau '-'
}

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

void loop() {
  // ===== Doc lenh tu Python =====
  while (Serial.available()) {
    char c = Serial.peek();

    if (c == 'P') {
      Serial.read();              // bo 'P'
      long v = readLong();        // doc toc do (co dau)
      pan_sps = constrain(v, -MAX_SPS, MAX_SPS);
      if (pan_sps > 0) digitalWrite(PAN_DIR, HIGH);
      else if (pan_sps < 0) digitalWrite(PAN_DIR, LOW);
    }
    else if (c == 'T') {
      Serial.read();              // bo 'T'
      long v = readLong();
      tilt_sps = constrain(v, -MAX_SPS, MAX_SPS);
      if (tilt_sps > 0) digitalWrite(TILT_DIR, HIGH);
      else if (tilt_sps < 0) digitalWrite(TILT_DIR, LOW);
    }
    else if (c == 'L') { Serial.read(); digitalWrite(LASER, HIGH); }
    else if (c == 'K') { Serial.read(); digitalWrite(LASER, LOW); }
    else if (c == 'x') {
      Serial.read();
      pan_sps = 0; tilt_sps = 0;
      digitalWrite(LASER, LOW);
    }
    else {
      Serial.read();  // bo ky tu rac (xuong dong, khoang trang...)
    }
  }

  unsigned long now = micros();

  // ===== PAN: phat xung theo toc do, dung khi cham limit huong do =====
  long pan_abs = labs(pan_sps);
  bool pan_blocked = (pan_sps < 0 && digitalRead(LIM_PAN_NEG) == LOW) ||
                     (pan_sps > 0 && digitalRead(LIM_PAN_POS) == LOW);
  if (pan_abs >= MIN_SPS && !pan_blocked) {
    // half-period (us) = 1e6 / (2 * step/s)
    unsigned long half_us = 1000000UL / (2UL * pan_abs);
    if (now - pan_last_us >= half_us) {
      pan_pin_state = !pan_pin_state;
      digitalWrite(PAN_STEP, pan_pin_state);
      pan_last_us = now;
    }
  }

  // ===== TILT: tuong tu =====
  long tilt_abs = labs(tilt_sps);
  bool tilt_blocked = (tilt_sps < 0 && digitalRead(LIM_TILT_NEG) == LOW) ||
                      (tilt_sps > 0 && digitalRead(LIM_TILT_POS) == LOW);
  if (tilt_abs >= MIN_SPS && !tilt_blocked) {
    unsigned long half_us = 1000000UL / (2UL * tilt_abs);
    if (now - tilt_last_us >= half_us) {
      tilt_pin_state = !tilt_pin_state;
      digitalWrite(TILT_STEP, tilt_pin_state);
      tilt_last_us = now;
    }
  }
}
