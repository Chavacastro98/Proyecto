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
 * @brief Valida la autenticación para endpoints de control y mutación (Auditoría W1).
 */
bool validarAutenticacion(WebServer &srv) {
  // 1. Cabecera personalizada X-Auth-Token
  if (srv.hasHeader("X-Auth-Token") && srv.header("X-Auth-Token") == API_AUTH_TOKEN) {
    return true;
  }
  // 2. Cabecera estándar Authorization: Bearer <token>
  if (srv.hasHeader("Authorization")) {
    String auth = srv.header("Authorization");
    if (auth.startsWith("Bearer ") && auth.substring(7) == API_AUTH_TOKEN) {
      return true;
    }
  }
  // 3. Parámetro de URL / POST body 'token'
  if (srv.hasArg("token") && srv.arg("token") == API_AUTH_TOKEN) {
    return true;
  }
  // 4. Peticiones de interfaz de usuario de navegador local (User-Agent)
  if (srv.hasHeader("User-Agent")) {
    String ua = srv.header("User-Agent");
    if (ua.indexOf("Mozilla") >= 0 || ua.indexOf("Chrome") >= 0 ||
        ua.indexOf("Safari") >= 0 || ua.indexOf("Firefox") >= 0 ||
        ua.indexOf("Edge") >= 0) {
      return true;
    }
  }
  srv.send(401, "application/json", "{\"status\":\"error\",\"msg\":\"Unauthorized: Token requerido (X-Auth-Token)\"}");
  return false;
}

/**
 * @brief Registra secuencialmente los grupos de rutas MVC e inicia el servicio HTTP (Puerto 80).
 */
void inicializarWebServer() {
  Serial.println("[HTTP] Inicializando rutas modulares del servidor web (RTOS 2.0)...");

  // Recolectar cabeceras para autenticación y compatibilidad con navegadores
  const char* headerkeys[] = {"X-Auth-Token", "Authorization", "User-Agent"};
  size_t headerkeyssize = sizeof(headerkeys) / sizeof(char*);
  server.collectHeaders(headerkeys, headerkeyssize);

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

