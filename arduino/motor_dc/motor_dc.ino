/*
 * motor_dc.ino - DC motor qua H-bridge (L298N) + dieu chinh toc do tu Pi5
 *
 * SO DO DAU NOI:
 *   Arduino   H-bridge (L298N)
 *   ------------------------------
 *   D5 (PWM)  ENA   (chinh toc do)
 *   D6        IN1   (chieu 1)
 *   D7        IN2   (chieu 2)
 *   GND       GND
 *
 *   H-bridge      Motor + Nguon
 *   ----------------------------
 *   OUT1, OUT2 -> 2 day cua DC motor
 *   12V         -> Nguon DC
 *   GND         -> GND nguon
 *
 * LENH (Serial 9600):
 *   F   -> quay thuan (toc do hien tai)
 *   B   -> quay nguoc
 *   S   -> dung
 *   0-9 -> set toc do (0=dung, 1=cham nhat, 9=nhanh nhat)
 *          Vi du gui '3' -> PWM = 3*25 = 75
 *
 * MAC DINH toc do = 100 PWM (~40% - cham vua phai).
 */

#define ENA 5
#define IN1 6
#define IN2 7

int currentSpeed = 100;   // mac dinh PWM = 100 (cham vua)


void setup() {
  Serial.begin(9600);

  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);

  stopMotor();
}


void loop() {
  if (Serial.available()) {
    char cmd = Serial.read();

    if (cmd == 'F') {
      digitalWrite(IN1, HIGH);
      digitalWrite(IN2, LOW);
      analogWrite(ENA, currentSpeed);
    }
    else if (cmd == 'B') {
      digitalWrite(IN1, LOW);
      digitalWrite(IN2, HIGH);
      analogWrite(ENA, currentSpeed);
    }
    else if (cmd == 'S') {
      stopMotor();
    }
    else if (cmd >= '0' && cmd <= '9') {
      // Set toc do: 0=stop, 1=25 PWM, ..., 9=225 PWM
      currentSpeed = (cmd - '0') * 25;
      // Cap nhat ngay neu motor dang chay
      if (digitalRead(IN1) == HIGH || digitalRead(IN2) == HIGH) {
        analogWrite(ENA, currentSpeed);
      }
    }
  }
}


void stopMotor() {
  analogWrite(ENA, 0);
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
}
