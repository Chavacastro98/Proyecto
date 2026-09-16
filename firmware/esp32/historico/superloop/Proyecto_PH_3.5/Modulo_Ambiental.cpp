#include "Modulo_Ambiental.h"
#include "config.h"
#include <Arduino.h>

/**
 * =================================================================================
 * IMPLEMENTACIÓN DEL MÓDULO AMBIENTAL (Modulo_Ambiental.cpp)
 * =================================================================================
 * Implementa la inicialización y lectura periódica de los sensores de
 * temperatura ambiente (AHT20), humedad relativa (AHT20) y presión atmosférica
 * (BMP280).
 * =================================================================================
 */

// Objetos de las librerías Adafruit para los sensores ambientales
Adafruit_AHTX0 aht;
Adafruit_BMP280 bmp;

// Banderas que indican si cada sensor se encontró correctamente al arrancar
// v3.1: Ahora visibles externamente (extern en Modulo_Ambiental.h) para diagnóstico
bool ahtInicializado = false;
bool bmpInicializado = false;

/**
 * Busca los sensores AHT20 y BMP280 en el bus I2C.
 * El BMP280 puede tener dirección 0x77 o 0x76 (depende de cómo está soldado
 * el pin SDO en la placa), así que se prueban ambas direcciones.
 *
 * @return true si ambos sensores se encontraron, false si alguno falló
 */
bool inicializarModuloAmbiental() {
  Serial.println("[AMBIENTAL] Inicializando sensores I2C (AHT20 + BMP280)...");

  // Buscar sensor AHT20 (siempre en dirección 0x38)
  ahtInicializado = aht.begin();
  if (!ahtInicializado) {
    Serial.println(
        "[AMBIENTAL] ❌ Error: Sensor AHT20 no detectado en dirección 0x38.");
  } else {
    Serial.println("[AMBIENTAL] Sensor AHT20 (Humedad/Temp) en línea.");
  }

  // Buscar sensor BMP280 (probar primero 0x77, luego 0x76)
  bmpInicializado = bmp.begin(0x77);
  if (!bmpInicializado) {
    bmpInicializado = bmp.begin(0x76);
    if (!bmpInicializado) {
      Serial.println("[AMBIENTAL] ❌ Error: Sensor BMP280 no detectado en 0x77 "
                     "ni en 0x76.");
    } else {
      Serial.println(
          "[AMBIENTAL] Sensor BMP280 (Presión) en línea en dirección 0x76.");
    }
  } else {
    Serial.println(
        "[AMBIENTAL] Sensor BMP280 (Presión) en línea en dirección 0x77.");
  }

  return ahtInicializado && bmpInicializado;
}

/**
 * Lee los sensores y actualiza las variables globales de ambiente.
 * Solo lee un sensor si fue inicializado correctamente para no colgar el bus
 * I2C.
 */
void procesarLecturaAmbiental() {
  if (ahtInicializado) {
    sensors_event_t humidity, temp;
    aht.getEvent(&humidity, &temp);
    amb_temp = temp.temperature;
    amb_hum = humidity.relative_humidity;
  }

  if (bmpInicializado) {
    // BMP280 devuelve presión en Pascales; dividir entre 100 para obtener
    // Hectopascales (hPa)
    amb_pres = bmp.readPressure() / 100.0f;
  }
}