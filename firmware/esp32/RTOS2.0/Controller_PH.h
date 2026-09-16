#ifndef CONTROLLER_PH_H
#define CONTROLLER_PH_H

/**
 * =================================================================================
 * CONTROLADOR: MEDICIÓN Y CALIBRACIÓN DE PH DEDICADO (Controller_PH.h) — RTOS 2.0
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * ENDPOINTS DESPACHADOS (RTOS 2.0):
 * - GET  `/ph`: Vista HTML de monitoreo, calibración y puntos NVS del sensor dedicado (HTML_PH).
 * - GET  `/get_ph`: Telemetría del sensor dedicado de pH, pendientes Nernst y puntos NVS por modo.
 * - GET  `/get_ph_dual`: Alias retrocompatible que entrega los datos del sensor dedicado.
 * - GET  `/data_ph_raw`: Lectura de tensión directa sin procesar para ajuste de offset en corto (A1).
 * - POST `/act_ph`: Habilitación / Apagado de la adquisición de pH con verificación de interlock.
 * - POST `/set_cal_mode`: Selección del modelo de calibración (0: Teórico, 1: 2 Puntos, 2: 3 Puntos).
 * - POST `/do_cal_ph`: Registro de punto de tampón estándar (pH 4, 7 o 10) y cálculo de pendientes.
 * - POST `/reset_cal_ph`: Restablecimiento de calibración a valores de fábrica en Flash NVS.
 * =================================================================================
 */

#include "config.h"

/**
 * @brief Registra los endpoints del módulo de pH dedicado en el servidor HTTP.
 */
void registrarRutasPH();

#endif // CONTROLLER_PH_H
