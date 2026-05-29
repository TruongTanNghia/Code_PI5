/*
 * 2 STEPPER closed-loop HBS57 (STEP/DIR) + 4 limit switch + laser
 *
 * ====== DAU DAY ======
 *  PAN  (ngang): STEP=D2, DIR=D3   -> HBS57 #1 (PUL-, DIR-)
 *  TILT (doc)  : STEP=D5, DIR=D6   -> HBS57 #2 (PUL-, DIR-)
 *  PUL+/DIR+ cua ca 2 driver -> 5V Arduino
 *  LASER = D7
 *
 *  LIMIT SWITCH (chan chung noi GND, INPUT_PULLUP, nhan=LOW):
 *    A0 = LEN (tilt-)   A1 = XUONG (tilt+)
 *    A2 = TRAI (pan-)   A3 = PHAI  (pan+)
 *
 * ====== GIAO THUC LENH (tu Python) ======
 *  "P<so>\n" -> toc do PAN  (>0 phai, <0 trai, =0 dung), |so|=step/s
 *  "T<so>\n" -> toc do TILT (>0 xuong, <0 len, =0 dung)
 *  'L'=bat laser  'K'=tat laser  'x'=dung het+tat laser
 *  '?'=in limit 1 lan  '+'/'-'=auto in (nguoi doc)  'M'/'N'=auto in (may doc)
 *  'F'=mode TRACK (chan cung cham limit, BAO VE phan cung) - MAC DINH
 *  'S'=mode SCAN  (KHONG chan limit, motor co the quay nguoc lai khi cham)
 *
 *  !!! QUAN TRONG: KHONG dung Serial.parseInt() vi no BLOCK 1 giay
 *      -> motor bi khung/giat. Thay bang parser non-blocking ben duoi.
 */

#define PAN_STEP   2
#define PAN_DIR    3
#define TILT_STEP  5
#define TILT_DIR   6
#define LASER      7

#define LIM_TILT_NEG  A0   // len
#define LIM_TILT_POS  A1   // xuong
#define LIM_PAN_NEG   A2   // trai
#define LIM_PAN_POS   A3   // phai

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

// ===== CHE DO AN TOAN =====
// safety_block = true  -> cham limit thi DUNG (bao ve phan cung, dung khi TRACKING)
// safety_block = false -> KHONG chan limit (dung khi QUET, Python tu lo lat chieu)
// Lenh 'F' bat safety, 'S' tat safety. Mac dinh BAT (an toan truoc).
bool safety_block = true;

// ===== PARSER NON-BLOCKING =====
// Thu thap ky tu cua lenh so (P/T) ma KHONG cho timeout.
// 'cmd_axis' = 'P' hoac 'T' khi dang doc so; 0 khi khong.
char cmd_axis = 0;
long cmd_val = 0;
bool cmd_neg = false;
bool cmd_has_digit = false;

void applyCmd(char axis, long val) {
  if (axis == 'P') {
    pan_sps = constrain(val, -MAX_SPS, MAX_SPS);
    if (pan_sps > 0) digitalWrite(PAN_DIR, HIGH);
    else if (pan_sps < 0) digitalWrite(PAN_DIR, LOW);
    Serial.print("OK PAN sps="); Serial.println(pan_sps);   // log xac nhan
  } else if (axis == 'T') {
    tilt_sps = constrain(val, -MAX_SPS, MAX_SPS);
    if (tilt_sps > 0) digitalWrite(TILT_DIR, HIGH);
    else if (tilt_sps < 0) digitalWrite(TILT_DIR, LOW);
    Serial.print("OK TILT sps="); Serial.println(tilt_sps); // log xac nhan
  }
}

// Doc limit: nhan = LOW. Loc nhieu nhe (2 lan).
bool limitHit(int pin) {
  if (digitalRead(pin) == HIGH) return false;
  delayMicroseconds(20);
  if (digitalRead(pin) == HIGH) return false;
  return true;
}

void reportLimits() {
  Serial.print("A0 LEN: ");    Serial.print(limitHit(A0) ? "NHAN" : "nha ");
  Serial.print(" | A1 XUONG: "); Serial.print(limitHit(A1) ? "NHAN" : "nha ");
  Serial.print(" | A2 TRAI: ");  Serial.print(limitHit(A2) ? "NHAN" : "nha ");
  Serial.print(" | A3 PHAI: ");  Serial.print(limitHit(A3) ? "NHAN" : "nha ");
  Serial.println();
}

void reportLimitsMachine() {
  Serial.print("LIM:");
  Serial.print(limitHit(A0) ? 1 : 0); Serial.print(",");
  Serial.print(limitHit(A1) ? 1 : 0); Serial.print(",");
  Serial.print(limitHit(A2) ? 1 : 0); Serial.print(",");
  Serial.print(limitHit(A3) ? 1 : 0);
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

  Serial.println("ARDUINO READY - stepper v2 (non-blocking)");
}

void loop() {
  // ===== Doc serial NON-BLOCKING tung ky tu mot =====
  while (Serial.available()) {
    char c = Serial.read();

    // Neu dang doc so cho lenh P/T
    if (cmd_axis != 0) {
      if (c == '-') { cmd_neg = true; continue; }
      if (c >= '0' && c <= '9') {
        cmd_val = cmd_val * 10 + (c - '0');
        cmd_has_digit = true;
        continue;
      }
      // ky tu ket thuc so (\n, space, hoac lenh moi) -> ap dung roi xu ly ky tu nay
      if (cmd_has_digit) applyCmd(cmd_axis, cmd_neg ? -cmd_val : cmd_val);
      cmd_axis = 0; cmd_val = 0; cmd_neg = false; cmd_has_digit = false;
      // KHONG continue -> de ky tu hien tai duoc xu ly o ben duoi
    }

    // Xu ly lenh
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
    // ky tu khac (\n, space, '-' khi khong dang doc so...) bo qua
  }

  // ===== Auto-report nguoi doc =====
  if (auto_report) {
    int s0=limitHit(A0)?1:0, s1=limitHit(A1)?1:0, s2=limitHit(A2)?1:0, s3=limitHit(A3)?1:0;
    if (s0!=prevL0||s1!=prevL1||s2!=prevL2||s3!=prevL3) {
      reportLimits(); prevL0=s0; prevL1=s1; prevL2=s2; prevL3=s3;
    }
  }
  // ===== Machine-report cho Python =====
  if (machine_report) {
    int m0=limitHit(A0)?1:0, m1=limitHit(A1)?1:0, m2=limitHit(A2)?1:0, m3=limitHit(A3)?1:0;
    if (m0!=prevM0||m1!=prevM1||m2!=prevM2||m3!=prevM3) {
      reportLimitsMachine(); prevM0=m0; prevM1=m1; prevM2=m2; prevM3=m3;
    }
  }

  unsigned long now = micros();

  // ===== PAN: phat xung. Chan khi cham limit CHI khi safety_block = true =====
  long pan_abs = labs(pan_sps);
  bool pan_blocked = safety_block && (
                       (pan_sps < 0 && limitHit(LIM_PAN_NEG)) ||
                       (pan_sps > 0 && limitHit(LIM_PAN_POS))
                     );
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
