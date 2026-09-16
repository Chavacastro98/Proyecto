#include "Controller_Termico.h"
#include "views/View_Termico.h"
#include "Modulo_Termico.h"
#include "config.h"

/**
 * =================================================================================
 * IMPLEMENTACIÓN: CONTROLADOR TÉRMICO (Controller_Termico.cpp) — Versión 4.0
 * =================================================================================
 */

// Handler de la página HTML del control térmico
static void handleTermico() {
  server.send_P(200, "text/html", HTML_TERMICO);
}

// Handler de telemetría de los 4 canales térmicos (JSON)
static void handleDataT() {
  char json[256];
  int offset = 0;
  offset += snprintf(json + offset, sizeof(json) - offset, "[");

  for (int i = 0; i < 4; i++) {
    portENTER_CRITICAL(&muxTermico);
    float temp = canales[i].temperatura;
    float sp = canales[i].setpoint;
    bool act = canales[i].activo;
    int pot = canales[i].potenciaActual;
    portEXIT_CRITICAL(&muxTermico);

    offset += snprintf(json + offset, sizeof(json) - offset,
                       "{\"t\":%.1f,\"sp\":%.1f,\"p\":%d,\"run\":%d}%s",
                       temp, sp, pot, act ? 1 : 0, (i < 3) ? "," : "");
  }
  snprintf(json + offset, sizeof(json) - offset, "]");
  server.send(200, "application/json", json);
}

// Handler para modificar la temperatura objetivo (Setpoint)
// Parámetros: ?id=0..3 y ?v=temperatura (0-150°C)
static void handleSetT() {
  if (!server.hasArg("id") || !server.hasArg("v")) {
    server.send(400, "text/plain", "Parámetros faltantes");
    return;
  }
  int id = server.arg("id").toInt();
  if (id >= 0 && id < 4) {
    portENTER_CRITICAL(&muxTermico);
    bool canalActivo = canales[id].activo;
    portEXIT_CRITICAL(&muxTermico);

    if (!canalActivo) {
      float nuevoSP = server.arg("v").toFloat();

      if (isnan(nuevoSP) || nuevoSP < 0.0f || nuevoSP > 150.0f) {
        server.send(400, "text/plain", "Setpoint fuera de rango (0-150°C)");
        return;
      }

      portENTER_CRITICAL(&muxTermico);
      canales[id].setpoint = nuevoSP;
      portEXIT_CRITICAL(&muxTermico);

      char key[16];
      snprintf(key, sizeof(key), "sp%d", id);
      memoria.putFloat(key, nuevoSP);
      server.send(200, "text/plain", "OK");
    } else {
      server.send(403, "text/plain", "Bloqueado - Canal Activo");
    }
  } else {
    server.send(400, "text/plain", "Error de ID");
  }
}

// Handler para encender o apagar el control térmico de todos los canales
static void handleActT() {
  if (!server.hasArg("run")) {
    server.send(400, "text/plain", "Parámetro run faltante");
    return;
  }
  bool estado = (server.arg("run") == "1");

  if (estado) {
    portENTER_CRITICAL(&muxPH);
    bool phOn = phModuloActivo;
    portEXIT_CRITICAL(&muxPH);
    if (phOn) {
      server.send(403, "text/plain", "Interlock: modulo pH activo. Apaguelo primero.");
      return;
    }
  }

  portENTER_CRITICAL(&muxTermico);
  for (int i = 0; i < 4; i++) {
    canales[i].activo = estado;
    if (!estado) {
      canales[i].limitePotencia = 0.0;
      canales[i].integral = 0.0;
    }
  }
  portEXIT_CRITICAL(&muxTermico);

  server.send(200, "text/plain", "OK");
}

void registrarRutasTermico() {
  server.on("/termico", handleTermico);
  server.on("/data_t", handleDataT);
  server.on("/set_t", handleSetT);
  server.on("/act_t", handleActT);
}
