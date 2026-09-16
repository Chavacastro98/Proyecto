/**
 * =================================================================================
 * ENRUTADOR PRINCIPAL DEL SERVIDOR WEB (WebServer_App.cpp) — RTOS 1.0
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * DESCRIPCIÓN DEL MÓDULO:
 * Ejecuta el registro en cascada de todos los endpoints HTTP.
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
  Serial.println("[HTTP] Inicializando rutas modulares del servidor web (RTOS)...");

  // 1. Rutas de Sistema, Menú, Diagnóstico de Sensores y Consola
  registrarRutasSystem();

  // 2. Rutas del Módulo de Control Térmico PI (4 Reactores)
  registrarRutasTermico();

  // 3. Rutas de la Salida de Corriente VCSS (Continua y Pulsada)
  registrarRutasFuente();

  // 4. Rutas del Módulo de Medición y Calibración de pH Dual
  registrarRutasPH();

  // 5. Rutas del Gestor de Actualizaciones de Firmware Inalámbrico (OTA)
  inicializarOTA();

  // Iniciar la escucha en el socket TCP puerto 80
  server.begin();
  Serial.println("[HTTP] Servidor Web HTTP v1.0 RTOS en línea (Puerto 80).");
}

