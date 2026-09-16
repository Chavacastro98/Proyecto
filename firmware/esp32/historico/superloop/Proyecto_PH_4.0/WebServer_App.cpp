#include "WebServer_App.h"
#include "Controller_System.h"
#include "Controller_Termico.h"
#include "Controller_Fuente.h"
#include "Controller_PH.h"
#include "config.h"

/**
 * =================================================================================
 * ENRUTADOR PRINCIPAL DEL SERVIDOR WEB — Versión 4.0 (WebServer_App.cpp)
 * =================================================================================
 * En la versión 4.0, este archivo pasa de un monolito de 1,557 líneas a un
 * enrutador maestro limpio y desacoplado de ~40 líneas que orquesta el registro
 * de las rutas de cada dominio funcional.
 * =================================================================================
 */

void inicializarWebServer() {
  Serial.println("[HTTP] Inicializando rutas modulares del servidor web...");

  // 1. Rutas de Sistema: Menú principal, datos meteorológicos y diagnóstico de sensores
  registrarRutasSystem();

  // 2. Rutas del Control Térmico: Lazos PI, setpoints y telemetría de 4 canales
  registrarRutasTermico();

  // 3. Rutas de la Fuente de Corriente: Sumidero VCSS, shunts duales, PWM y lazo cerrado
  registrarRutasFuente();

  // 4. Rutas del Módulo de pH 2.0: Monitoreo dual, calibración tri-modo y offset
  registrarRutasPH();

  // Poner en marcha el servidor HTTP en el puerto 80
  server.begin();
  Serial.println("[HTTP] Servidor Web Modular v4.0 en línea (Puerto 80).");
}
