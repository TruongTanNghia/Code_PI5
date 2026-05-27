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
 *  LIMIT SWITCH (chan chung noi GND, dung INPUT_PULLUP):
 *    Ngang trai  = A0      nhan -> doc LOW
 *    Ngang phai  = A1
 *    Doc tren    = A2
 *    Doc duoi    = A3
 *    Moi cong tac: 1 chan -> A0..A3, chan chung -> GND. KHONG can dien tro.
 *
 * ====== GIAO THUC LENH (tu Python) ======
 *  "P<so>\n" -> toc do PAN  (>0 phai, <0 trai, =0 dung), |so|=step/s
 *  "T<so>\n" -> toc do TILT (>0 xuong, <0 len, =0 dung)
 *  'L'=bat laser  'K'=tat laser  'x'=dung het+tat laser
 *  '?'=in trang thai limit 1 lan  '+'=bat auto in  '-'=tat auto in
 */

// ===== CHAN STEP/DIR =====
#define PAN_STEP   2
#define PAN_DIR    3
#define TILT_STEP  5
#define TILT_DIR   6

#define LASER      7

// ===== CHAN LIMIT SWITCH =====
// Da doi cho khop thuc te dau day cua phen:
//   A0 = cong tac LEN   (tilt am)
//   A1 = cong tac XUONG (tilt duong)
//   A2 = cong tac TRAI  (pan am)
//   A3 = cong tac PHAI  (pan duong)
#define LIM_TILT_NEG  A0   // len
#define LIM_TILT_POS  A1   // xuong
#define LIM_PAN_NEG   A2   // trai
#define LIM_PAN_POS   A3   // phai

// ===== GIOI HAN TOC DO =====
const long MAX_SPS = 4000;
const long MIN_SPS = 150;

long pan_sps  = 0;
long tilt_sps = 0;

unsigned long pan_last_us  = 0;
unsigned long tilt_last_us = 0;
bool pan_pin_state  = false;
bool tilt_pin_state = false;

bool auto_report = false;
int prevL0 = -1, prevL1 = -1, prevL2 = -1, prevL3 = -1;

long readLong() {
  return Serial.parseInt();
}

// ===== DOC LIMIT (noi GND + PULLUP): nhan = LOW =====
// Loc nhieu RAT NHE de cong tac nhay (cham phat an lien).
// Doc 2 lan cach nhau 20us, ca 2 LOW moi tinh nhan.
bool limitHit(int pin) {
  if (digitalRead(pin) == HIGH) return false;
  delayMicroseconds(20);
  if (digitalRead(pin) == HIGH) return false;
  return true;
}

// In trang thai 4 cong tac (theo dung chan vat ly A0-A3)
void reportLimits() {
  bool a0 = limitHit(A0);
  bool a1 = limitHit(A1);
  bool a2 = limitHit(A2);
  bool a3 = limitHit(A3);

  Serial.print("A0 LEN: ");    Serial.print(a0 ? "NHAN" : "nha ");
  Serial.print(" | A1 XUONG: "); Serial.print(a1 ? "NHAN" : "nha ");
  Serial.print(" | A2 TRAI: ");  Serial.print(a2 ? "NHAN" : "nha ");
  Serial.print(" | A3 PHAI: ");  Serial.print(a3 ? "NHAN" : "nha ");
  Serial.println();
}

void setup() {
  Serial.begin(9600);

  pinMode(PAN_STEP, OUTPUT);
  pinMode(PAN_DIR, OUTPUT);
  pinMode(TILT_STEP, OUTPUT);
  pinMode(TILT_DIR, OUTPUT);
  pinMode(LASER, OUTPUT);

  // Chan chung noi GND -> dung INPUT_PULLUP (chuan, chong nhieu)
  pinMode(LIM_PAN_NEG, INPUT_PULLUP);
  pinMode(LIM_PAN_POS, INPUT_PULLUP);
  pinMode(LIM_TILT_NEG, INPUT_PULLUP);
  pinMode(LIM_TILT_POS, INPUT_PULLUP);

  digitalWrite(PAN_STEP, LOW);
  digitalWrite(TILT_STEP, LOW);
  digitalWrite(LASER, LOW);
}

void loop() {
  // ===== Doc lenh tu Python =====
  while (Serial.available()) {
    char c = Serial.peek();

    if (c == 'P') {
      Serial.read();
      long v = readLong();
      pan_sps = constrain(v, -MAX_SPS, MAX_SPS);
      if (pan_sps > 0) digitalWrite(PAN_DIR, HIGH);
      else if (pan_sps < 0) digitalWrite(PAN_DIR, LOW);
    }
    else if (c == 'T') {
      Serial.read();
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
    else if (c == '?') { Serial.read(); reportLimits(); }
    else if (c == '+') { Serial.read(); auto_report = true;  }
    else if (c == '-') { Serial.read(); auto_report = false; }
    else { Serial.read(); }
  }

  // ===== Auto-report =====
  if (auto_report) {
    int s0 = limitHit(A0) ? 1 : 0;
    int s1 = limitHit(A1) ? 1 : 0;
    int s2 = limitHit(A2) ? 1 : 0;
    int s3 = limitHit(A3) ? 1 : 0;
    if (s0 != prevL0 || s1 != prevL1 || s2 != prevL2 || s3 != prevL3) {
      reportLimits();
      prevL0 = s0; prevL1 = s1; prevL2 = s2; prevL3 = s3;
    }
  }

  unsigned long now = micros();

  // ===== PAN: dung khi cham limit huong do =====
  long pan_abs = labs(pan_sps);
  bool pan_blocked = (pan_sps < 0 && limitHit(LIM_PAN_NEG)) ||
                     (pan_sps > 0 && limitHit(LIM_PAN_POS));
  if (pan_abs >= MIN_SPS && !pan_blocked) {
    unsigned long half_us = 1000000UL / (2UL * pan_abs);
    if (now - pan_last_us >= half_us) {
      pan_pin_state = !pan_pin_state;
      digitalWrite(PAN_STEP, pan_pin_state);
      pan_last_us = now;
    }
  }

  // ===== TILT =====
  long tilt_abs = labs(tilt_sps);
  bool tilt_blocked = (tilt_sps < 0 && limitHit(LIM_TILT_NEG)) ||
                      (tilt_sps > 0 && limitHit(LIM_TILT_POS));
  if (tilt_abs >= MIN_SPS && !tilt_blocked) {
    unsigned long half_us = 1000000UL / (2UL * tilt_abs);
    if (now - tilt_last_us >= half_us) {
      tilt_pin_state = !tilt_pin_state;
      digitalWrite(TILT_STEP, tilt_pin_state);
      tilt_last_us = now;
    }
  }
}
