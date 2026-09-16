#include <AcPhaseControl.h>

int syncsignal = 3;   // Zero crossing
int gate = 7;         // Gate TRIAC

AcPhaseControl Control_Ac;

int angle = 180;      // 180 = apagado
int step = 1;         // suavidad
bool subida = true;

void setup()
{
  Control_Ac.begin(gate, syncsignal);
}

void loop()
{
  Control_Ac.ControlAngle(angle);

  if (subida)
  {
    angle--;
    if (angle <= 0) subida = false;
  }
  else
  {
    angle++;
    if (angle >= 180) subida = true;
  }

  delay(40);   // VELOCIDAD DEL FADE (sube esto para más lento)
}


