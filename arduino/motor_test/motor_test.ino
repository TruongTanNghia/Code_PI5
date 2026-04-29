/*
 * motor_test.ino - V3 (dua tren CODE GOC cua anh, da test work)
 *
 * Su dung run_smooth() y het code goc cua anh, them check Serial moi 128 step
 * de co the dung giua chung neu Pi gui 's'.
 *
 * SO DO DAU NOI:
 *   D2  -> Driver 1 CW-   (motor 1 thuan)
 *   D3  -> Driver 1 CCW-  (motor 1 nguoc)
 *   D4  -> Driver 2 CW-   (motor 2 thuan)
 *   D5  -> Driver 2 CCW-  (motor 2 nguoc)
 *   5V  -> CW+ va CCW+ ca 2 driver
 *   GND -> GND ca 2 driver
 *
 * LENH (Serial 9600):
 *   1 -> M1 thuan, 2 -> M1 nguoc, 3 -> M2 thuan, 4 -> M2 nguoc
 *   s -> STOP (dung giua chung)
 */

#define PIN_M1_CW  2
#define PIN_M1_CCW 3
#define PIN_M2_CW  4
#define PIN_M2_CCW 5

// THONG SO CHINH XAC GIONG CODE GOC CUA ANH (da test work)
int start_delay = 5000;
int min_delay   = 1500;
int step_change = 50;

const long MAX_STEPS = 1000000L;   // gan nhu khong gioi han, chi dung khi 's' den


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

    if ((i & 0x7F) == 0) {     // 0x7F = 127 (& nhanh hon %)
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
  Serial.println(F("=== MOTOR v3 (orig + serial stop) ==="));
  Serial.println(F("1=M1+ 2=M1- 3=M2+ 4=M2- s=STOP"));
  Serial.println();
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
      case 's': case 'S':
        // s nhan ngoai run_smooth -> idle, khong lam gi
        return;
      default:
        return;
    }

    if (pin < 0) return;

    Serial.print(F(">>> SPIN "));
    Serial.println(name);

    run_smooth(pin, MAX_STEPS);
    setAllLow();

    Serial.println(F(">>> STOP/DONE"));
  }
}
