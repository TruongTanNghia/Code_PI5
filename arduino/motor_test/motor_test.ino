/*
 * motor_test.ino - V9 (V8 base + Serial trigger, NO println anywhere)
 *
 * V8 da test work khi co Serial.begin nhung KHONG co print.
 * V7 fail vi co Serial.println trong setup (lam roi pulse dau tien).
 *
 * V9: V8 base, them Serial.read() de chon channel, KHONG print gi ca.
 *     Spin 5000 step (~15 giay) moi lenh roi tu dung.
 *
 * SO DO DAU NOI: D2/D3/D4/D5 -> CW-/CCW- driver, 5V -> CW+/CCW+, GND -> GND
 *
 * LENH (Pi5 gui qua USB):
 *   1 -> M1 thuan, 2 -> M1 nguoc, 3 -> M2 thuan, 4 -> M2 nguoc
 *   Moi lenh quay 5000 step (~15 giay) roi tu dung.
 *
 * TUYET DOI KHONG dung Serial.print/println O DAU CA - de pulse sach.
 */

#define M1_CW  2
#define M1_CCW 3
#define M2_CW  4
#define M2_CCW 5

int start_delay = 5000;
int min_delay = 1500;
int step_change = 50;

const int RUN_STEPS = 5000;   // ~15 giay quay tai 333 step/s


void pulse(int pin, int d) {
  digitalWrite(pin, HIGH);
  delayMicroseconds(d);
  digitalWrite(pin, LOW);
  delayMicroseconds(d);
}


void run_smooth(int pin, int steps) {
  for (int d = start_delay; d > min_delay; d -= step_change) {
    pulse(pin, d);
  }
  for (int i = 0; i < steps; i++) {
    pulse(pin, min_delay);
  }
  for (int d = min_delay; d < start_delay; d += step_change) {
    pulse(pin, d);
  }
}


void setup() {
  Serial.begin(9600);

  pinMode(M1_CW,  OUTPUT);
  pinMode(M1_CCW, OUTPUT);
  pinMode(M2_CW,  OUTPUT);
  pinMode(M2_CCW, OUTPUT);

  digitalWrite(M1_CW,  LOW);
  digitalWrite(M1_CCW, LOW);
  digitalWrite(M2_CW,  LOW);
  digitalWrite(M2_CCW, LOW);

  // KHONG Serial.println - bat ky print nao trong setup deu disturb pulse dau
}


void loop() {
  if (Serial.available()) {
    char c = Serial.read();
    int pin = -1;

    if (c == '1') pin = M1_CW;
    else if (c == '2') pin = M1_CCW;
    else if (c == '3') pin = M2_CW;
    else if (c == '4') pin = M2_CCW;
    else return;

    // Drain bytes thua trong RX buffer (vd '\n' neu Pi gui kem)
    while (Serial.available()) Serial.read();

    run_smooth(pin, RUN_STEPS);
    digitalWrite(pin, LOW);
  }
}
