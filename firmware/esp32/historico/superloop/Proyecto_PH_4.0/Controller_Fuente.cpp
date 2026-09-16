#include "Controller_Fuente.h"
#include "views/View_Fuente.h"
#include "Modulo_Fuentes.h"
#include "config.h"

/**
 * =================================================================================
 * IMPLEMENTACIÓN: CONTROLADOR DE FUENTE VCSS (Controller_Fuente.cpp) — Versión 4.0
 * =================================================================================
 */

// Handler de la página HTML de la fuente de corriente
static void handleFuente() {
  server.send_P(200, "text/html", HTML_FUENTE);
}

// Handler de telemetría completa de la fuente VCSS (JSON)
static void handleDataF() {
  char json[288];
  portENTER_CRITICAL(&muxFuente);
  bool act = fuenteActiva;
  bool modo = modoPulsado;
  int amp = amplitudDAC;
  int sp = amplitudDAC_Setpoint;
  int freq = frecuencia;
  int duty = dutyCycle;
  float i_real = corrienteTotalReal;
  float i1 = corrienteReal_R1;
  float i2 = corrienteReal_R2;
  float vs1 = voltajeShunt1_raw;
  float vs2 = voltajeShunt2_raw;
  float gm = factorGananciaVCSS;
  bool comp = compensacionLazoCerrado;
  bool rele = estadoReleVDD;
  portEXIT_CRITICAL(&muxFuente);

  float amps = (sp / 4095.0f) * 6.6f;
  snprintf(json, sizeof(json),
           "{\"act\":%d,\"modo\":%d,\"amp\":%d,\"sp\":%d,\"freq\":%d,\"duty\":%d,"
           "\"amps\":%.2f,\"i_real\":%.2f,\"i1\":%.2f,\"i2\":%.2f,"
           "\"vs1\":%.3f,\"vs2\":%.3f,\"gm\":%.4f,\"comp\":%d,\"rele\":%d}",
           act ? 1 : 0, modo ? 1 : 0, amp, sp, freq, duty, amps,
           i_real, i1, i2, vs1, vs2, gm, comp ? 1 : 0, rele ? 1 : 0);
  server.send(200, "application/json", json);
}

// Handler para modificar parámetros de la fuente (?p=a/f/d&v=valor)
static void handleSetF() {
  if (!server.hasArg("p") || server.arg("p").length() == 0 || !server.hasArg("v")) {
    server.send(400, "text/plain", "Parámetros insuficientes");
    return;
  }

  char parametro = server.arg("p")[0];
  int valor = server.arg("v").toInt();

  portENTER_CRITICAL(&muxFuente);
  if (parametro == 'a') {
    amplitudDAC_Setpoint = constrain(valor, 0, 4095); // Consigna deseada
    amplitudDAC = amplitudDAC_Setpoint;
    memoria.putInt("dac_amp", amplitudDAC_Setpoint);
  } else if (parametro == 'f') {
    frecuencia = constrain(valor, 1, 100); // 1-100 Hz
    memoria.putInt("dac_freq", frecuencia);
  } else if (parametro == 'd') {
    dutyCycle = constrain(valor, 0, 100); // 0-100 %
    memoria.putInt("dac_duty", dutyCycle);
  }
  portEXIT_CRITICAL(&muxFuente);

  server.send(200, "text/plain", "OK");
}

// Handler para cambiar entre corriente continua y pulsada (?v=0 o 1)
static void handleModoF() {
  if (!server.hasArg("v")) {
    server.send(400, "text/plain", "Parámetro v faltante");
    return;
  }
  bool usarPulsado = (server.arg("v") == "1");

  portENTER_CRITICAL(&muxFuente);
  modoPulsado = usarPulsado;
  amplitudDAC = amplitudDAC_Setpoint; // Restaurar setpoint base
  memoria.putBool("dac_modo", usarPulsado);
  portEXIT_CRITICAL(&muxFuente);

  server.send(200, "text/plain", "OK");
}

// Handler para activar/desactivar la compensación de lazo cerrado (?v=0 o 1)
static void handleSetCompF() {
  if (!server.hasArg("v")) {
    server.send(400, "text/plain", "Parámetro v faltante");
    return;
  }
  bool habilitar = (server.arg("v") == "1");
  setCompensacionLazoCerrado(habilitar);
  server.send(200, "text/plain", "OK");
}

// Handler para auto-calibrar transconductancia con carga de prueba (1.50 A)
static void handleCalVCSS() {
  bool ok = autoCalibrarVCSS();
  char json[96];
  snprintf(json, sizeof(json), "{\"ok\":%d,\"gm\":%.4f}", ok ? 1 : 0, factorGananciaVCSS);
  server.send(200, "application/json", json);
}

// Handler para encender o apagar la salida de corriente con ZCS e interlock
static void handleActF() {
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

  setEstadoFuente(estado);
  server.send(200, "text/plain", "OK");
}

void registrarRutasFuente() {
  server.on("/fuente", handleFuente);
  server.on("/data_f", handleDataF);
  server.on("/set_f", handleSetF);
  server.on("/modo_f", handleModoF);
  server.on("/set_comp_f", handleSetCompF);
  server.on("/cal_vcss", handleCalVCSS);
  server.on("/act_f", handleActF);
}
