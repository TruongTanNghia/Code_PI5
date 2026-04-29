/*
 * motor_test.ino - SIMPLE VERSION
 *
 * Giong code cu cua anh (chay duoc), chi them Serial de chon kenh.
 * KHONG co Serial.print khi dang quay -> khong gian doan xung.
 *
 * SO DO DAU NOI:
 *   D2  -> Driver 1 CW-   (motor 1 thuan)
 *   D3  -> Driver 1 CCW-  (motor 1 nguoc)
 *   D4  -> Driver 2 CW-   (motor 2 thuan)
 *   D5  -> Driver 2 CCW-  (motor 2 nguoc)
 *   5V  -> CW+ va CCW+ ca 2 driver
 *   GND -> GND ca 2 driver
 *
 * CACH DUNG (Serial Monitor 9600 baud, hoac arduino_motor.py):
 *   1 -> motor 1 quay thuan, 1000 step (~720 deg)
 *   2 -> motor 1 quay nguoc, 1000 step
 *   3 -> motor 2 quay thuan, 1000 step
 *   4 -> motor 2 quay nguoc, 1000 step
 *
 * Khi nhan lenh -> motor quay tron 1000 step roi tu dung.
 * Khong nhan duoc lenh moi khi dang quay (de pulse khong bi gian doan).
 */

#define PIN_M1_CW  2
#define PIN_M1_CCW 3
#define PIN_M2_CW  4
#define PIN_M2_CCW 5

const int START_DELAY = 5000;   // bat dau cuc cham (~100 step/s)
const int MIN_DELAY   = 1500;   // toc do toi da (~333 step/s)
const int RAMP_STEP   = 50;     // do muot
const int RUN_STEPS   = 1000;   // so step chay deu (1000 * 0.72 = 720 deg = 2 vong)


void pulse(int pin, int d) {
  digitalWrite(pin, HIGH);
  delayMicroseconds(d);
  digitalWrite(pin, LOW);
  delayMicroseconds(d);
}


void run_smooth(int pin, int steps) {
  // Tang toc
  for (int d = START_DELAY; d > MIN_DELAY; d -= RAMP_STEP) {
    pulse(pin, d);
  }
  // Chay deu
  for (int i = 0; i < steps; i++) {
    pulse(pin, MIN_DELAY);
  }
  // Giam toc
  for (int d = MIN_DELAY; d < START_DELAY; d += RAMP_STEP) {
    pulse(pin, d);
  }
}


void setup() {
  Serial.begin(9600);

  pinMode(PIN_M1_CW,  OUTPUT); digitalWrite(PIN_M1_CW,  LOW);
  pinMode(PIN_M1_CCW, OUTPUT); digitalWrite(PIN_M1_CCW, LOW);
  pinMode(PIN_M2_CW,  OUTPUT); digitalWrite(PIN_M2_CW,  LOW);
  pinMode(PIN_M2_CCW, OUTPUT); digitalWrite(PIN_M2_CCW, LOW);

  delay(100);
  Serial.println();
  Serial.println(F("=== MOTOR TEST (simple) ==="));
  Serial.println(F("Go: 1=M1-thuan, 2=M1-nguoc, 3=M2-thuan, 4=M2-nguoc"));
  Serial.print(F("Moi lenh quay "));
  Serial.print(RUN_STEPS);
  Serial.println(F(" step (~720 deg) roi tu dung."));
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
      default: return;  // bo qua \n, \r, ky tu khac
    }

    Serial.print(F(">>> Quay "));
    Serial.print(name);
    Serial.print(F(" - "));
    Serial.print(RUN_STEPS);
    Serial.println(F(" step..."));

    run_smooth(pin, RUN_STEPS);

    Serial.println(F(">>> XONG. Go lenh tiep."));
  }
}
