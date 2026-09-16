/**
 * =================================================================================
 * CONTROLADOR: SALIDA DE CORRIENTE VCSS (Controller_Fuente.cpp) — RTOS 1.0
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * DESCRIPCIÓN DEL MÓDULO:
 * Procesa las peticiones HTTP relativas al sumidero de corriente VCSS (Voltage-Controlled
 * Current Sink). Aplica validación de rangos, persistencia diferida en Flash NVS
 * y verificación de interlocks antes de conmutar relés o modificar el DAC.
 * =================================================================================
 */

#include "Controller_Fuente.h"
#include "views/View_Fuente.h"
#include "Modulo_Fuentes.h"
#include "RTOS_Core.h"
#include "config.h"

/**
 * @brief Entrega la vista web HTML de control de la salida de corriente (HTML_FUENTE).
 */
static void handleFuente() {
  server.send_P(200, "text/html", HTML_FUENTE);
}

/**
 * @brief Endpoint JSON que entrega el estado instantáneo de la salida de corriente:
 * estado operativo, modo (DC/Pulsado), consignas, lecturas de shunts y ganancia Gm.
 */
static void handleDataF() {
  char json[512];
  bool act = false, modo = false, comp = false, rele = false;
  int amp = 0, sp = 0, freq = 1, duty = 50;
  float i_real = 0.0f, i1 = 0.0f, i2 = 0.0f, vs1 = 0.0f, vs2 = 0.0f, gm = 1.0f;
  uint8_t pi_st = 0, salud = 0;
  float wave[ETS_NUM_PUNTOS];

  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    act = fuenteActiva;
    modo = modoPulsado;
    amp = amplitudDAC;
    sp = amplitudDAC_Setpoint;
    freq = frecuencia;
    duty = dutyCycle;
    i_real = corrienteTotalReal;
    i1 = corrienteReal_R1;
    i2 = corrienteReal_R2;
    vs1 = voltajeShunt1_raw;
    vs2 = voltajeShunt2_raw;
    gm = factorGananciaVCSS;
    comp = compensacionLazoCerrado;
    rele = estadoReleVDD;
    pi_st = estadoPICorriente;
    salud = estadoSaludCelda;
    for (int i = 0; i < ETS_NUM_PUNTOS; i++) {
      wave[i] = s_ondaETS[i];
    }
    giveDataMutex();
  }

  float amps = (sp / 4095.0f) * VCSS_IMAX_NOMINAL;
  int n = snprintf(json, sizeof(json),
           "{\"act\":%d,\"modo\":%d,\"amp\":%d,\"sp\":%d,\"freq\":%d,\"duty\":%d,"
           "\"amps\":%.2f,\"i_real\":%.2f,\"i1\":%.2f,\"i2\":%.2f,"
           "\"vs1\":%.3f,\"vs2\":%.3f,\"gm\":%.4f,\"comp\":%d,\"rele\":%d,"
           "\"pi_st\":%d,\"salud\":%d,\"wave\":[",
           act ? 1 : 0, modo ? 1 : 0, amp, sp, freq, duty, amps,
           i_real, i1, i2, vs1, vs2, gm, comp ? 1 : 0, rele ? 1 : 0,
           pi_st, salud);

  for (int i = 0; i < ETS_NUM_PUNTOS && n < (int)sizeof(json) - 10; i++) {
    n += snprintf(json + n, sizeof(json) - n, (i == 0) ? "%.2f" : ",%.2f", wave[i]);
  }
  if (n < (int)sizeof(json) - 2) {
    json[n++] = ']';
    json[n++] = '}';
    json[n] = '\0';
  }
  server.send(200, "application/json", json);
}

/**
 * @brief Modifica consignas de amplitud ('a'), frecuencia ('f') o duty cycle ('d').
 * La escritura en Flash NVS se realiza fuera del mutex para no retener la sección crítica.
 */
static void handleSetF() {
  if (!server.hasArg("p") || server.arg("p").length() == 0 || !server.hasArg("v")) {
    server.send(400, "text/plain", "Parámetros insuficientes");
    return;
  }

  char parametro = server.arg("p")[0];
  int valor = server.arg("v").toInt();

  int nvsVal = 0;
  const char* nvsKey = NULL;

  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    if (parametro == 'a') {
      amplitudDAC_Setpoint = constrain(valor, 0, 4095);
      float factor = (factorGananciaVCSS > 0.5f && factorGananciaVCSS < 1.5f) ? factorGananciaVCSS : 1.0f;
      amplitudDAC = constrain((int)roundf(amplitudDAC_Setpoint / factor), 0, 4095);
      nvsVal = amplitudDAC_Setpoint;
      nvsKey = "dac_amp";
    } else if (parametro == 'f') {
      frecuencia = constrain(valor, 1, 100);
      nvsVal = frecuencia;
      nvsKey = "dac_freq";
    } else if (parametro == 'd') {
      dutyCycle = constrain(valor, 0, 100);
      nvsVal = dutyCycle;
      nvsKey = "dac_duty";
    }
    giveDataMutex();
  }

  // Persistencia NVS fuera del mutex (evita contención de Flash durante la sección crítica)
  if (nvsKey != NULL) {
    memoria.putInt(nvsKey, nvsVal);
    if (parametro == 'a') {
      float ampsTarget = (valor / 4095.0f) * VCSS_IMAX_NOMINAL;
      logSistema(LOG_LVL_INFO, "FUENTE", "Consigna VCSS ajustada a %.2f A (DAC: %d)", ampsTarget, valor);
    } else if (parametro == 'f') {
      logSistema(LOG_LVL_INFO, "FUENTE", "Frecuencia pulsado ajustada a %d Hz", valor);
    } else if (parametro == 'd') {
      logSistema(LOG_LVL_INFO, "FUENTE", "Duty cycle ajustado a %d%%", valor);
    }
  }

  server.send(200, "text/plain", "OK");
}

/**
 * @brief Conmuta el modo de operación entre Continuo (DC) y Pulsado.
 */
static void handleModoF() {
  if (!server.hasArg("v")) {
    server.send(400, "text/plain", "Parámetro v faltante");
    return;
  }
  bool usarPulsado = (server.arg("v") == "1");
  conmutarModoFuente(usarPulsado);
  memoria.putBool("dac_modo", usarPulsado);
  logSistema(LOG_LVL_INFO, "FUENTE", "Modo VCSS conmutado a: %s", usarPulsado ? "PULSADO" : "CONTINUO (DC)");
  server.send(200, "text/plain", "OK");
}

/**
 * @brief Habilita o deshabilita la compensación automática de ganancia en lazo cerrado (2 Hz).
 */
static void handleSetCompF() {
  if (!server.hasArg("v")) {
    server.send(400, "text/plain", "Parámetro v faltante");
    return;
  }
  bool habilitar = (server.arg("v") == "1");
  setCompensacionLazoCerrado(habilitar);
  server.send(200, "text/plain", "OK");
}

/**
 * @brief Dispara el proceso de calibración automática de transconductancia inyectando 1.50 A patrón.
 * Aplica interlock estricto: la fuente DEBE estar apagada previamente para evitar colisión I2C y cuelgues.
 */
static void handleCalVCSS() {
  bool activa = false;
  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    activa = fuenteActiva;
    giveDataMutex();
  }

  if (activa) {
    server.send(403, "application/json", "{\"ok\":0,\"err\":\"Interlock activo: La fuente esta encendida. Apague la fuente antes de autocalibrar los shunts.\"}");
    return;
  }

  if (g_failsafe_latched) {
    server.send(403, "application/json", "{\"ok\":0,\"err\":\"Bloqueado: Sistema en alarma Fail-Safe.\"}");
    return;
  }

  if (phModuloActivo) {
    server.send(403, "application/json", "{\"ok\":0,\"err\":\"Interlock activo: Modulo de pH operando. Apague el pH antes de calibrar shunts.\"}");
    return;
  }

  bool ok = autoCalibrarVCSS();
  logSistema(LOG_LVL_INFO, "VCSS", "Auto-calibracion %s (Ganancia: %.4f)", ok ? "OK" : "FALLIDA", factorGananciaVCSS);
  char json[128];
  snprintf(json, sizeof(json), "{\"ok\":%d,\"gm\":%.4f%s}", ok ? 1 : 0, factorGananciaVCSS, ok ? "" : ",\"err\":\"Corriente fuera de rango\"");
  server.send(200, "application/json", json);
}

/**
 * @brief Restablece la ganancia Gm al valor nominal de diseño (2.000 S, Factor 1.0000x).
 */
static void handleResetCalVCSS() {
  bool activa = false;
  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    activa = fuenteActiva;
    giveDataMutex();
  }

  if (activa) {
    server.send(403, "application/json", "{\"ok\":0,\"err\":\"Interlock activo: La fuente esta encendida. Apague la fuente antes de restablecer.\"}");
    return;
  }

  resetCalibracionVCSS();
  logSistema(LOG_LVL_INFO, "VCSS", "Ganancia VCSS reescrita a nominal (Gm = 2.00 S, Factor = 1.0000)");
  char json[96];
  snprintf(json, sizeof(json), "{\"ok\":1,\"gm\":%.4f}", factorGananciaVCSS);
  server.send(200, "application/json", json);
}

/**
 * @brief Conmuta el estado de encendido/apagado de la salida de corriente VCSS.
 * Aplica interlocks de seguridad (prohibido si Fail-Safe está activo o si el módulo de pH está operando).
 */
static void handleActF() {
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

  setEstadoFuente(estado);
  if (estado) {
    float a = (amplitudDAC_Setpoint / 4095.0f) * VCSS_IMAX_NOMINAL;
    logSistema(LOG_LVL_INFO, "FUENTE", "Salida de Corriente ENCENDIDA: %.2f A (%s)", a, modoPulsado ? "Pulsado" : "DC");
  } else {
    logSistema(LOG_LVL_INFO, "FUENTE", "Salida de Corriente APAGADA por operador");
  }
  server.send(200, "text/plain", "OK");
}

/**
 * @brief Registra formalmente los endpoints de la salida de corriente en el servidor HTTP.
 */
void registrarRutasFuente() {
  server.on("/fuente", handleFuente);
  server.on("/data_f", handleDataF);
  server.on("/set_f", handleSetF);
  server.on("/modo_f", handleModoF);
  server.on("/set_comp_f", handleSetCompF);
  server.on("/cal_vcss", handleCalVCSS);
  server.on("/reset_cal_vcss", handleResetCalVCSS);
  server.on("/act_f", handleActF);
}

