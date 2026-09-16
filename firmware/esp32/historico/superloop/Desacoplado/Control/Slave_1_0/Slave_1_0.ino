#include <AcPhaseControl.h>

int ZC_PIN   = 3;   // Zero Crossing
int GATE_PIN = 7;   // Gate TRIAC

AcPhaseControl dimmer;

unsigned long windowSize = 3000; // 3 s
unsigned long windowStart = 0;

int potencia = 0; // 0–100 %

void setup()
{
  Serial.begin(115200);

  // IMPORTANTE: variables, no defines
  dimmer.begin(GATE_PIN, ZC_PIN);

  windowStart = millis();
}

void loop()
{
  // Recibe potencia desde ESP32
  if (Serial.available())
  {
    potencia = Serial.parseInt();
    potencia = constrain(potencia, 0, 100);
  }

  unsigned long now = millis();

  if (now - windowStart >= windowSize)
    windowStart += windowSize;

  if ((now - windowStart) < (windowSize * potencia / 100))
    dimmer.APC_ON(GATE_PIN);
  else
    dimmer.APC_OFF(GATE_PIN);
}

