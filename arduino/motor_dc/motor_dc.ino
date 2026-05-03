/*
 * motor_dc.ino - DC motor qua H-bridge (L298N hoac tuong tu)
 *
 * Day la code anh da nap va test work tren Arduino Uno.
 * Luu o day de tham khao.
 *
 * SO DO DAU NOI:
 *   Arduino                 H-bridge (L298N)
 *   ----------------------------------------
 *   D5 (PWM)  ENA -> ENA       (chinh toc do)
 *   D6        IN1 -> IN1       (chieu quay 1)
 *   D7        IN2 -> IN2       (chieu quay 2)
 *   GND           -> GND
 *
 *   H-bridge   Motor + Nguon
 *   ----------------------------
 *   OUT1, OUT2  -> 2 day cua DC motor
 *   12V         -> Nguon DC 12V
 *   GND         -> GND nguon
 *
 * LENH (Serial 9600):
 *   F -> quay thuan (200/255 PWM)
 *   B -> quay nguoc
 *   S -> dung
 */

#define ENA 5
#define IN1 6
#define IN2 7


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

    if (cmd == 'F') {        // quay thuan
      digitalWrite(IN1, HIGH);
      digitalWrite(IN2, LOW);
      analogWrite(ENA, 200);
    }
    else if (cmd == 'B') {   // quay nguoc
      digitalWrite(IN1, LOW);
      digitalWrite(IN2, HIGH);
      analogWrite(ENA, 200);
    }
    else if (cmd == 'S') {   // dung
      stopMotor();
    }
  }
}


void stopMotor() {
  analogWrite(ENA, 0);
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
}
