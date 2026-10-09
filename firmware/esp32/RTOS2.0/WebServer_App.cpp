/**
 * =================================================================================
 * ENRUTADOR PRINCIPAL DEL SERVIDOR WEB (WebServer_App.cpp) — RTOS 2.0
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * DESCRIPCIÓN DEL MÓDULO:
 * Ejecuta el registro en cascada de todos los endpoints HTTP REST JSON y OTA.
 * Despachado periódicamente en Core 0 por Task_Web.
 * =================================================================================
 */

#include "WebServer_App.h"
#include "Controller_System.h"
#include "Controller_Termico.h"
#include "Controller_Fuente.h"
#include "Controller_PH.h"
#include "Modulo_OTA.h"
#include "config.h"

/**
 * @brief Registra secuencialmente los grupos de rutas MVC e inicia el servicio HTTP (Puerto 80).
 */
void inicializarWebServer() {
  Serial.println("[HTTP] Inicializando rutas modulares del servidor web (RTOS 2.0)...");

  // 1. Rutas de Sistema, Menú, Diagnóstico de Sensores, Consola y Telemetría Unificada (/data_all)
  registrarRutasSystem();

  // 2. Rutas del Módulo de Control Térmico PI (4 Reactores)
  registrarRutasTermico();

  // 3. Rutas de la Salida de Corriente VCSS (Continua y Pulsada)
  registrarRutasFuente();

  // 4. Rutas del Módulo de Medición y Calibración de pH (Canal A1 Dedicado)
  registrarRutasPH();

  // 5. Rutas del Gestor de Actualizaciones de Firmware Inalámbrico (OTA)
  inicializarOTA();

  // Iniciar la escucha en el socket TCP puerto 80
  server.begin();
  Serial.println("[HTTP] Servidor Web HTTP RTOS 2.0 en línea (Puerto 80).");
}

