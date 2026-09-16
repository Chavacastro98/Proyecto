#ifndef CONTROLLER_PH_H
#define CONTROLLER_PH_H

/**
 * =================================================================================
 * CONTROLADOR: MEDICIÓN Y CALIBRACIÓN DE PH DUAL (Controller_PH.h) — RTOS 1.0
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * ENDPOINTS DESPACHADOS:
 * - GET  `/ph`: Vista HTML de monitoreo y calibración de pH dual (HTML_PH).
 * - GET  `/get_ph_dual`: Telemetría de pH de ambas tinas, pendientes Nernst y estado de calibración.
 * - GET  `/data_ph_raw`: Lectura de tensión directa sin procesar para diagnóstico del electrodo.
 * - POST `/act_ph`: Habilitación / Apagado de la adquisición de pH con verificación de interlock.
 * - POST `/set_cal_mode`: Selección del modelo de calibración (0: Teórico, 1: 2 Puntos, 2: 3 Puntos).
 * - POST `/do_cal_ph`: Registro de punto de tampón estándar (pH 4, 7 o 10) y cálculo de pendientes.
 * =================================================================================
 */

#include "config.h"

/**
 * @brief Registra los endpoints del módulo de pH dual en el servidor HTTP.
 */
void registrarRutasPH();

#endif // CONTROLLER_PH_H

