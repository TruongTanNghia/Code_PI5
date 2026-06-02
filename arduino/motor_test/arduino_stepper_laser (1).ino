/*
 * 2 STEPPER closed-loop HBS57 (STEP/DIR) + 4 limit switch + laser
 *
 * ====== DAU DAY ======
 *  PAN  (ngang): STEP=D2, DIR=D3   -> HBS57 #1 (PUL-, DIR-)
 *  TILT (doc)  : STEP=D5, DIR=D6   -> HBS57 #2 (PUL-, DIR-)
 *  PUL+/DIR+ cua ca 2 driver -> 5V Arduino
 *  LASER = A5 (active HIGH)
 *
 *  LIMIT SWITCH (chan chung GND, INPUT_PULLUP, nhan=LOW):
 *    A0 = cong tac TREN vat ly  (chan tilt khi quay LEN)
 *    A1 = cong tac DUOI vat ly  (chan tilt khi quay XUONG)
 *    A2 = cong tac PHAI vat ly  (chan PAN khi quay TRAI - PAN DOI DIEN)
 *    A3 = cong tac TRAI vat ly  (chan PAN khi quay PHAI - PAN DOI DIEN)
 *
 * ====== GIAO THUC LENH (tu Python) ======
 *  "P<so>\n" -> toc do PAN  (>0 phai, <0 trai, =0 dung), |so|=step/s
 *  "T<so>\n" -> toc do TILT (>0 xuong, <0 len, =0 dung)
 *  'L'=bat laser  'K'=tat laser  'x'=dung het+tat laser
 *  '?'=in limit 1 lan  '+'/'-'=auto in (nguoi doc)  'M'/'N'=auto in (may doc)
 *  'F'=mode TRACK (chan cung cham limit, BAO VE phan cung) - MAC DINH
 *  'S'=mode SCAN  (KHONG chan limit, motor co the quay nguoc lai khi cham)
 */

#define PAN_STEP   2
#define PAN_DIR    3
#define TILT_STEP  5
#define TILT_DIR   6
#define LASER      A5   // Laser: active HIGH

// TILT BINH THUONG: quay len dap cong tac TREN, quay xuong dap cong tac DUOI
#define LIM_TILT_NEG  A0   // ngat quay LEN  = cong tac TREN vat ly
#define LIM_TILT_POS  A1   // ngat quay XUONG = cong tac DUOI vat ly
// PAN DOI DIEN: quay trai dap cong tac PHAI, quay phai dap cong tac TRAI
// DA SWAP A2<->A3 cho khop dau day thuc te (xac dinh tu log):
//   pan quay TRAI (sps<0) dap cong tac PHAI vat ly = A3 -> chan sps<0
//   pan quay PHAI (sps>0) dap cong tac TRAI vat ly = A2 -> chan sps>0
#define LIM_PAN_NEG   A3   // ngat quay TRAI (sps<0) = cong tac PHAI vat ly (A3)
#define LIM_PAN_POS   A2   // ngat quay PHAI (sps>0) = cong tac TRAI vat ly (A2)

const long MAX_SPS = 4000;
const long MIN_SPS = 150;

long pan_sps  = 0;
long tilt_sps = 0;

unsigned long pan_last_us  = 0;
unsigned long tilt_last_us = 0;
bool pan_pin_state  = false;
bool tilt_pin_state = false;

bool auto_report = false;
bool machine_report = false;
int prevL0=-1, prevL1=-1, prevL2=-1, prevL3=-1;
int prevM0=-1, prevM1=-1, prevM2=-1, prevM3=-1;

bool safety_block = true;

char cmd_axis = 0;
long cmd_val = 0;
bool cmd_neg = false;
bool cmd_has_digit = false;

void applyCmd(char axis, long val) {
  if (axis == 'P') {
    pan_sps = constrain(val, -MAX_SPS, MAX_SPS);
    // DA DAO HIGH/LOW de pan_sps>0 = quay PHAI vat ly (khop voi setup phan cung)
    if (pan_sps > 0) digitalWrite(PAN_DIR, LOW);
    else if (pan_sps < 0) digitalWrite(PAN_DIR, HIGH);
    Serial.print("OK PAN sps="); Serial.println(pan_sps);
  } else if (axis == 'T') {
    tilt_sps = constrain(val, -MAX_SPS, MAX_SPS);
    if (tilt_sps > 0) digitalWrite(TILT_DIR, HIGH);
    else if (tilt_sps < 0) digitalWrite(TILT_DIR, LOW);
    Serial.print("OK TILT sps="); Serial.println(tilt_sps);
  }
}

// Doc limit cong tac:
// - PHAT HIEN NHAN ngay lap tuc khi thay LOW (de phan ung nhanh, khong bo lo)
// - Filter nhe 3 lan de chong nhieu xung ngan
bool limitHit(int pin) {
  if (digitalRead(pin) == LOW) {
    // Confirm: doc them 2 lan nua de chong nhieu (xung ngan)
    delayMicroseconds(50);
    if (digitalRead(pin) == LOW) {
      delayMicroseconds(50);
      if (digitalRead(pin) == LOW) return true;
    }
  }
  return false;
}

void reportLimits() {
  Serial.print("LEN: ");     Serial.print(limitHit(LIM_TILT_NEG) ? "NHAN" : "nha ");
  Serial.print(" | XUONG: "); Serial.print(limitHit(LIM_TILT_POS) ? "NHAN" : "nha ");
  Serial.print(" | TRAI(ngat-quay-trai): ");  Serial.print(limitHit(LIM_PAN_NEG)  ? "NHAN" : "nha ");
  Serial.print(" | PHAI(ngat-quay-phai): ");  Serial.print(limitHit(LIM_PAN_POS)  ? "NHAN" : "nha ");
  Serial.println();
}

void reportLimitsMachine() {
  Serial.print("LIM:");
  Serial.print(limitHit(LIM_TILT_NEG) ? 1 : 0); Serial.print(",");  // LEN
  Serial.print(limitHit(LIM_TILT_POS) ? 1 : 0); Serial.print(",");  // XUONG
  Serial.print(limitHit(LIM_PAN_NEG)  ? 1 : 0); Serial.print(",");  // ngat quay TRAI
  Serial.print(limitHit(LIM_PAN_POS)  ? 1 : 0);                     // ngat quay PHAI
  Serial.println();
}

void setup() {
  Serial.begin(9600);

  pinMode(PAN_STEP, OUTPUT);
  pinMode(PAN_DIR, OUTPUT);
  pinMode(TILT_STEP, OUTPUT);
  pinMode(TILT_DIR, OUTPUT);
  pinMode(LASER, OUTPUT);

  pinMode(LIM_TILT_NEG, INPUT_PULLUP);
  pinMode(LIM_TILT_POS, INPUT_PULLUP);
  pinMode(LIM_PAN_NEG, INPUT_PULLUP);
  pinMode(LIM_PAN_POS, INPUT_PULLUP);

  digitalWrite(PAN_STEP, LOW);
  digitalWrite(TILT_STEP, LOW);
  digitalWrite(LASER, LOW);

  Serial.println("ARDUINO READY - stepper v3 (PAN doi dien)");
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();

    if (cmd_axis != 0) {
      if (c == '-') { cmd_neg = true; continue; }
      if (c >= '0' && c <= '9') {
        cmd_val = cmd_val * 10 + (c - '0');
        cmd_has_digit = true;
        continue;
      }
      if (cmd_has_digit) applyCmd(cmd_axis, cmd_neg ? -cmd_val : cmd_val);
      cmd_axis = 0; cmd_val = 0; cmd_neg = false; cmd_has_digit = false;
    }

    if (c == 'P' || c == 'T') {
      cmd_axis = c; cmd_val = 0; cmd_neg = false; cmd_has_digit = false;
    }
    else if (c == 'L') digitalWrite(LASER, HIGH);
    else if (c == 'K') digitalWrite(LASER, LOW);
    else if (c == 'x') { pan_sps = 0; tilt_sps = 0; digitalWrite(LASER, LOW); }
    else if (c == '?') reportLimits();
    else if (c == '+') auto_report = true;
    else if (c == 'M') { machine_report = true; reportLimitsMachine(); }
    else if (c == 'N') machine_report = false;
    else if (c == 'F') { safety_block = true;  Serial.println("MODE: TRACK"); }
    else if (c == 'S') { safety_block = false; Serial.println("MODE: SCAN"); }
  }

  if (auto_report) {
    int s0=limitHit(A0)?1:0, s1=limitHit(A1)?1:0, s2=limitHit(A2)?1:0, s3=limitHit(A3)?1:0;
    if (s0!=prevL0||s1!=prevL1||s2!=prevL2||s3!=prevL3) {
      reportLimits(); prevL0=s0; prevL1=s1; prevL2=s2; prevL3=s3;
    }
  }
  if (machine_report) {
    int m0=limitHit(A0)?1:0, m1=limitHit(A1)?1:0, m2=limitHit(A2)?1:0, m3=limitHit(A3)?1:0;
    bool changed = (m0!=prevM0||m1!=prevM1||m2!=prevM2||m3!=prevM3);
    // Gui khi DOI trang thai, HOAC dinh ky 100ms khi co bat ky limit nao chạm
    // (de Python chac chan biet limit dang cham, khong bo lo)
    static unsigned long lastSendMs = 0;
    bool anyHit = (m0 || m1 || m2 || m3);
    unsigned long nowMs = millis();
    if (changed || (anyHit && nowMs - lastSendMs >= 100)) {
      reportLimitsMachine();
      prevM0=m0; prevM1=m1; prevM2=m2; prevM3=m3;
      lastSendMs = nowMs;
    }
  }

  unsigned long now = micros();

  // ===== PAN: cham limit -> DUNG huong do (ca TRACK va SCAN) =====
  // Python (Scanner) tu lo lat chieu khi scan, dua tren trang thai LIM
  // Arduino chi viec: huong nao cham limit thi khong phat xung huong do.
  long pan_abs = labs(pan_sps);
  bool pan_blocked = (pan_sps > 0 && limitHit(LIM_PAN_POS)) ||
                     (pan_sps < 0 && limitHit(LIM_PAN_NEG));
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
  bool tilt_blocked = safety_block && (
                        (tilt_sps < 0 && limitHit(LIM_TILT_NEG)) ||
                        (tilt_sps > 0 && limitHit(LIM_TILT_POS))
                      );
  if (tilt_abs >= MIN_SPS && !tilt_blocked) {
    unsigned long half_us = 1000000UL / (2UL * tilt_abs);
    if (now - tilt_last_us >= half_us) {
      tilt_pin_state = !tilt_pin_state;
      digitalWrite(TILT_STEP, tilt_pin_state);
      tilt_last_us = now;
    }
  }
}
