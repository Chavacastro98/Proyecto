#ifndef MODULO_AMBIENTAL_H
#define MODULO_AMBIENTAL_H

/**
 * =================================================================================
 * MÓDULO DE MONITOREO AMBIENTAL (Modulo_Ambiental.h)
 * =================================================================================
 * Este módulo mide las condiciones del ambiente en el laboratorio usando dos
 * sensores conectados al bus I2C:
 *
 *   - AHT20  (dirección 0x38): Temperatura (°C) y Humedad Relativa (%)
 *   - BMP280 (dirección 0x76 o 0x77): Presión Atmosférica (hPa)
 *
 * Estos datos se muestran en la página principal de la interfaz web y son
 * útiles porque la humedad y la presión afectan la evaporación de las
 * soluciones electrolíticas y la convección térmica en las tinas.
 */

#include "config.h"
#include <Adafruit_AHTX0.h>
#include <Adafruit_BMP280.h>

// Objetos de los sensores ambientales (creados en Modulo_Ambiental.cpp)
extern Adafruit_AHTX0 aht;
extern Adafruit_BMP280 bmp;

/**
 * Inicializa los sensores AHT20 y BMP280, buscando en las direcciones I2C
 * posibles.
 * @return true si ambos sensores se encontraron correctamente, false si alguno
 * falló.
 */
bool inicializarModuloAmbiental();

/**
 * Lee los sensores ambientales y actualiza las variables amb_temp, amb_hum y
 * amb_pres. Se llama cada 5 segundos desde el bucle principal.
 */
void procesarLecturaAmbiental();

#endif // MODULO_AMBIENTAL_H