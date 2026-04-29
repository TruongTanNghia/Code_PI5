/*
 * motor_test.ino - V7 (gan giong code goc cua anh nhat co the)
 *
 * Code GIONG HET code goc cua anh, chi them:
 *   - Serial.begin(9600)
 *   - Lenh '1'/'2'/'3'/'4' tu Serial -> goi run_smooth tuong ung
 *   - Khong co print, khong co flush, khong co stop check
 *   - Motor quay xong 800 step roi tu dung (giong code goc)
 *
 * Neu V7 NAY khong chay -> phai chuyen huong khac (vd Pi5 GPIO truc tiep).
 *
 * SO DO DAU NOI: D2/D3/D4/D5 -> CW-/CCW- driver, 5V -> CW+/CCW+, GND -> GND
 *
 * LENH: 1=M1+ 2=M1- 3=M2+ 4=M2- (moi lenh chay 800 step)
 */

#define M1_CW  2
#define M1_CCW 3
#define M2_CW  4
#define M2_CCW 5

int start_delay = 5000;
int min_delay = 1500;
int step_change = 50;


void pulse(int pin, int d) {
  digitalWrite(pin, HIGH);
  delayMicroseconds(d);
  digitalWrite(pin, LOW);
  delayMicroseconds(d);
}


void run_smooth(int pin, int steps) {
  for (int d = start_delay; d > min_delay; d -= step_change) {
    pulse(pin, d);
  }
  for (int i = 0; i < steps; i++) {
    pulse(pin, min_delay);
  }
  for (int d = min_delay; d < start_delay; d += step_change) {
    pulse(pin, d);
  }
}


void setup() {
  Serial.begin(9600);

  pinMode(M1_CW,  OUTPUT);
  pinMode(M1_CCW, OUTPUT);
  pinMode(M2_CW,  OUTPUT);
  pinMode(M2_CCW, OUTPUT);

  digitalWrite(M1_CW,  LOW);
  digitalWrite(M1_CCW, LOW);
  digitalWrite(M2_CW,  LOW);
  digitalWrite(M2_CCW, LOW);

  Serial.println(F("V7 ready. Send 1/2/3/4"));
}


void loop() {
  if (Serial.available()) {
    char c = Serial.read();
    int pin = -1;

    if (c == '1') pin = M1_CW;
    else if (c == '2') pin = M1_CCW;
    else if (c == '3') pin = M2_CW;
    else if (c == '4') pin = M2_CCW;
    else return;

    // KHONG print gi ca - giu code y nhu OLD code, run_smooth ngay
    run_smooth(pin, 800);
    digitalWrite(pin, LOW);
  }
}
