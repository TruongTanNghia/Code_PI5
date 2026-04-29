/*
 * motor_test.ino - V8 (DIAGNOSTIC: OLD code + Serial.begin only)
 *
 * Y CHANG code goc cua anh, chi them 1 dong Serial.begin(9600).
 * KHONG co Serial.read, KHONG co print, KHONG xu ly lenh.
 * Auto-run forever giong code goc.
 *
 * MUC DICH: kiem tra xem chi viec enable Serial co lam motor twitch khong.
 *
 * Sau khi upload, motor PHAI quay nhu code goc:
 *   - Quay thuan 800 step (~2.4 giay)
 *   - Cho 2 giay
 *   - Quay nguoc 800 step
 *   - Cho 3 giay
 *   - Lap lai
 *
 * Neu motor van twitch -> Serial.begin co tac dong -> can fix.
 * Neu motor quay binh thuong -> Serial.begin OK, van de o cho khac.
 */

#define CW 2
#define CCW 3

int start_delay = 5000;
int min_delay = 1500;
int step_change = 50;


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
  Serial.begin(9600);   // <-- DONG DUY NHAT KHAC code goc

  pinMode(CW, OUTPUT);
  pinMode(CCW, OUTPUT);
  digitalWrite(CW, LOW);
  digitalWrite(CCW, LOW);
}


void loop() {
  run_smooth(CW, 800);
  delay(2000);

  run_smooth(CCW, 800);
  delay(3000);
}
