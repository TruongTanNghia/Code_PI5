/*
 * motor_test.ino - LIEN TUC + STOP
 *
 * Mode: nhan lenh -> quay LIEN TUC voi tang toc.
 *       Nhan 's' -> dung NGAY (giam toc nhe).
 *
 * SO DO DAU NOI:
 *   D2  -> Driver 1 CW-   (motor 1 thuan)
 *   D3  -> Driver 1 CCW-  (motor 1 nguoc)
 *   D4  -> Driver 2 CW-   (motor 2 thuan)
 *   D5  -> Driver 2 CCW-  (motor 2 nguoc)
 *   5V  -> CW+ va CCW+ ca 2 driver
 *   GND -> GND ca 2 driver
 *
 * LENH (qua Serial 9600 baud):
 *   1 -> motor 1 quay thuan LIEN TUC
 *   2 -> motor 1 quay nguoc LIEN TUC
 *   3 -> motor 2 quay thuan LIEN TUC
 *   4 -> motor 2 quay nguoc LIEN TUC
 *   s -> DUNG NGAY
 */

#define PIN_M1_CW  2
#define PIN_M1_CCW 3
#define PIN_M2_CW  4
#define PIN_M2_CCW 5

const int START_DELAY = 5000;   // bat dau cham (~100 step/s)
const int MIN_DELAY   = 1500;   // toc do toi da (~333 step/s)
const int RAMP_STEP   = 50;     // do muot tang toc

int activePin = -1;             // pin dang phat xung (-1 = idle)
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
  Serial.println(F("=== MOTOR (continuous + stop) ==="));
  Serial.println(F("1=M1+ 2=M1- 3=M2+ 4=M2- s=STOP"));
  Serial.println();
}


void loop() {
  // Check Serial - non-blocking
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

  // Phat xung neu dang spin
  if (activePin >= 0) {
    digitalWrite(activePin, HIGH);
    delayMicroseconds(currentDelay);
    digitalWrite(activePin, LOW);
    delayMicroseconds(currentDelay);
    stepCount++;

    // Tang toc
    if (currentDelay > MIN_DELAY) {
      currentDelay -= RAMP_STEP;
      if (currentDelay < MIN_DELAY) currentDelay = MIN_DELAY;
    }
  }
}
