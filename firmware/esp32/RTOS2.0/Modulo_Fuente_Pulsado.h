/**
 * =================================================================================
 * CONTROL DE CORRIENTE PULSADA VCSS (Modulo_Fuente_Pulsado.h) — RTOS 1.4
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * Módulo especializado en modulación pulsada de alta precisión:
 * - Generador de onda cuadrada de 1 a 100 Hz con ciclo de trabajo configurable (0..100%)
 * - Amplitud directa fijada al setpoint calibrado (cero interferencia de rampa o integrador PI)
 * - Muestreo estroboscópico ETS (Equivalent Time Sampling) en 16 puntos
 * - Diagnóstico dinámico de impedancia y balance de ramas
 * =================================================================================
 */

#ifndef MODULO_FUENTE_PULSADO_H
#define MODULO_FUENTE_PULSADO_H

#include <Arduino.h>
#include "config.h"

/**
 * @brief Inicializa variables del módulo de pulsado.
 */
void inicializarFuentePulsada();

/**
 * @brief Resetea índices estroboscópicos y contadores de pulso.
 */
void resetLazoPulsado();

/**
 * @brief Ejecuta un ciclo completo de pulso (flanco alto, ETS y flanco bajo).
 * Llamado por Task_Fuente cuando la fuente está en modo pulsado.
 */
void ejecutarCicloFuentePulsada();

/**
 * @brief Actualiza la telemetría estimada cuando el ancho de pulso es menor a 5 ms.
 */
void actualizarTelemetriaPulsadaEstimada();

#endif // MODULO_FUENTE_PULSADO_H
