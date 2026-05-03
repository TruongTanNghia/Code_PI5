#define M1_CW  2
#define M1_CCW 3
#define M2_CW  4
#define M2_CCW 5

int speedLevel = 2;
int pulseDelay = 3000;

bool m1Running = false;
bool m2Running = false;
int m1Pin = -1;
int m2Pin = -1;

unsigned long lastM1 = 0;
unsigned long lastM2 = 0;
bool m1State = LOW;
bool m2State = LOW;

void setup() {
  Serial.begin(9600);

  pinMode(M1_CW, OUTPUT);
  pinMode(M1_CCW, OUTPUT);
  pinMode(M2_CW, OUTPUT);
  pinMode(M2_CCW, OUTPUT);

  stopM1();
  stopM2();
}

void loop() {
  readSerial();
  runMotor1();
  runMotor2();
}

void readSerial() {
  while (Serial.available()) {
    char c = Serial.read();

    // speed 0-9
    if (c >= '0' && c <= '9') {
      speedLevel = c - '0';

      // speed thấp = chậm hơn
      // 0 rất chậm, 9 nhanh
      pulseDelay = map(speedLevel, 0, 9, 8000, 800);
    }

    else if (c == 'F') {      // M1 phải
      startM1(M1_CW);
    }

    else if (c == 'B') {      // M1 trái
      startM1(M1_CCW);
    }

    else if (c == 'U') {      // M2 lên
      startM2(M2_CW);
    }

    else if (c == 'D') {      // M2 xuống
      startM2(M2_CCW);
    }

    else if (c == 'X') {      // stop M1
      stopM1();
    }

    else if (c == 'Y') {      // stop M2
      stopM2();
    }

    else if (c == 'S') {      // stop all
      stopM1();
      stopM2();
    }
  }
}

void startM1(int pin) {
  stopM1();
  m1Pin = pin;
  m1Running = true;
}

void startM2(int pin) {
  stopM2();
  m2Pin = pin;
  m2Running = true;
}

void stopM1() {
  digitalWrite(M1_CW, LOW);
  digitalWrite(M1_CCW, LOW);
  m1Running = false;
  m1Pin = -1;
  m1State = LOW;
}

void stopM2() {
  digitalWrite(M2_CW, LOW);
  digitalWrite(M2_CCW, LOW);
  m2Running = false;
  m2Pin = -1;
  m2State = LOW;
}

void runMotor1() {
  if (!m1Running || m1Pin < 0) return;

  unsigned long now = micros();
  if (now - lastM1 >= pulseDelay) {
    lastM1 = now;
    m1State = !m1State;
    digitalWrite(m1Pin, m1State);
  }
}

void runMotor2() {
  if (!m2Running || m2Pin < 0) return;

  unsigned long now = micros();
  if (now - lastM2 >= pulseDelay) {
    lastM2 = now;
    m2State = !m2State;
    digitalWrite(m2Pin, m2State);
  }
}