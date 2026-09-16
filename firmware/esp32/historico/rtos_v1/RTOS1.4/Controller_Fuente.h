#ifndef CONTROLLER_FUENTE_H
#define CONTROLLER_FUENTE_H

/**
 * =================================================================================
 * CONTROLADOR: SALIDA DE CORRIENTE VCSS (Controller_Fuente.h) — RTOS 1.0
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * ENDPOINTS DESPACHADOS:
 * - GET  `/fuente`: Vista de control de la salida de corriente (HTML_FUENTE).
 * - GET  `/data_f`: Telemetría de la fuente (amplitud, frecuencia, corriente medida en shunts, ganancia Gm).
 * - POST `/set_f`: Modificación de parámetros ('a': amplitud DAC, 'f': frecuencia Hz, 'd': duty cycle %).
 * - POST `/modo_f`: Conmutación entre modo Continuo (DC) y Pulsado.
 * - POST `/set_comp_f`: Habilitación del lazo cerrado de compensación automática de ganancia.
 * - POST `/cal_vcss`: Ejecución del protocolo automático de calibración con 1.50 A patrón.
 * - POST `/reset_cal_vcss`: Restablecimiento de la ganancia Gm a nominal (2.000 S, Factor 1.0000x).
 * - POST `/act_f`: Encendido / Apagado seguro de la fuente bajo protocolo ZCS e interlock de pH.
 * =================================================================================
 */

#include "config.h"

/**
 * @brief Registra todos los endpoints de control y telemetría de la salida de corriente VCSS.
 */
void registrarRutasFuente();

#endif // CONTROLLER_FUENTE_H

