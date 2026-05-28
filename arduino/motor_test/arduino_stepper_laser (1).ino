/*
 * TEST RIENG MOTOR STEPPER (HBS57) - KHONG CAN PYTHON
 *
 * Muc dich: kiem tra phan cung motor + driver co chay khong.
 * Nap code nay vao, motor se TU DONG quay qua lai, khong can gui lenh gi.
 *
 * ====== DAU DAY ======
 *  PAN  (ngang): STEP=D2, DIR=D3
 *  TILT (doc)  : STEP=D5, DIR=D6
 *  Driver HBS57:
 *    PUL+ -> 5V Arduino
 *    PUL- -> D2 (pan) / D5 (tilt)
 *    DIR+ -> 5V Arduino
 *    DIR- -> D3 (pan) / D6 (tilt)
 *
 *  !!! QUAN TRONG: neu co module trung gian giua Arduino va driver
 *      -> THAO RA, noi THANG Arduino vao driver de test.
 *
 * ====== HOAT DONG ======
 *  Motor PAN  quay phai 1 giay -> dung 0.5s -> quay trai 1 giay -> dung 0.5s -> lap
 *  Motor TILT lam tuong tu, lech pha
 *  Serial in trang thai de theo doi (mo Serial Monitor 9600).
 *
 *  Neu motor KHONG quay:
 *   - Xem den driver co nhay khi motor "dang quay" trong log khong
 *   - Kiem tra DIP: SW7=off, SW8=on (cho motor 57)
 *   - Kiem tra day A+/A-/B+/B- motor
 *   - Thao module trung gian, noi thang
 */

#define PAN_STEP   2
#define PAN_DIR    3
#define TILT_STEP  5
#define TILT_DIR   6
#define LED_BUILTIN_PIN 13   // den on-board de bao Arduino dang chay

// Toc do: nua chu ky xung (microseconds). Lon hon = cham hon, chac hon.
// 500us ~ 1000 step/s (cham, de motor chay chac khi test).
unsigned int STEP_HALF_US = 500;

// So step quay moi luot (200 step = 1 vong neu 1.8 do/step, full step)
long STEPS_PER_MOVE = 400;

void setup() {
  Serial.begin(9600);

  pinMode(PAN_STEP, OUTPUT);
  pinMode(PAN_DIR, OUTPUT);
  pinMode(TILT_STEP, OUTPUT);
  pinMode(TILT_DIR, OUTPUT);
  pinMode(LED_BUILTIN_PIN, OUTPUT);

  digitalWrite(PAN_STEP, LOW);
  digitalWrite(TILT_STEP, LOW);

  Serial.println("=== TEST MOTOR STEPPER - TU DONG QUAY ===");
  Serial.println("Motor se quay qua lai. Xem motor co quay + den driver co nhay khong.");
  delay(1000);
}

// Quay 1 motor: phat 'steps' xung tren chan step
void quay(int stepPin, int dirPin, bool chieu, long steps, const char* ten) {
  digitalWrite(dirPin, chieu ? HIGH : LOW);
  digitalWrite(LED_BUILTIN_PIN, HIGH);   // den sang khi dang quay
  Serial.print(ten);
  Serial.print(" quay ");
  Serial.print(chieu ? "PHAI/XUONG" : "TRAI/LEN");
  Serial.print(" (");
  Serial.print(steps);
  Serial.println(" steps)...");

  for (long i = 0; i < steps; i++) {
    digitalWrite(stepPin, HIGH);
    delayMicroseconds(STEP_HALF_US);
    digitalWrite(stepPin, LOW);
    delayMicroseconds(STEP_HALF_US);
  }
  digitalWrite(LED_BUILTIN_PIN, LOW);    // den tat khi quay xong
}

void loop() {
  // ===== TEST PAN =====
  Serial.println("\n--- TEST MOTOR PAN (D2/D3) ---");
  quay(PAN_STEP, PAN_DIR, true, STEPS_PER_MOVE, "PAN");   // phai
  delay(500);
  quay(PAN_STEP, PAN_DIR, false, STEPS_PER_MOVE, "PAN");  // trai
  delay(1000);

  // ===== TEST TILT =====
  Serial.println("\n--- TEST MOTOR TILT (D5/D6) ---");
  quay(TILT_STEP, TILT_DIR, true, STEPS_PER_MOVE, "TILT");  // xuong
  delay(500);
  quay(TILT_STEP, TILT_DIR, false, STEPS_PER_MOVE, "TILT"); // len
  delay(1000);

  Serial.println("\n=== Lap lai sau 2 giay ===");
  delay(2000);
}
