#include <ServoSmooth.h>

ServoSmooth serv[7];

uint32_t servoTimer;
uint32_t turnTimer;

void setup() {
  for (int i = 0; i < 7; ++i) {
    serv[i].attach(i + 2);
    serv[i].setSpeed(1000);
    serv[i].setAccel(0.5);
  }

   Serial.begin(115200);
}

void loop() {
  if (millis() - servoTimer >= 20) {  // взводим таймер на 20 мс (как в библиотеке)
    servoTimer += 20;
    for (byte i = 0; i < 7; i++) {
      serv[i].tickManual();   // двигаем все сервы. Такой вариант эффективнее отдельных тиков
    }
  }

  if (millis() - turnTimer >= 100) {
    turnTimer = millis();
    if (Serial.available() && Serial.read() == 254) {
      for (int i = 0; i < 7; ++i) {
        while (!Serial.available());
        int v = Serial.read();
        serv[i].setTargetDeg(v);
      }
      Serial.write('a');
    }
  }
}
