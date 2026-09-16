#include "Modulo_Ambiental.h"
#include "config.h"

/**
 * =================================================================================
 * IMPLEMENTACIÓN DEL MÓDULO AMBIENTAL (Modulo_Ambiental.cpp) — Versión 4.0
 * =================================================================================
 */

// Banderas globales para conocer si los sensores arrancaron bien
bool ahtInicializado = false;
bool bmpInicializado = false;

// Creación de los objetos que manejan la comunicación con los sensores
Adafruit_AHTX0 aht;
Adafruit_BMP280 bmp;

/**
 * Inicializa los sensores de temperatura/humedad (AHT20) y presión (BMP280).
 */
bool inicializarModuloAmbiental() {
  // Inicialización del sensor AHT20 en la dirección I2C estándar (0x38)
  if (!aht.begin(&Wire)) {
    Serial.println("[AMBIENTAL] ❌ Error: Sensor AHT20 no detectado en bus I2C (0x38).");
    ahtInicializado = false;
  } else {
    Serial.println("[AMBIENTAL] Sensor AHT20 (Temp/Humedad) en línea.");
    ahtInicializado = true;
  }

  // Inicialización del sensor BMP280 buscando en 0x76 y 0x77
  if (!bmp.begin(0x76, BMP280_CHIPID)) {
    if (!bmp.begin(0x77, BMP280_CHIPID)) {
      Serial.println("[AMBIENTAL] ❌ Error: Sensor BMP280 no detectado en direcciones 0x76 ni 0x77.");
      bmpInicializado = false;
    } else {
      Serial.println("[AMBIENTAL] Sensor BMP280 (Presión) en línea en dirección 0x77.");
      bmpInicializado = true;
    }
  } else {
    Serial.println("[AMBIENTAL] Sensor BMP280 (Presión) en línea en dirección 0x76.");
    bmpInicializado = true;
  }

  return (ahtInicializado && bmpInicializado);
}

/**
 * Lee los datos de los sensores y actualiza las variables globales.
 */
void procesarLecturaAmbiental() {
  if (ahtInicializado) {
    sensors_event_t hum, temp;
    aht.getEvent(&hum, &temp);
    amb_temp = temp.temperature;
    amb_hum = hum.relative_humidity;
  }

  if (bmpInicializado) {
    amb_pres = bmp.readPressure() / 100.0f; // Pa a hPa
  }
}
