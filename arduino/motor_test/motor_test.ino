/*
 * motor_test.ino - V4 (clean first pulse via Serial.flush)
 *
 * V3 in print xuong Serial truoc khi run_smooth -> TX interrupt firing
 * khi motor bat dau xung dau tien -> motor 5-phase mat sync -> twitch.
 *
 * V4 fix: Serial.flush() truoc run_smooth de cho TX buffer rong han
 *         truoc khi bat dau phat xung -> xung dau tien CHE
 *
 * SO DO DAU NOI: D2/D3/D4/D5 -> CW-/CCW- driver, 5V -> CW+/CCW+, GND -> GND
 *
 * LENH: 1=M1+ 2=M1- 3=M2+ 4=M2- s=STOP
 */

#define PIN_M1_CW  2
#define PIN_M1_CCW 3
#define PIN_M2_CW  4
#define PIN_M2_CCW 5

int start_delay = 5000;
int min_delay   = 1500;
int step_change = 50;

const long MAX_STEPS = 1000000L;


void pulse(int pin, int d) {
  digitalWrite(pin, HIGH);
  delayMicroseconds(d);
  digitalWrite(pin, LOW);
  delayMicroseconds(d);
}


bool stopRequested() {
  if (Serial.available()) {
    char c = Serial.peek();
    if (c == 's' || c == 'S') {
      Serial.read();
      return true;
    }
  }
  return false;
}


void run_smooth(int pin, long steps) {
  // === TANG TOC ===
  for (int d = start_delay; d > min_delay; d -= step_change) {
    pulse(pin, d);
  }

  // === CHAY DEU (check serial moi 128 step) ===
  for (long i = 0; i < steps; i++) {
    pulse(pin, min_delay);

    if ((i & 0x7F) == 0) {
      if (stopRequested()) break;
    }
  }

  // === GIAM TOC ===
  for (int d = min_delay; d < start_delay; d += step_change) {
    pulse(pin, d);
  }
}


void setAllLow() {
  digitalWrite(PIN_M1_CW,  LOW);
  digitalWrite(PIN_M1_CCW, LOW);
  digitalWrite(PIN_M2_CW,  LOW);
  digitalWrite(PIN_M2_CCW, LOW);
}


void setup() {
  Serial.begin(9600);

  pinMode(PIN_M1_CW,  OUTPUT);
  pinMode(PIN_M1_CCW, OUTPUT);
  pinMode(PIN_M2_CW,  OUTPUT);
  pinMode(PIN_M2_CCW, OUTPUT);
  setAllLow();

  delay(100);
  Serial.println();
  Serial.println(F("=== MOTOR v4 (clean first pulse) ==="));
  Serial.println(F("1=M1+ 2=M1- 3=M2+ 4=M2- s=STOP"));
  Serial.flush();   // dam bao banner gui xong truoc khi nhan lenh
}


void loop() {
  if (Serial.available()) {
    char c = Serial.read();
    int pin = -1;
    const char* name = "";

    switch (c) {
      case '1': pin = PIN_M1_CW;  name = "M1 thuan (D2)"; break;
      case '2': pin = PIN_M1_CCW; name = "M1 nguoc (D3)"; break;
      case '3': pin = PIN_M2_CW;  name = "M2 thuan (D4)"; break;
      case '4': pin = PIN_M2_CCW; name = "M2 nguoc (D5)"; break;
      default: return;
    }

    if (pin < 0) return;

    // QUAN TRONG: in roi flush truoc khi spin motor
    // Neu khong flush, byte van dang gui qua TX interrupt
    // -> jitter pulse dau tien -> motor 5-phase mat sync
    Serial.print(F(">>> SPIN "));
    Serial.println(name);
    Serial.flush();   // CHO TX BUFFER RONG HAN

    run_smooth(pin, MAX_STEPS);
    setAllLow();

    Serial.println(F(">>> DONE"));
    Serial.flush();
  }
}
