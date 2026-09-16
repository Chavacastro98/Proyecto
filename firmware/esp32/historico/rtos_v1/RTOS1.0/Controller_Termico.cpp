/**
 * =================================================================================
 * CONTROLADOR: CONTROL TÉRMICO PI (Controller_Termico.cpp) — RTOS 1.0
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * DESCRIPCIÓN DEL MÓDULO:
 * Procesa las peticiones HTTP del subsistema térmico. Garantiza que las modificaciones
 * de setpoint solo puedan realizarse cuando los canales están inactivos para prevenir
 * saltos abruptos de consigna con calentadores energizados.
 * =================================================================================
 */

#include "Controller_Termico.h"
#include "views/View_Termico.h"
#include "Modulo_Termico.h"
#include "RTOS_Core.h"
#include "config.h"

/**
 * @brief Entrega la vista web HTML de control térmico (HTML_TERMICO).
 */
static void handleTermico() {
  server.send_P(200, "text/html", HTML_TERMICO);
}

/**
 * @brief Endpoint JSON que entrega la matriz de telemetría de los 4 canales:
 * temperatura medida, setpoint consignado, potencia aplicada (0..100%) y estado (activo/inactivo).
 */
static void handleDataT() {
  char json[256];
  int offset = 0;
  offset += snprintf(json + offset, sizeof(json) - offset, "[");

  for (int i = 0; i < 4; i++) {
    float temp = 0.0f, sp = 0.0f;
    bool act = false;
    int pot = 0;

    if (takeDataMutex(pdMS_TO_TICKS(20))) {
      temp = canales[i].temperatura;
      sp = canales[i].setpoint;
      act = canales[i].activo;
      pot = canales[i].potenciaActual;
      giveDataMutex();
    }

    offset += snprintf(json + offset, sizeof(json) - offset,
                       "{\"t\":%.1f,\"sp\":%.1f,\"p\":%d,\"run\":%d}%s",
                       temp, sp, pot, act ? 1 : 0, (i < 3) ? "," : "");
  }
  snprintf(json + offset, sizeof(json) - offset, "]");
  server.send(200, "application/json", json);
}

/**
 * @brief Modifica la consigna de temperatura de una tina específica.
 * Por seguridad industrial, el canal DEBE estar inactivo para aceptar el cambio.
 */
static void handleSetT() {
  if (!server.hasArg("id") || !server.hasArg("v")) {
    server.send(400, "text/plain", "Parámetros faltantes");
    return;
  }
  int id = server.arg("id").toInt();
  if (id >= 0 && id < 4) {
    bool canalActivo = false;
    if (takeDataMutex(pdMS_TO_TICKS(20))) {
      canalActivo = canales[id].activo;
      giveDataMutex();
    }

    if (!canalActivo) {
      float nuevoSP = server.arg("v").toFloat();

      if (isnan(nuevoSP) || nuevoSP < 0.0f || nuevoSP > 150.0f) {
        server.send(400, "text/plain", "Setpoint fuera de rango (0-150°C)");
        return;
      }

      if (takeDataMutex(pdMS_TO_TICKS(20))) {
        canales[id].setpoint = nuevoSP;
        giveDataMutex();
      }

      char key[16];
      snprintf(key, sizeof(key), "sp%d", id);
      memoria.putFloat(key, nuevoSP);
      const char* nombT[] = {"Limpieza", "Decapado", "Celda Hull", "Niquelado"};
      logSistema(LOG_LVL_INFO, "TERMICO", "Canal %d (%s) SP modificado a %.1f C", id, nombT[id], nuevoSP);
      server.send(200, "text/plain", "OK");
    } else {
      server.send(403, "text/plain", "Bloqueado - Canal Activo");
    }
  } else {
    server.send(400, "text/plain", "Error de ID");
  }
}

/**
 * @brief Conmuta el estado global de los 4 canales de calentamiento.
 * Al apagar el sistema, reinicia a 0 el límite de rampa y el acumulador integral.
 */
static void handleActT() {
  if (!server.hasArg("run")) {
    server.send(400, "text/plain", "Parámetro run faltante");
    return;
  }
  bool estado = (server.arg("run") == "1");

  if (estado) {
    if (g_failsafe_latched) {
      server.send(403, "text/plain", "Bloqueado: Sistema en alarma FAIL-SAFE");
      return;
    }

    bool phOn = false;
    if (takeDataMutex(pdMS_TO_TICKS(20))) {
      phOn = phModuloActivo;
      giveDataMutex();
    }

    if (phOn) {
      server.send(403, "text/plain", "Interlock: modulo pH activo. Apaguelo primero.");
      return;
    }
  }

  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    for (int i = 0; i < 4; i++) {
      canales[i].activo = estado;
      if (!estado) {
        canales[i].limitePotencia = 0.0f;
        canales[i].integral = 0.0f;
      }
    }
    giveDataMutex();
  }

  if (estado) {
    logSistema(LOG_LVL_INFO, "TERMICO", "Sistema termico ENCENDIDO");
  } else {
    logSistema(LOG_LVL_INFO, "TERMICO", "Sistema termico APAGADO por operador");
  }

  server.send(200, "text/plain", "OK");
}

/**
 * @brief Registra formalmente las rutas de control térmico en el servidor HTTP.
 */
void registrarRutasTermico() {
  server.on("/termico", handleTermico);
  server.on("/data_t", handleDataT);
  server.on("/set_t", handleSetT);
  server.on("/act_t", handleActT);
}

