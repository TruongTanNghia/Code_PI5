/*
 * motor_test.ino - V5 (noInterrupts during accel/decel)
 *
 * Loi V4: Serial.begin enabled UART interrupt -> jitter cho xung dau tien
 *         -> motor 5-phase mat sync -> twitch.
 *
 * V5 fix: noInterrupts() trong pha TANG TOC va GIAM TOC.
 *         Pha chay deu cho phep interrupts de nhan duoc lenh 's' STOP.
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


void run_smooth(int pin, long steps) {
  // === PHA 1: TANG TOC - CRITICAL, KHOA INTERRUPT ===
  // Khoa interrupt de timing xung CHE
  // Motor 5-phase can xung dau tien khong bi disturb de lock sync
  noInterrupts();
  for (int d = start_delay; d > min_delay; d -= step_change) {
    pulse(pin, d);
  }
  interrupts();

  // === PHA 2: CHAY DEU - cho phep interrupt de nhan 's' ===
  for (long i = 0; i < steps; i++) {
    pulse(pin, min_delay);

    // Check 's' moi 128 step
    if ((i & 0x7F) == 0) {
      if (Serial.available()) {
        char c = Serial.peek();
        if (c == 's' || c == 'S') {
          Serial.read();
          break;
        }
      }
    }
  }

  // === PHA 3: GIAM TOC - critical lai ===
  noInterrupts();
  for (int d = min_delay; d < start_delay; d += step_change) {
    pulse(pin, d);
  }
  interrupts();
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
  Serial.println(F("=== MOTOR v5 (noInterrupts accel/decel) ==="));
  Serial.println(F("1=M1+ 2=M1- 3=M2+ 4=M2- s=STOP"));
  Serial.flush();
}


void loop() {
  if (Serial.available()) {
    char c = Serial.read();
    int pin = -1;
    const char* name = "";

    switch (c) {
      case '1': pin = PIN_M1_CW;  name = "M1 thuan"; break;
      case '2': pin = PIN_M1_CCW; name = "M1 nguoc"; break;
      case '3': pin = PIN_M2_CW;  name = "M2 thuan"; break;
      case '4': pin = PIN_M2_CCW; name = "M2 nguoc"; break;
      default: return;
    }

    if (pin < 0) return;

    Serial.print(F(">>> SPIN "));
    Serial.println(name);
    Serial.flush();   // dam bao TX hoan toan rong truoc khi vao run_smooth

    run_smooth(pin, MAX_STEPS);
    setAllLow();

    Serial.println(F(">>> DONE"));
    Serial.flush();
  }
}
