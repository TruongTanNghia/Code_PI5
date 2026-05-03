/*
 * motor_dc.ino - 2 DC motor qua L298N (Channel A + B)
 *
 * SO DO DAU NOI:
 *   Arduino   L298N
 *   ------------------------------
 *   Motor 1 (PAN - trai/phai):
 *   D5 (PWM)  ENA
 *   D6        IN1
 *   D7        IN2
 *
 *   Motor 2 (TILT - len/xuong):
 *   D10 (PWM) ENB
 *   D8        IN3
 *   D9        IN4
 *
 *   GND       GND
 *
 *   L298N      Motor + Nguon
 *   ----------------------------
 *   OUT1, OUT2 -> 2 day Motor 1 (pan)
 *   OUT3, OUT4 -> 2 day Motor 2 (tilt)
 *   12V        -> Nguon DC
 *   GND        -> GND nguon
 *
 * LENH (Serial 9600):
 *   F   -> Motor 1 forward (PHAI, toward M1MAX)
 *   B   -> Motor 1 backward (TRAI, toward M1MIN)
 *   U   -> Motor 2 up (toward M2MAX)
 *   D   -> Motor 2 down (toward M2MIN)
 *   X   -> Stop Motor 1 only
 *   Y   -> Stop Motor 2 only
 *   S   -> STOP ALL motors (emergency)
 *   0-9 -> Set toc do (0=stop, 1=PWM 25, ..., 9=PWM 225)
 */

#define ENA 5    // Motor 1 PWM
#define IN1 6    // Motor 1 dir 1
#define IN2 7    // Motor 1 dir 2

#define IN3 8    // Motor 2 dir 1
#define IN4 9    // Motor 2 dir 2
#define ENB 10   // Motor 2 PWM

int motorSpeed = 100;   // chung cho ca 2 motor


void setup() {
  Serial.begin(9600);

  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(ENB, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  stopAll();
}


void m1Forward() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  analogWrite(ENA, motorSpeed);
}

void m1Backward() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  analogWrite(ENA, motorSpeed);
}

void m1Stop() {
  analogWrite(ENA, 0);
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
}


void m2Forward() {
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  analogWrite(ENB, motorSpeed);
}

void m2Backward() {
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
  analogWrite(ENB, motorSpeed);
}

void m2Stop() {
  analogWrite(ENB, 0);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}


void stopAll() {
  m1Stop();
  m2Stop();
}


void loop() {
  if (Serial.available()) {
    char cmd = Serial.read();

    switch (cmd) {
      case 'F': m1Forward();  break;
      case 'B': m1Backward(); break;
      case 'U': m2Forward();  break;
      case 'D': m2Backward(); break;
      case 'X': m1Stop();     break;
      case 'Y': m2Stop();     break;
      case 'S': stopAll();    break;
      default:
        if (cmd >= '0' && cmd <= '9') {
          motorSpeed = (cmd - '0') * 25;
          // Apply ngay neu motor dang chay
          if (digitalRead(IN1) == HIGH || digitalRead(IN2) == HIGH) {
            analogWrite(ENA, motorSpeed);
          }
          if (digitalRead(IN3) == HIGH || digitalRead(IN4) == HIGH) {
            analogWrite(ENB, motorSpeed);
          }
        }
        break;
    }
  }
}
