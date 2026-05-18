#define M1_LEFT   2
#define M1_RIGHT  3
#define M2_DOWN   4
#define M2_UP     5

int targetDelay = 4000;   // nhỏ hơn = nhanh hơn, thử 4000 -> 3000 -> 2000

bool m1_run = false;
bool m2_run = false;

int m1_pin = -1;
int m2_pin = -1;

void pulsePin(int pin, int d) {
  // Active LOW
  digitalWrite(pin, LOW);
  delayMicroseconds(d);
  digitalWrite(pin, HIGH);
  delayMicroseconds(d);
}

void stopM1() {
  m1_run = false;
  m1_pin = -1;
  digitalWrite(M1_LEFT, HIGH);
  digitalWrite(M1_RIGHT, HIGH);
}

void stopM2() {
  m2_run = false;
  m2_pin = -1;
  digitalWrite(M2_UP, HIGH);
  digitalWrite(M2_DOWN, HIGH);
}

void startM1(int pin) {
  m1_pin = pin;
  m1_run = true;
}

void startM2(int pin) {
  m2_pin = pin;
  m2_run = true;
}

void setup() {
  Serial.begin(9600);

  pinMode(M1_LEFT, OUTPUT);
  pinMode(M1_RIGHT, OUTPUT);
  pinMode(M2_DOWN, OUTPUT);
  pinMode(M2_UP, OUTPUT);

  // Active LOW: HIGH = không chạy
  digitalWrite(M1_LEFT, HIGH);
  digitalWrite(M1_RIGHT, HIGH);
  digitalWrite(M2_DOWN, HIGH);
  digitalWrite(M2_UP, HIGH);
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();

    if (c == 'a') startM1(M1_LEFT);        // trái
    else if (c == 'd') startM1(M1_RIGHT);  // phải
    else if (c == 's') startM2(M2_DOWN);   // xuống
    else if (c == 'w') startM2(M2_UP);     // lên

    else if (c == 'h') stopM1();           // dừng ngang
    else if (c == 'v') stopM2();           // dừng dọc
    else if (c == 'x') {
      stopM1();
      stopM2();
    }
  }

  if (m1_run && m1_pin != -1) {
    pulsePin(m1_pin, targetDelay);
  }

  if (m2_run && m2_pin != -1) {
    pulsePin(m2_pin, targetDelay);
  }
}