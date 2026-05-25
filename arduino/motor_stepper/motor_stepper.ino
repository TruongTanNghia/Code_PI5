/*
 * motor_stepper.ino
 *
 * Dieu khien 2 stepper closed-loop (57HSE2.2N) qua 2 driver HBS57.
 * Giu nguyen protocol nhu motor_dc.ino:
 *   d = pan phai     a = pan trai     h = dung pan
 *   s = tilt xuong   w = tilt len     v = dung tilt
 *   x = dung tat ca  L = laser ON     K = laser OFF
 *
 * -> main.py KHONG can sua, chi can upload sketch nay vao Arduino.
 *
 * DAU NOI (common anode - chan + chung 5V Arduino, chan - la Arduino digital):
 *
 *   Driver TRUC NGANG (X / pan):
 *     Arduino D5  -> HBS57 PUL-
 *     Arduino D6  -> HBS57 DIR-
 *     Arduino 5V  -> HBS57 PUL+  va  DIR+
 *
 *   Driver TRUC DOC (Y / tilt):
 *     Arduino D2  -> HBS57 PUL-
 *     Arduino D3  -> HBS57 DIR-
 *     Arduino 5V  -> HBS57 PUL+  va  DIR+
 *
 *   Common GND: Arduino GND noi voi GND power supply driver.
 *   Driver VDC: cap 24-48V DC tu nguon ngoai (theo SW7/SW8 cho 57HSE).
 *   Motor 57HSE2.2N: A+/A-/B+/B- + encoder EA+/-/EB+/-/VCC/GND vao driver.
 *
 * LOGIC ACTIVE LOW:
 *   - PUL = HIGH (idle), keo LOW de tao xung
 *   - 1 chu ky LOW->HIGH = 1 microstep
 *   - DIR LOW = mot chieu, DIR HIGH = chieu nguoc
 *   - Neu motor di sai chieu so voi camera, dao 2 case 'a' va 'd'
 *     (hoac 'w' va 's'), HOAC flip DIP SW5 tren driver
 */

#define X_PUL 5
#define X_DIR 6
#define Y_PUL 2
#define Y_DIR 3
#define LASER_PIN 13   // mac dinh LED onboard - thay neu noi laser khac

// Toc do pulse (microseconds cho 1/2 chu ky)
// 500us nghia la 1 pulse moi 1ms = 1000 step/giay
// Tang len 1000 cho cham hon, giam xuong 250 cho nhanh hon (chu y motor stall)
const unsigned long PULSE_HALF_US = 500;

bool xRunning = false;
bool yRunning = false;
unsigned long lastXEdge = 0;
unsigned long lastYEdge = 0;
bool xPulHigh = true;     // idle = HIGH (active LOW)
bool yPulHigh = true;


void setup() {
  Serial.begin(9600);

  pinMode(X_PUL, OUTPUT);
  pinMode(X_DIR, OUTPUT);
  pinMode(Y_PUL, OUTPUT);
  pinMode(Y_DIR, OUTPUT);
  pinMode(LASER_PIN, OUTPUT);

  // Idle: PUL HIGH (no pulse), DIR LOW (default chieu)
  digitalWrite(X_PUL, HIGH);
  digitalWrite(Y_PUL, HIGH);
  digitalWrite(X_DIR, LOW);
  digitalWrite(Y_DIR, LOW);
  digitalWrite(LASER_PIN, LOW);
}


void handleCommand(char c) {
  switch (c) {
    // ====== PAN (truc X / ngang) ======
    case 'd':  // pan phai (object o ben phai -> camera quay phai)
      digitalWrite(X_DIR, HIGH);
      xRunning = true;
      break;
    case 'a':  // pan trai
      digitalWrite(X_DIR, LOW);
      xRunning = true;
      break;
    case 'h':  // stop pan
      xRunning = false;
      break;

    // ====== TILT (truc Y / doc) ======
    case 's':  // tilt xuong (object phia duoi -> camera cui xuong)
      digitalWrite(Y_DIR, HIGH);
      yRunning = true;
      break;
    case 'w':  // tilt len
      digitalWrite(Y_DIR, LOW);
      yRunning = true;
      break;
    case 'v':  // stop tilt
      yRunning = false;
      break;

    // ====== STOP ALL ======
    case 'x':
      xRunning = false;
      yRunning = false;
      break;

    // ====== LASER ======
    case 'L':
      digitalWrite(LASER_PIN, HIGH);
      break;
    case 'K':
      digitalWrite(LASER_PIN, LOW);
      break;

    default:
      break;
  }
}


void loop() {
  // 1. Doc serial command (non-blocking)
  while (Serial.available()) {
    char c = Serial.read();
    handleCommand(c);
  }

  // 2. Phat xung (non-blocking)
  unsigned long now = micros();

  if (xRunning) {
    if (now - lastXEdge >= PULSE_HALF_US) {
      lastXEdge = now;
      xPulHigh = !xPulHigh;
      digitalWrite(X_PUL, xPulHigh ? HIGH : LOW);
    }
  } else if (!xPulHigh) {
    // Dam bao idle HIGH khi dung
    digitalWrite(X_PUL, HIGH);
    xPulHigh = true;
  }

  if (yRunning) {
    if (now - lastYEdge >= PULSE_HALF_US) {
      lastYEdge = now;
      yPulHigh = !yPulHigh;
      digitalWrite(Y_PUL, yPulHigh ? HIGH : LOW);
    }
  } else if (!yPulHigh) {
    digitalWrite(Y_PUL, HIGH);
    yPulHigh = true;
  }
}
