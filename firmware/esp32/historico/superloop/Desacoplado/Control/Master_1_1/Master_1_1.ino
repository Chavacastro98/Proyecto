/****************************************************
   SISTEMA MULTIZONA 3 RESISTENCIAS + 4 TERMOPARES
   ESP32 (MASTER)
****************************************************/

#include <max6675.h>   // Librería para el módulo MAX6675

// ---------------- PINES SPI COMPARTIDOS ----------------
// Todos los MAX6675 comparten reloj (SCK) y datos (SO)
#define SCK  18   // Pin reloj SPI
#define SO   19   // Pin salida de datos del MAX6675

// Cada termopar necesita su propio pin CS (Chip Select)
#define CS1  5    // Zona 1
#define CS2  16   // Zona 2
#define CS3  4    // Zona 3
#define CS4  2    // Ambiente (solo monitoreo)

// Crear los 4 objetos MAX6675
MAX6675 tc1(SCK, CS1, SO);
MAX6675 tc2(SCK, CS2, SO);
MAX6675 tc3(SCK, CS3, SO);
MAX6675 tc4(SCK, CS4, SO); // Ambiente

// ---------------- CONFIGURACIÓN PID ----------------

// Temperatura objetivo para cada zona
double setpoint[3] = {60, 60, 60};

// Constantes PID (pueden personalizarse por zona si quieres)
double Kp = 3.0;
double Ki = 0.05;
double Kd = 10.0;

// Variables internas del PID para cada zona
double integral[3] = {0,0,0};       // Acumulador integral
double errorPrevio[3] = {0,0,0};    // Para calcular derivada

// ---------------- SOFT START ----------------

// Límite progresivo de potencia por zona
double limitePotencia[3] = {0,0,0};

// Temporizadores
unsigned long lastPID = 0;     // Controla cada cuánto se ejecuta el PID
unsigned long lastRamp = 0;    // Controla la velocidad de la rampa

const unsigned long PID_INTERVAL = 1000;     // 1 segundo entre cálculos PID
const unsigned long RAMP_INTERVAL = 200;     // 200 ms entre incrementos

/****************************************************
   FUNCIÓN PID PARA UNA ZONA
   zona  -> índice 0,1,2
   input -> temperatura actual
****************************************************/
double calcularPID(int zona, double input)
{
  // Error = diferencia entre objetivo y temperatura actual
  double error = setpoint[zona] - input;

  // Seguridad:
  // Si ya alcanzó o superó el setpoint, apaga
  if (input >= setpoint[zona])
  {
    integral[zona] = 0;           // Reinicia integral
    errorPrevio[zona] = error;    // Guarda error
    return 0;                     // Potencia = 0%
  }

  // Acumulación integral
  integral[zona] += error;

  // Derivada = cambio de error
  double derivada = error - errorPrevio[zona];

  // Guardar error actual para la próxima iteración
  errorPrevio[zona] = error;

  // Fórmula PID
  double output = Kp * error 
                + Ki * integral[zona] 
                + Kd * derivada;

  // Limitar salida entre 0% y 100%
  return constrain(output, 0, 100);
}

void setup()
{
  Serial.begin(115200);  // Monitor serial PC

  // Comunicación con Nano (dimmers)
  Serial2.begin(
    115200,
    SERIAL_8N1,
    -1,     // RX no usado
    17      // TX hacia Nano
  );

  Serial.println("Sistema 3 Zonas + Ambiente");
}

void loop()
{
  /****************************************************
     BLOQUE 1: RAMPA DE ARRANQUE
     Incrementa lentamente el límite de potencia
  ****************************************************/
  if (millis() - lastRamp >= RAMP_INTERVAL)
  {
    lastRamp = millis();

    for (int i=0; i<3; i++)
    {
      if (limitePotencia[i] < 100)
        limitePotencia[i] += 1;   // +1% cada 200ms
    }
  }

  /****************************************************
     BLOQUE 2: EJECUCIÓN PID
  ****************************************************/
  if (millis() - lastPID >= PID_INTERVAL)
  {
    lastPID = millis();

    // Leer temperaturas
    double t1 = tc1.readCelsius();
    double t2 = tc2.readCelsius();
    double t3 = tc3.readCelsius();
    double ambiente = tc4.readCelsius();

    // Si alguna lectura falla, salir
    if (isnan(t1) || isnan(t2) || isnan(t3) || isnan(ambiente))
      return;

    // Guardar temperaturas de zonas en arreglo
    double temps[3] = {t1, t2, t3};
    double salidaFinal[3];

    // Calcular PID para cada zona
    for (int i=0; i<3; i++)
    {
      double salidaPID = calcularPID(i, temps[i]);

      // Aplicar limitador de rampa
      salidaFinal[i] = min(salidaPID, limitePotencia[i]);
    }

    /****************************************************
       MONITOR SERIAL (DEBUG)
    ****************************************************/
    Serial.print("T1: "); Serial.print(t1);
    Serial.print(" | T2: "); Serial.print(t2);
    Serial.print(" | T3: "); Serial.print(t3);
    Serial.print(" | Amb: "); Serial.print(ambiente);
    Serial.println();

    Serial.print("P1: "); Serial.print(salidaFinal[0]);
    Serial.print(" | P2: "); Serial.print(salidaFinal[1]);
    Serial.print(" | P3: "); Serial.print(salidaFinal[2]);
    Serial.println("\n");

    /****************************************************
       ENVÍO AL NANO
       Formato: 35,60,10\n
    ****************************************************/
    Serial2.print((int)salidaFinal[0]);
    Serial2.print(",");
    Serial2.print((int)salidaFinal[1]);
    Serial2.print(",");
    Serial2.print((int)salidaFinal[2]);
    Serial2.print('\n');
  }
}
