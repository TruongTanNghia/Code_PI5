/*
 * motor_test.ino - V6 (FULL noInterrupts during run_smooth + direct UART poll)
 *
 * V5 chi tat interrupt o pha tang/giam toc, pha chay deu van bi interrupt fire
 * (Timer0 millis tick moi 1ms). Motor 5-phase van mat sync.
 *
 * V6 fix manh hon: noInterrupts() suot tron qua trinh run_smooth.
 *  -> Khong co Timer0, khong co UART interrupt
 *  -> Pulse timing CHE 100%
 * Vao 's' bang cach poll thang UART hardware register (UCSR0A & RXC0).
 *
 * SO DO DAU NOI: D2/D3/D4/D5 -> CW-/CCW- driver, 5V -> CW+/CCW+, GND -> GND
 *
 * LENH: 1=M1+ 2=M1- 3=M2+ 4=M2- s=STOP
 */

#define PIN_M1_CW  2
#define PIN_M1_CCW 3
#define PIN_M2_CW  4
#define PIN_M2_CCW 5

int start_delay = 5000;
int min_delay   = 1500;
int step_change = 50;

const long MAX_STEPS = 1000000L;


void pulse(int pin, int d) {
  digitalWrite(pin, HIGH);
  delayMicroseconds(d);
  digitalWrite(pin, LOW);
  delayMicroseconds(d);
}


// Doc UART tu hardware register, KHONG qua interrupt
inline bool uartByteAvailable() {
  return UCSR0A & (1 << RXC0);
}

inline char uartReadByte() {
  return UDR0;
}


void run_smooth(int pin, long steps) {
  // KHOA TAT CA INTERRUPT - pulse timing CHE
  noInterrupts();

  // PHA TANG TOC
  for (int d = start_delay; d > min_delay; d -= step_change) {
    pulse(pin, d);
  }

  // PHA CHAY DEU - poll UART truc tiep cho 's'
  for (long i = 0; i < steps; i++) {
    pulse(pin, min_delay);

    if ((i & 0x7F) == 0) {     // moi 128 step
      if (uartByteAvailable()) {
        char c = uartReadByte();
        if (c == 's' || c == 'S') break;
      }
    }
  }

  // PHA GIAM TOC
  for (int d = min_delay; d < start_delay; d += step_change) {
    pulse(pin, d);
  }

  // MO LAI INTERRUPT
  interrupts();
}


void setAllLow() {
  digitalWrite(PIN_M1_CW,  LOW);
  digitalWrite(PIN_M1_CCW, LOW);
  digitalWrite(PIN_M2_CW,  LOW);
  digitalWrite(PIN_M2_CCW, LOW);
}


void setup() {
  Serial.begin(9600);

  pinMode(PIN_M1_CW,  OUTPUT);
  pinMode(PIN_M1_CCW, OUTPUT);
  pinMode(PIN_M2_CW,  OUTPUT);
  pinMode(PIN_M2_CCW, OUTPUT);
  setAllLow();

  delay(100);
  Serial.println();
  Serial.println(F("=== MOTOR v6 (full noInterrupts) ==="));
  Serial.println(F("1=M1+ 2=M1- 3=M2+ 4=M2- s=STOP"));
  Serial.flush();
}


void loop() {
  if (Serial.available()) {
    char c = Serial.read();
    int pin = -1;
    const char* name = "";

    switch (c) {
      case '1': pin = PIN_M1_CW;  name = "M1 thuan"; break;
      case '2': pin = PIN_M1_CCW; name = "M1 nguoc"; break;
      case '3': pin = PIN_M2_CW;  name = "M2 thuan"; break;
      case '4': pin = PIN_M2_CCW; name = "M2 nguoc"; break;
      default: return;
    }

    if (pin < 0) return;

    Serial.print(F(">>> SPIN "));
    Serial.println(name);
    Serial.flush();

    run_smooth(pin, MAX_STEPS);
    setAllLow();

    Serial.println(F(">>> DONE"));
    Serial.flush();
  }
}
