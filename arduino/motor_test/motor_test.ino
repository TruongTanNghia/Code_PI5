/*
 * motor_test.ino
 *
 * Test stepper Autonics A16K-M569 + driver MD5-HD14.
 * NOI THANG ARDUINO VAO DRIVER (khong qua PC817).
 *
 * SO DO DAU NOI:
 *
 *   Arduino Uno R3            ->  Driver MD5-HD14
 *   ----------------------------------------------
 *   D2  (output)              ->  CW-   (Driver 1)
 *   D3  (output)              ->  CCW-  (Driver 1)
 *   D4  (output)              ->  CW-   (Driver 2)
 *   D5  (output)              ->  CCW-  (Driver 2)
 *   5V  (cap nguon cho opto)  ->  CW+ va CCW+ cua CA HAI driver
 *   GND                       ->  GND cua CA HAI driver
 *
 *   [Driver 1 & 2]
 *     +24V  ->  V+
 *     GND   ->  V-
 *     5 day mau (BLUE/RED/ORANGE/GREEN/BLACK) -> motor
 *
 * LOGIC TIN HIEU (QUAN TRONG - khac voi cach noi qua PC817):
 *   - Idle (khong xung): Arduino pin = HIGH (5V) -> CW- = 5V
 *     -> Khong co dong qua driver LED (CW+ va CW- cung 5V)
 *     -> Driver KHONG step
 *   - Active (xung): Arduino pin = LOW (0V) -> CW- = 0V
 *     -> Dong chay tu CW+ (5V) qua driver internal LED -> CW- (0V) -> GND
 *     -> Driver thay 1 xung -> Step 1 cai
 *
 * MOI BUOC = 1 chu ky LOW(active) -> HIGH(idle) -> LOW... -> 1 step = 0.72 deg
 *
 * CACH DUNG (Serial Monitor, baud 9600):
 *   1/2/3/4 -> chon kenh (motor 1 thuan/nguoc, motor 2 thuan/nguoc)
 *   s       -> dung
 *   v       -> RAT CHAM (5 step/s)
 *   l       -> CHAM (50 step/s)
 *   m       -> VUA (200 step/s, default)
 *   f       -> NHANH (1000 step/s)
 */

const int PIN_U1 = 2;   // -> Driver 1 CW-   (motor 1 thuan)
const int PIN_U2 = 3;   // -> Driver 1 CCW-  (motor 1 nguoc)
const int PIN_U3 = 4;   // -> Driver 2 CW-   (motor 2 thuan)
const int PIN_U4 = 5;   // -> Driver 2 CCW-  (motor 2 nguoc)

const float STEP_DEG = 0.72;  // A16K-M569

// ACTIVE LOW: idle = HIGH, pulse active = LOW
const int IDLE  = HIGH;
const int PULSE = LOW;

int activePin = -1;
int activeChannel = 0;
int delayUs = 2500;           // mac dinh 200 step/s

unsigned long stepCount = 0;
unsigned long lastPrint = 0;
unsigned long startTime = 0;


void setAllIdle() {
  digitalWrite(PIN_U1, IDLE);
  digitalWrite(PIN_U2, IDLE);
  digitalWrite(PIN_U3, IDLE);
  digitalWrite(PIN_U4, IDLE);
}


void selectChannel(int n) {
  setAllIdle();
  switch (n) {
    case 1: activePin = PIN_U1; break;
    case 2: activePin = PIN_U2; break;
    case 3: activePin = PIN_U3; break;
    case 4: activePin = PIN_U4; break;
    default: activePin = -1; return;
  }
  activeChannel = n;
  stepCount = 0;
  startTime = millis();
  lastPrint = startTime;

  Serial.print(F(">>> KENH "));
  Serial.print(n);
  Serial.print(F(" - GPIO Pin "));
  Serial.print(activePin);
  Serial.print(F("  toc do: "));
  Serial.print(500000L / delayUs);
  Serial.println(F(" step/s"));
}


void setSpeed(int sps, const char* label) {
  delayUs = 500000L / sps;
  Serial.print(F(">>> Toc do moi: "));
  Serial.print(sps);
  Serial.print(F(" step/s ("));
  Serial.print(label);
  Serial.println(F(")"));
}


void setup() {
  Serial.begin(9600);

  pinMode(PIN_U1, OUTPUT);
  pinMode(PIN_U2, OUTPUT);
  pinMode(PIN_U3, OUTPUT);
  pinMode(PIN_U4, OUTPUT);
  setAllIdle();   // Quan trong: HIGH = no step

  delay(100);

  Serial.println();
  Serial.println(F("==============================================="));
  Serial.println(F("  MOTOR TEST - Direct Arduino -> Driver"));
  Serial.println(F("  (KHONG qua PC817 - logic ACTIVE LOW)"));
  Serial.println(F("==============================================="));
  Serial.println(F("  D2 -> Driver 1 CW-  (motor 1 thuan)"));
  Serial.println(F("  D3 -> Driver 1 CCW- (motor 1 nguoc)"));
  Serial.println(F("  D4 -> Driver 2 CW-  (motor 2 thuan)"));
  Serial.println(F("  D5 -> Driver 2 CCW- (motor 2 nguoc)"));
  Serial.println(F("  5V -> CW+ va CCW+ ca 2 driver"));
  Serial.println(F("  GND -> GND ca 2 driver"));
  Serial.println();
  Serial.println(F("LENH (go vao Serial Monitor):"));
  Serial.println(F("  1/2/3/4 -> chon kenh"));
  Serial.println(F("  s       -> stop"));
  Serial.println(F("  v       -> rat cham (5 step/s)"));
  Serial.println(F("  l       -> cham    (50 step/s)"));
  Serial.println(F("  m       -> vua     (200 step/s) [default]"));
  Serial.println(F("  f       -> nhanh   (1000 step/s)"));
  Serial.println(F("==============================================="));
  Serial.println(F("San sang. Go 1, 2, 3, hoac 4 de bat dau..."));
  Serial.println();
}


void loop() {
  // Doc Serial input
  if (Serial.available()) {
    char c = Serial.read();
    switch (c) {
      case '1': selectChannel(1); break;
      case '2': selectChannel(2); break;
      case '3': selectChannel(3); break;
      case '4': selectChannel(4); break;
      case 's':
      case 'S':
        activePin = -1;
        setAllIdle();
        Serial.println(F(">>> STOP"));
        break;
      case 'v': case 'V': setSpeed(5, "RAT CHAM"); break;
      case 'l': case 'L': setSpeed(50, "CHAM"); break;
      case 'm': case 'M': setSpeed(200, "VUA"); break;
      case 'f': case 'F': setSpeed(1000, "NHANH"); break;
      default: break;
    }
  }

  // Phat xung neu dang co kenh active
  // Logic: pulse active = LOW (keo CW- xuong GND -> dong qua driver LED)
  //        idle         = HIGH (CW- = 5V, khong co dong)
  if (activePin >= 0) {
    digitalWrite(activePin, PULSE);   // active = LOW
    delayMicroseconds(delayUs);
    digitalWrite(activePin, IDLE);    // idle = HIGH
    delayMicroseconds(delayUs);
    stepCount++;

    unsigned long now = millis();
    if (now - lastPrint >= 500) {
      float deg = stepCount * STEP_DEG;
      float secs = (now - startTime) / 1000.0;
      Serial.print(F("  KENH "));
      Serial.print(activeChannel);
      Serial.print(F("  step="));
      Serial.print(stepCount);
      Serial.print(F("  goc="));
      Serial.print(deg, 1);
      Serial.print(F("deg ("));
      Serial.print(deg / 360.0, 2);
      Serial.print(F(" vong)  thoi gian="));
      Serial.print(secs, 1);
      Serial.println(F("s"));
      lastPrint = now;
    }
  }
}
