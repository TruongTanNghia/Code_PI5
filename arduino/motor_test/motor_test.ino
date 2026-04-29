/*
 * motor_test.ino - V10 (V9 simpler + protect motor from DTR reset)
 *
 * V8 auto-run hoat dong. V9 fail khi tu Pi5 trigger qua USB.
 * Nghi van: Pi5 mo serial port -> DTR toggle -> Arduino reset
 *           -> ngat run_smooth giua chung -> motor twitch.
 *
 * V10: trigger don gian, KHONG print gi ca, SPIN dai 5000 step.
 *      Ket hop voi motor_no_dtr.py (Python tat DTR) -> Pi5 mo port
 *      ma KHONG reset Arduino.
 *
 * SO DO DAU NOI: D2/D3/D4/D5 -> CW-/CCW- driver, 5V -> CW+/CCW+, GND -> GND
 *
 * LENH (Pi5 gui): 1=M1+ 2=M1- 3=M2+ 4=M2-
 */

#define M1_CW  2
#define M1_CCW 3
#define M2_CW  4
#define M2_CCW 5


void pulse(int pin, int d) {
  digitalWrite(pin, HIGH);
  delayMicroseconds(d);
  digitalWrite(pin, LOW);
  delayMicroseconds(d);
}


void run_smooth(int pin, int steps) {
  // Tang toc
  for (int d = 5000; d > 1500; d -= 50) {
    pulse(pin, d);
  }
  // Chay deu
  for (int i = 0; i < steps; i++) {
    pulse(pin, 1500);
  }
  // Giam toc
  for (int d = 1500; d < 5000; d += 50) {
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

    while (Serial.available()) Serial.read();

    run_smooth(pin, 5000);
    digitalWrite(pin, LOW);
  }
}
