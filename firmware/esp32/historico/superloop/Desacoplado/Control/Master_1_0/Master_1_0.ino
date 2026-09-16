#include <max6675.h>
#define SCK  18
#define CS   5
#define SO   19
double setpoint = 60.0;   // °C objetivo
double Kp = 3.0;
double Ki = 0.05;
double Kd = 10.0;
double tempActual;
double salidaPID;
double error, errorPrevio;
double integral, derivada;

unsigned long lastPID = 0;
const unsigned long PID_INTERVAL = 1000; // 1 segundo

MAX6675 thermocouple(SCK, CS, SO);

void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println("MAX6675 + ESP32 (Modo Alta Estabilidad)");

  Serial2.begin(
  115200,
  SERIAL_8N1,
  -1,      // RX no usado
  17       // TX (elige el GPIO que cableaste)
);

}

double calcularPID(double setpoint, double input)
{
  double error = setpoint - input;

  // Corte de seguridad
  if (input >= setpoint)
  {
    integral = 0;
    errorPrevio = error;
    return 0;
  }

  // Integral con anti-windup
  integral += error;

  double derivada = error - errorPrevio;
  errorPrevio = error;

  double output = Kp * error + Ki * integral + Kd * derivada;

  output = constrain(output, 0, 100);
  return output;
}


void loop()
{
  if (millis() - lastPID >= PID_INTERVAL)
  {
    lastPID = millis();

    double temp = thermocouple.readCelsius();
    if (isnan(temp)) return;

    tempActual = temp;
    salidaPID = calcularPID(setpoint, tempActual);

    Serial.print("Temp: ");
    Serial.print(tempActual);
    Serial.print(" °C | Potencia: ");
    Serial.print(salidaPID);
    Serial.println(" %");

    // ENVÍO AL SLAVE
    Serial2.print((int)salidaPID);
    Serial2.print('\n');
  }
}
