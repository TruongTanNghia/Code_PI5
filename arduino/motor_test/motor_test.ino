/*
 * motor_test.ino
 *
 * Test stepper Autonics A16K-M569 + driver MD5-HD14 + module PC817 4-kenh.
 * Tuong tu spin.py ben Pi5 nhung chay tren Arduino (5V logic - du dong cho PC817).
 *
 * CACH DAU NOI (Arduino Uno):
 *
 *   Arduino  -> PC817 IN  -> PC817 OUT (U) -> Driver
 *   ----------------------------------------------
 *   Pin 2    -> IN1       -> U1            -> Driver 1 CW-
 *   Pin 3    -> IN2       -> U2            -> Driver 1 CCW-
 *   Pin 4    -> IN3       -> U3            -> Driver 2 CW-
 *   Pin 5    -> IN4       -> U4            -> Driver 2 CCW-
 *   GND      -> G(input)  -> G(output) -> GND driver
 *   5V       -> Vcc PC817 (cap nguon module - QUAN TRONG)
 *
 *   Driver:
 *     CW+/CCW+ -> +24V
 *     20-35V +/- -> nguon DC 24V
 *     5 day mau (BLUE/RED/ORANGE/GREEN/BLACK) -> motor
 *
 * CACH DUNG (Serial Monitor, baud 9600):
 *   Go phim '1' -> quay channel U1
 *   Go phim '2' -> quay channel U2
 *   Go phim '3' -> quay channel U3
 *   Go phim '4' -> quay channel U4
 *   Go phim 's' -> dung
 *   Go phim 'f' -> NHANH (1000 step/s)
 *   Go phim 'm' -> VUA (200 step/s)
 *   Go phim 'l' -> CHAM (50 step/s)
 *   Go phim 'v' -> RAT CHAM (5 step/s, de quan sat LED)
 */

const int PIN_U1 = 2;   // -> PC817 IN1 -> U1 -> driver 1 CW-
const int PIN_U2 = 3;   // -> PC817 IN2 -> U2 -> driver 1 CCW-
const int PIN_U3 = 4;   // -> PC817 IN3 -> U3 -> driver 2 CW-
const int PIN_U4 = 5;   // -> PC817 IN4 -> U4 -> driver 2 CCW-

const float STEP_DEG = 0.72;  // A16K-M569

int activePin = -1;
int activeChannel = 0;
int delayUs = 2500;           // mac dinh 200 step/s (= 2500us moi nua chu ky)

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

  Serial.print(F(">>> KENH "));
  Serial.print(n);
  Serial.print(F(" (U"));
  Serial.print(n);
  Serial.print(F(") - GPIO Pin "));
  Serial.print(activePin);
  Serial.print(F("  toc do: "));
  Serial.print(500000L / delayUs);
  Serial.println(F(" step/s"));
}


void setSpeed(int sps, const char* label) {
  delayUs = 500000L / sps;  // half period in microseconds
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
  setAllLow();

  delay(100);

  Serial.println();
  Serial.println(F("==============================================="));
  Serial.println(F("  MOTOR TEST - Autonics A16K-M569 + MD5-HD14"));
  Serial.println(F("==============================================="));
  Serial.println(F("  Pin 2 -> IN1 -> U1 (driver1 CW)"));
  Serial.println(F("  Pin 3 -> IN2 -> U2 (driver1 CCW)"));
  Serial.println(F("  Pin 4 -> IN3 -> U3 (driver2 CW)"));
  Serial.println(F("  Pin 5 -> IN4 -> U4 (driver2 CCW)"));
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
        setAllLow();
        Serial.println(F(">>> STOP"));
        break;
      case 'v': case 'V': setSpeed(5, "RAT CHAM"); break;
      case 'l': case 'L': setSpeed(50, "CHAM"); break;
      case 'm': case 'M': setSpeed(200, "VUA"); break;
      case 'f': case 'F': setSpeed(1000, "NHANH"); break;
      default: break;  // bo qua \n, \r va ky tu khac
    }
  }

  // Phat xung neu dang co kenh active
  if (activePin >= 0) {
    digitalWrite(activePin, HIGH);
    delayMicroseconds(delayUs);
    digitalWrite(activePin, LOW);
    delayMicroseconds(delayUs);
    stepCount++;

    // In trang thai moi 500ms
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
