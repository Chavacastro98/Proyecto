/**
 * =================================================================================
 * CONTROL DE CORRIENTE CONTINUA (DC) VCSS (Modulo_Fuente_DC.h) — RTOS 1.4
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * Módulo especializado en la gestión de corriente continua:
 * - Rampa Soft-Start de 500 ms (cero sobreimpulso inductivo)
 * - Blanking analógico de 300 ms (estabilización rápida)
 * - Sensado analógico en shunts ADS1115 A2/A3 a 10 Hz
 * - Lazo PI adaptativo por zonas de error (estabilización en < 2.5s)
 * - Diagnóstico en tiempo real de salud de celda
 * =================================================================================
 */

#ifndef MODULO_FUENTE_DC_H
#define MODULO_FUENTE_DC_H

#include <Arduino.h>
#include "config.h"

/**
 * @brief Inicializa el módulo de corriente continua y resetea variables de estado.
 */
void inicializarFuenteDC();

/**
 * @brief Reinicia el lazo de control DC (integrador PI, marcas de tiempo y rampa).
 * Debe invocarse al encender la fuente en modo continuo.
 */
void resetLazoDC();

/**
 * @brief Ejecuta un ciclo de regulación de corriente continua (llamado a 10 Hz por Task_Fuente).
 * Lee shunts, evalúa salud de celda, ejecuta PI adaptativo y actualiza el DAC MCP4725.
 */
void ejecutarCicloFuenteDC();

/**
 * @brief Aplica un código digital directo al DAC MCP4725 bajo protección de mutex.
 * @param codigoDAC Código de 12 bits (0..4095).
 */
void escribirDAC_DC(uint16_t codigoDAC);

#endif // MODULO_FUENTE_DC_H
