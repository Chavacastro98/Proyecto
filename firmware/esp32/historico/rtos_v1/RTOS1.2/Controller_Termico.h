#ifndef CONTROLLER_TERMICO_H
#define CONTROLLER_TERMICO_H

/**
 * =================================================================================
 * CONTROLADOR: CONTROL TÉRMICO PI (Controller_Termico.h) — RTOS 1.0
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * ENDPOINTS DESPACHADOS:
 * - GET  `/termico`: Vista HTML de supervisión térmica (HTML_TERMICO).
 * - GET  `/data_t`: Telemetría térmica de los 4 canales (T actual, setpoint, potencia, estado).
 * - POST `/set_t`: Modificación de consigna de temperatura (0..150 °C) en canal inactivo.
 * - POST `/act_t`: Encendido / Apagado global del sistema térmico con verificación de interlock.
 * =================================================================================
 */

#include "config.h"

/**
 * @brief Registra los endpoints de control y telemetría térmica en el servidor HTTP.
 */
void registrarRutasTermico();

#endif // CONTROLLER_TERMICO_H

