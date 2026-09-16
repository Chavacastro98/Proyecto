#ifndef WEBSERVER_APP_H
#define WEBSERVER_APP_H

/**
 * =================================================================================
 * ENRUTADOR PRINCIPAL DEL SERVIDOR WEB (WebServer_App.h) — RTOS 1.0
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * ARQUITECTURA MODULAR MVC:
 * Centraliza la inicialización de todas las rutas HTTP delegando el registro de
 * endpoints a sus controladores temáticos correspondientes:
 * - Controller_System: Vistas maestras, telemetría unificada (`/data_all`) y reset Fail-Safe.
 * - Controller_Termico: Interfaz térmica, consignas de temperatura y activación de lazos PI.
 * - Controller_Fuente: Interfaz de salida de corriente VCSS, consignas, pulsado y calibración.
 * - Controller_PH: Interfaz de pH dual 2.0, modos de calibración y lecturas de buffer.
 * - Modulo_OTA: Carga inalámbrica de firmware.
 * =================================================================================
 */

#include "config.h"

/**
 * @brief Registra todas las rutas HTTP modulares e inicia la escucha del servidor en el puerto 80.
 */
void inicializarWebServer();

#endif // WEBSERVER_APP_H

