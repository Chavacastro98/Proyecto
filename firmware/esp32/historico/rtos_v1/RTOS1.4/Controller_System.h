#ifndef CONTROLLER_SYSTEM_H
#define CONTROLLER_SYSTEM_H

/**
 * =================================================================================
 * CONTROLADOR: SISTEMA, AMBIENTE Y DIAGNÓSTICO (Controller_System.h) — RTOS 1.0
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * ENDPOINTS DESPACHADOS:
 * - GET `/`: Menú principal (HTML_MENU).
 * - GET `/sensores`: Diagnóstico de hardware en tiempo real (HTML_SENSORES).
 * - GET `/consola`: Visor de eventos y registros del sistema (HTML_CONSOLA).
 * - GET `/logs`: Flujo JSON de eventos en RAM (`obtenerLogsJSON`).
 * - GET `/data_env`: Telemetría ambiental (AHT20/BMP280) y estado Fail-Safe.
 * - GET `/data_all`: Endpoint unificado SCADA (reduce tráfico HTTP en 75%).
 * - GET `/data_sensors`: Sondeo I2C/SPI de periféricos conectados.
 * - POST `/failsafe_reset`: Restablecimiento de enclavamiento por el operador.
 * =================================================================================
 */

#include "config.h"

/**
 * @brief Registra las rutas de sistema, vistas generales y telemetría global en el servidor HTTP.
 */
void registrarRutasSystem();

#endif // CONTROLLER_SYSTEM_H

