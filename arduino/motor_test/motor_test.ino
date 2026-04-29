/*
 * motor_test.ino - LIEN TUC + STOP (TIGHT BURST)
 *
 * Mode: nhan lenh -> quay LIEN TUC voi tang toc.
 *       Nhan 's' -> dung NGAY.
 *
 * KEY: pulse trong tight burst (50 step / loop) de timing on dinh
 *      cho motor 5-phase. Stop response ~150ms (acceptable).
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
 *   s -> STOP
 */

#define PIN_M1_CW  2
#define PIN_M1_CCW 3
#define PIN_M2_CW  4
#define PIN_M2_CCW 5

const int START_DELAY = 5000;
const int MIN_DELAY   = 1500;
const int RAMP_STEP   = 50;
const int BURST_SIZE  = 50;     // so step / 1 burst (timing on dinh)

int activePin = -1;
int currentDelay = START_DELAY;
unsigned long stepCount = 0;


void setAllLow() {
  digitalWrite(PIN_M1_CW,  LOW);
  digitalWrite(PIN_M1_CCW, LOW);
  digitalWrite(PIN_M2_CW,  LOW);
  digitalWrite(PIN_M2_CCW, LOW);
}


void startSpin(int pin, const char* name) {
  setAllLow();
  activePin = pin;
  currentDelay = START_DELAY;
  stepCount = 0;
  Serial.print(F(">>> SPIN "));
  Serial.print(name);
  Serial.println(F(" - lien tuc"));
}


void stopSpin() {
  setAllLow();
  activePin = -1;
  Serial.print(F(">>> STOP. Tong: "));
  Serial.print(stepCount);
  Serial.print(F(" step ("));
  Serial.print(stepCount * 0.72, 1);
  Serial.println(F(" deg)"));
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
  Serial.println(F("=== MOTOR (continuous + stop, burst) ==="));
  Serial.println(F("1=M1+ 2=M1- 3=M2+ 4=M2- s=STOP"));
  Serial.println();
}


void loop() {
  // === 1. Check Serial command ===
  if (Serial.available()) {
    char c = Serial.read();
    switch (c) {
      case '1': startSpin(PIN_M1_CW,  "M1 thuan (D2)"); break;
      case '2': startSpin(PIN_M1_CCW, "M1 nguoc (D3)"); break;
      case '3': startSpin(PIN_M2_CW,  "M2 thuan (D4)"); break;
      case '4': startSpin(PIN_M2_CCW, "M2 nguoc (D5)"); break;
      case 's': case 'S':
        if (activePin >= 0) stopSpin();
        break;
      default: break;
    }
  }

  // === 2. Run pulse BURST (tight loop, on dinh timing) ===
  if (activePin >= 0) {
    int pin = activePin;            // cache vao bien local cho toc do
    int delay_us = currentDelay;
    int min_d = MIN_DELAY;
    int ramp = RAMP_STEP;

    for (int i = 0; i < BURST_SIZE; i++) {
      digitalWrite(pin, HIGH);
      delayMicroseconds(delay_us);
      digitalWrite(pin, LOW);
      delayMicroseconds(delay_us);

      // Tang toc trong burst
      if (delay_us > min_d) {
        delay_us -= ramp;
        if (delay_us < min_d) delay_us = min_d;
      }
    }

    // Cap nhat lai bien global sau burst
    currentDelay = delay_us;
    stepCount += BURST_SIZE;
  }
}
