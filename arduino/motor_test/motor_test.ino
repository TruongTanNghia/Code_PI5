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
 * LOGIC TIN HIEU (giong code anh da test thanh cong hom truoc):
 *   - Pulse cycle: HIGH(d us) -> LOW(d us)
 *   - Driver count step tren transition (HIGH->LOW)
 *   - Idle state: LOW (khong phat xung)
 *   - QUAN TRONG: phai TANG TOC TU TU tu cham -> nhanh
 *     (5-phase stepper khong khoi dong duoc o toc do cao ngay tu dau)
 *
 * CACH DUNG (Serial Monitor, baud 9600):
 *   1/2/3/4 -> chon kenh
 *   s       -> dung
 *   v       -> RAT CHAM (50 step/s, khong tang toc)
 *   l       -> CHAM    (100 step/s)
 *   m       -> VUA     (200 step/s) [default]
 *   f       -> NHANH   (333 step/s)
 *   x       -> RAT NHANH (500 step/s)
 */

const int PIN_U1 = 2;   // -> Driver 1 CW-   (motor 1 thuan)
const int PIN_U2 = 3;   // -> Driver 1 CCW-  (motor 1 nguoc)
const int PIN_U3 = 4;   // -> Driver 2 CW-   (motor 2 thuan)
const int PIN_U4 = 5;   // -> Driver 2 CCW-  (motor 2 nguoc)

const float STEP_DEG = 0.72;

// THAM SO TANG TOC (lay tu code anh chay duoc)
const int START_DELAY = 5000;   // bat dau cuc cham (100 step/s = 1/(5000us*2))
const int RAMP_STEP   = 50;     // moi step giam delay 50us (cang nho cang muot)

int activePin = -1;
int activeChannel = 0;
int targetDelay = 2500;         // mac dinh 200 step/s
int currentDelay = START_DELAY; // hien tai (se ramp xuong target)

unsigned long stepCount = 0;
unsigned long lastPrint = 0;
unsigned long startTime = 0;


void setAllLow() {
  digitalWrite(PIN_U1, LOW);
  digitalWrite(PIN_U2, LOW);
  digitalWrite(PIN_U3, LOW);
  digitalWrite(PIN_U4, LOW);
}


void selectChannel(int n) {
  setAllLow();
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
  currentDelay = START_DELAY;  // bat dau cham, ramp len target

  Serial.print(F(">>> KENH "));
  Serial.print(n);
  Serial.print(F(" - Pin "));
  Serial.print(activePin);
  Serial.print(F(" - target "));
  Serial.print(500000L / targetDelay);
  Serial.println(F(" step/s (tang toc tu 100 step/s)"));
}


void setSpeed(int sps, const char* label) {
  targetDelay = 500000L / sps;
  Serial.print(F(">>> Toc do target moi: "));
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
  setAllLow();

  delay(100);

  Serial.println();
  Serial.println(F("==============================================="));
  Serial.println(F("  MOTOR TEST v2 - Direct Arduino -> Driver"));
  Serial.println(F("  (logic ACTIVE HIGH + co TANG TOC tu tu)"));
  Serial.println(F("==============================================="));
  Serial.println(F("  D2 -> Driver 1 CW-  (motor 1 thuan)"));
  Serial.println(F("  D3 -> Driver 1 CCW- (motor 1 nguoc)"));
  Serial.println(F("  D4 -> Driver 2 CW-  (motor 2 thuan)"));
  Serial.println(F("  D5 -> Driver 2 CCW- (motor 2 nguoc)"));
  Serial.println();
  Serial.println(F("LENH (go vao Serial):"));
  Serial.println(F("  1/2/3/4 -> chon kenh"));
  Serial.println(F("  s       -> stop"));
  Serial.println(F("  v=50  l=100  m=200  f=333  x=500 step/s"));
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
        setAllLow();
        Serial.println(F(">>> STOP"));
        break;
      case 'v': case 'V': setSpeed(50,  "RAT CHAM"); break;
      case 'l': case 'L': setSpeed(100, "CHAM"); break;
      case 'm': case 'M': setSpeed(200, "VUA"); break;
      case 'f': case 'F': setSpeed(333, "NHANH"); break;
      case 'x': case 'X': setSpeed(500, "RAT NHANH"); break;
      default: break;
    }
  }

  // Phat xung (giong code anh da chay duoc: HIGH -> LOW)
  if (activePin >= 0) {
    digitalWrite(activePin, HIGH);
    delayMicroseconds(currentDelay);
    digitalWrite(activePin, LOW);
    delayMicroseconds(currentDelay);
    stepCount++;

    // TANG TOC: giam currentDelay tu tu cho den khi bang targetDelay
    if (currentDelay > targetDelay) {
      currentDelay -= RAMP_STEP;
      if (currentDelay < targetDelay) currentDelay = targetDelay;
    }

    // In trang thai moi 500ms
    unsigned long now = millis();
    if (now - lastPrint >= 500) {
      float deg = stepCount * STEP_DEG;
      float secs = (now - startTime) / 1000.0;
      int sps = 500000L / currentDelay;
      Serial.print(F("  KENH "));
      Serial.print(activeChannel);
      Serial.print(F("  step="));
      Serial.print(stepCount);
      Serial.print(F("  goc="));
      Serial.print(deg, 1);
      Serial.print(F("deg ("));
      Serial.print(deg / 360.0, 2);
      Serial.print(F(" vong)  toc do hien tai="));
      Serial.print(sps);
      Serial.print(F(" step/s  thoi gian="));
      Serial.print(secs, 1);
      Serial.println(F("s"));
      lastPrint = now;
    }
  }
}
