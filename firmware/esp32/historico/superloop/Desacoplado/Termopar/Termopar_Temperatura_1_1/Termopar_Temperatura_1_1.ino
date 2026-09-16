#include <max6675.h>

// Pines
#define SCK  18
#define CS   5
#define SO   19

// Ajustes de precisión
#define NUM_MUESTRAS 16
#define OFFSET_CALIBRACION -0.75   // ajusta según tu referencia

MAX6675 thermocouple(SCK, CS, SO);

void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println("MAX6675 + ESP32 (Modo Alta Estabilidad)");
}

double leerTemperaturaPrecisa() {
  double suma = 0;
  int validas = 0;

  for (int i = 0; i < NUM_MUESTRAS; i++) {
    double t = thermocouple.readCelsius();
    if (!isnan(t)) {
      suma += t;
      validas++;
    }
    delay(50); // respeta el tiempo interno del MAX6675
  }

  if (validas == 0) return NAN;

  return (suma / validas) + OFFSET_CALIBRACION;
}

void loop() {
  double temp = leerTemperaturaPrecisa();

  if (isnan(temp)) {
    Serial.println("Error: Termopar desconectado");
  } else {
    Serial.print("Temperatura estable: ");
    Serial.print(temp, 2);
    Serial.println(" °C");
  }

  delay(1000);
}
