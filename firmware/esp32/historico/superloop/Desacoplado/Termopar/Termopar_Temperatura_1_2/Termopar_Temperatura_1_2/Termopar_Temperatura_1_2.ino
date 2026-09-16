#include <max6675.h>

// Pines compartidos
#define SCK  18
#define SO   19

// Pines CS individuales
#define CS1  5
#define CS2  17
#define CS3  16
#define CS4  4

#define NUM_MUESTRAS 16

// Offsets individuales (calibra cada termopar)
double offset[4] = {
  -0.75,   // TC1
  -0.75,   // TC2
  -0.75,   // TC3
  -0.75    // TC4
};

// Objetos
MAX6675 tc1(SCK, CS1, SO);
MAX6675 tc2(SCK, CS2, SO);
MAX6675 tc3(SCK, CS3, SO);
MAX6675 tc4(SCK, CS4, SO);

double leerPreciso(MAX6675 &tc, int idx) {
  double suma = 0;
  int validas = 0;

  for (int i = 0; i < NUM_MUESTRAS; i++) {
    double t = tc.readCelsius();
    if (!isnan(t)) {
      suma += t;
      validas++;
    }
    delay(20);
  }

  if (validas == 0) return NAN;
  return (suma / validas) + offset[idx];
}

void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println("ESP32 + 4x MAX6675 (Alta Estabilidad)");
}

void loop() {
  double t1 = leerPreciso(tc1, 0);
  double t2 = leerPreciso(tc2, 1);
  double t3 = leerPreciso(tc3, 2);
  double t4 = leerPreciso(tc4, 3);

  Serial.println("------ Temperaturas ------");

  if (!isnan(t1)) { Serial.print("TC1: "); Serial.print(t1, 2); Serial.println(" °C"); }
  else Serial.println("TC1: Error");

  if (!isnan(t2)) { Serial.print("TC2: "); Serial.print(t2, 2); Serial.println(" °C"); }
  else Serial.println("TC2: Error");

  if (!isnan(t3)) { Serial.print("TC3: "); Serial.print(t3, 2); Serial.println(" °C"); }
  else Serial.println("TC3: Error");

  if (!isnan(t4)) { Serial.print("TC4: "); Serial.print(t4, 2); Serial.println(" °C"); }
  else Serial.println("TC4: Error");

  Serial.println("--------------------------\n");

  delay(1000);
}
