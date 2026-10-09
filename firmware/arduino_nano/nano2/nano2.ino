/**
 * =================================================================================
 * FIRMWARE ALTERNATIVO DEL ARDUINO NANO CON LIBRERÍA JELDimmer2 (nano2.ino)
 * =================================================================================
 * Plataforma: Arduino Nano (ATmega328P)
 * Módulo de potencia: Dimmer AC de 4 canales (JEL Electrónica / BTA24-800BW)
 *
 * ¿QUÉ HACE ESTE PROGRAMA?
 * Es una versión alternativa del firmware del Arduino Nano que usa la librería
 * JELDimmer2 (incluida en la misma carpeta del sketch) en lugar de controlar
 * los TRIACs directamente con interrupciones y registros PORT.
 *
 * DIFERENCIA CON nano.ino:
 * En vez de usar control de ángulo de fase (disparo retardado por microsegundos),
 * este firmware usa control de TIEMPO PROPORCIONAL: divide el tiempo en ventanas
 * de 3 segundos y enciende/apaga los TRIACs a ciclos completos (100% o 0%) según
 * el porcentaje de potencia deseado. Es más simple pero produce más fluctuación
 * térmica que el control de fase.
 *
 * SEGURIDAD:
 * Si no llegan datos del ESP32 por más de 4 segundos, todas las salidas se apagan.
 * =================================================================================
 */

#include <Arduino.h>
#include "JELDimmer2.h"

// =================================================================================
// PINES DEL HARDWARE
// =================================================================================
const int ZC_PIN = 3;                  // Pin de cruce por cero (INT1)
const int GATE_PINS[] = {7, 8, 9, 10}; // Pines de disparo a los TRIACs
const int NUM_CANALES = 4;             // Cantidad de canales de potencia

// Objeto de la librería JELDimmer2
JELDimmer2 dimmer;

// =================================================================================
// VARIABLES DE CONTROL
// =================================================================================
const unsigned long WINDOW_SIZE_MS = 3000; // Duración de la ventana de tiempo proporcional (3 seg)
unsigned long windowStart = 0;              // Inicio de la ventana actual
int potencias[4] = {0, 0, 0, 0};           // Potencias recibidas del ESP32 (0 a 100%)

// Perro guardián de comunicación
unsigned long ultimaComunicacionMs = 0;
const unsigned long TIMEOUT_UART_MS = 4000; // Apagar si no hay datos en 4 segundos

// Buffer para recepción serie byte a byte
char rxBuf[32];
uint8_t rxPos = 0;

/**
 * Configuración inicial del Arduino Nano.
 */
void setup() {
  Serial.begin(9600); 
  
  // Inicializar el módulo dimmer con los 4 pines de disparo y el pin de cruce por cero
  dimmer.begin(GATE_PINS[0], GATE_PINS[1], GATE_PINS[2], GATE_PINS[3], ZC_PIN);
  
  // Apagar todos los canales al arrancar
  for (int i = 0; i < NUM_CANALES; i++) {
    dimmer.APC_OFF(GATE_PINS[i]);
  }
  
  windowStart = millis();
  ultimaComunicacionMs = millis();
}

/**
 * Bucle principal.
 */
void loop() {
  // --- 1. RECEPCIÓN SERIE (byte a byte, sin bloquear) ---
  // Formato esperado del ESP32: "pot0,pot1,pot2,pot3\n"
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      rxBuf[rxPos] = '\0';
      int p0, p1, p2, p3;
      if (sscanf(rxBuf, "%d,%d,%d,%d", &p0, &p1, &p2, &p3) == 4) {
        potencias[0] = constrain(p0, 0, 100);
        potencias[1] = constrain(p1, 0, 100);
        potencias[2] = constrain(p2, 0, 100);
        potencias[3] = constrain(p3, 0, 100);
        ultimaComunicacionMs = millis();
      }
      rxPos = 0;
    } else if (c != '\r' && rxPos < sizeof(rxBuf) - 1) {
      rxBuf[rxPos++] = c;
    }
  }

  // --- 2. PERRO GUARDIÁN DE COMUNICACIÓN ---
  if (millis() - ultimaComunicacionMs > TIMEOUT_UART_MS) {
    for (int i = 0; i < NUM_CANALES; i++) {
      potencias[i] = 0;
    }
  }

  // --- 3. LÓGICA DE TIEMPO PROPORCIONAL ---
  // Divide el tiempo en ventanas de 3 segundos. Si la potencia es, por ejemplo,
  // 50%, el TRIAC estará encendido los primeros 1.5 segundos y apagado el resto.
  unsigned long ahora = millis();
  if (ahora - windowStart >= WINDOW_SIZE_MS) {
    windowStart = ahora; // Reiniciar ventana
  }

  unsigned long tiempoTranscurrido = ahora - windowStart;

  // --- 4. ENCENDER O APAGAR CADA CANAL SEGÚN SU PORCENTAJE ---
  for (int i = 0; i < NUM_CANALES; i++) {
    // Calcular cuántos milisegundos debe estar encendido en esta ventana
    unsigned long tiempoEncendido = (WINDOW_SIZE_MS * (unsigned long)potencias[i]) / 100;
    
    if (potencias[i] == 0) {
      dimmer.APC_OFF(GATE_PINS[i]);       // 0% → siempre apagado
    } 
    else if (tiempoTranscurrido < tiempoEncendido) {
      dimmer.APC_ON(GATE_PINS[i]);        // Dentro del tiempo encendido → ON
    } 
    else {
      dimmer.APC_OFF(GATE_PINS[i]);       // Fuera del tiempo encendido → OFF
    }
  }
}
