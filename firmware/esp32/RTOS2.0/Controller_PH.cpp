/**
 * =================================================================================
 * CONTROLADOR: MEDICIÓN Y CALIBRACIÓN DE PH DEDICADO (Controller_PH.cpp) — RTOS 2.0
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * DESCRIPCIÓN DEL MÓDULO (RTOS 2.0):
 * Gestiona el sensor de pH único y dedicado en Canal A1 del ADS1115 (Canal A0 eliminado).
 * Procesa las peticiones HTTP del subsistema de pH, modelos de calibración multipunto,
 * cálculo de eficiencia de electrodo respecto a la pendiente teórica de Nernst,
 * exposición de los puntos guardados en Flash NVS por modo y salvaguarda de interlock.
 * =================================================================================
 */

#include "Controller_PH.h"
#include "views/View_PH.h"
#include "Modulo_PH.h"
#include "RTOS_Core.h"
#include "config.h"
#include <math.h>

/**
 * @brief Entrega la vista web HTML de monitoreo, calibración y puntos NVS (HTML_PH).
 */
static void handlePH() {
  server.send_P(200, "text/html", HTML_PH);
}

/**
 * @brief Endpoint JSON que entrega el estado del sensor de pH dedicado:
 * lectura actual, voltajes analógicos reales (ADC A1 y Sonda), pendientes,
 * estado de interlock y puntos exactos guardados en memoria Flash NVS por modo.
 */
static void handleGetPH() {
  char json[512];
  float p = 7.0f;
  float v = PH_OFFSET_TEORICO;
  float vs = 2.50f;
  bool activo = false;
  uint8_t m = 0;
  float slope_m = PH_PENDIENTE_TEORICA;
  float sAc = PH_PENDIENTE_TEORICA, sBa = PH_PENDIENTE_TEORICA;
  bool cal = false;
  float saved_v7 = PH_OFFSET_TEORICO, saved_v4 = 2.0f, saved_v10 = 1.3f;

  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    p = phActual;
    v = voltajeADC_ph;
    vs = voltajeSonda_ph;
    activo = phModuloActivo;
    m = tipoCalPH;
    slope_m = m_ph;
    sAc = mAcida_ph;
    sBa = mBasica_ph;
    cal = calibradoPH;
    saved_v7 = v7_ph;
    saved_v4 = v4_ph;
    saved_v10 = v10_ph;
    giveDataMutex();
  }

  // Cálculo de Eficiencia de Pendiente Nernst (% respecto a PH_PENDIENTE_TEORICA)
  float sl = 100.0f;
  if (m == 0) {
    sl = 100.0f;
  } else if (m == 1 && cal) {
    sl = fabsf(slope_m) / PH_PENDIENTE_TEORICA * 100.0f;
  } else if (m == 2 && cal) {
    float pctAc = fabsf(sAc) / PH_PENDIENTE_TEORICA * 100.0f;
    float pctBa = fabsf(sBa) / PH_PENDIENTE_TEORICA * 100.0f;
    sl = (pctAc + pctBa) / 2.0f;
  }

  bool il = phInterlockActivo();

  // Respuesta enriquecida: Nuevas claves unificadas + Puntos NVS + Alias retrocompatibles
  snprintf(json, sizeof(json),
           "{\"p\":\"%.2f\",\"v\":\"%.3f\",\"vs\":\"%.2f\","
           "\"on\":%d,\"m\":%d,\"sl\":\"%.1f\",\"c\":%d,\"il\":%d,"
           "\"v7\":\"%.3f\",\"v4\":\"%.3f\",\"v10\":\"%.3f\","
           "\"mph\":\"%.2f\",\"mac\":\"%.2f\",\"mba\":\"%.2f\","
           "\"p1\":\"%.2f\",\"p2\":\"%.2f\","
           "\"v1\":\"%.3f\",\"v2\":\"%.3f\","
           "\"vs1\":\"%.2f\",\"vs2\":\"%.2f\","
           "\"m1\":%d,\"m2\":%d,"
           "\"sl1\":\"%.1f\",\"sl2\":\"%.1f\","
           "\"c1\":%d,\"c2\":%d}",
           p, v, vs,
           activo ? 1 : 0, m, sl, cal ? 1 : 0, il ? 1 : 0,
           saved_v7, saved_v4, saved_v10,
           slope_m, sAc, sBa,
           p, p,
           v, v,
           vs, vs,
           m, m,
           sl, sl,
           cal ? 1 : 0, cal ? 1 : 0);

  server.send(200, "application/json", json);
}

/**
 * @brief Endpoint JSON que entrega el voltaje directo sin procesar del sensor
 * dedicado en Canal A1 para ajuste de offset de hardware (potenciómetro PH-4502C en corto).
 */
static void handleDataPHRaw() {
  if (phInterlockActivo()) {
    server.send(403, "application/json", "{\"err\":\"Interlock activo: apague la fuente o calentadores\"}");
    return;
  }

  float v1 = leerVoltajeCrudoPH(ADS_CH_PH);

  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    voltajeCrudoPH = v1;
    giveDataMutex();
  }

  char json[160];
  snprintf(json, sizeof(json),
           "{\"v\":\"%.3f\",\"mv\":\"%.1f\",\"v1\":\"%.3f\",\"mv1\":\"%.1f\",\"v2\":\"0.000\",\"mv2\":\"0.0\"}",
           v1, v1 * 1000.0f, v1, v1 * 1000.0f);
  server.send(200, "application/json", json);
}

/**
 * @brief Conmuta el estado de adquisición del módulo de pH con validación estricta de interlock.
 */
static void handleActPH() {
  if (!server.hasArg("run")) {
    server.send(400, "text/plain", "Parámetro run faltante");
    return;
  }
  bool activar = (server.arg("run") == "1");

  if (activar) {
    if (g_failsafe_latched) {
      server.send(403, "text/plain", "Bloqueado: Sistema en alarma FAIL-SAFE");
      return;
    }
    if (phInterlockActivo()) {
      server.send(403, "text/plain", "Interlock: térmico o fuente activos");
      return;
    }
  }

  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    phModuloActivo = activar;
    giveDataMutex();
  }

  logSistema(LOG_LVL_INFO, "PH", "Modulo pH (Canal A1) %s por operador", activar ? "ACTIVADO" : "APAGADO");
  server.send(200, "text/plain", "OK");
}

/**
 * @brief Selecciona el modelo metrológico de calibración (0: Teórico, 1: 2 Puntos, 2: 3 Puntos).
 */
static void handleSetCalMode() {
  if (!server.hasArg("m")) {
    server.send(400, "text/plain", "Parámetro m (modo) faltante");
    return;
  }

  int modo = server.arg("m").toInt();
  if (modo < 0 || modo > 2) {
    server.send(400, "text/plain", "Modo inválido (use 0, 1 o 2)");
    return;
  }

  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    tipoCalPH = (uint8_t)modo;
    if (modo == 0) calibradoPH = true;
    giveDataMutex();
  }

  memoria.putUChar("tcal", (uint8_t)modo);
  memoria.putUChar("tcal1", (uint8_t)modo); // Compatibilidad

  server.send(200, "text/plain", "OK");
}

/**
 * @brief Ejecuta el registro de un punto tampón (pH 4, 7 o 10) con análisis de estabilidad,
 * coherencia de buffer, cálculo de pendientes y persistencia en Flash NVS.
 */
static void handleDoCalPH() {
  if (phInterlockActivo()) {
    server.send(403, "application/json", "{\"ok\":0,\"err\":\"Interlock activo: apague la fuente antes de calibrar\"}");
    return;
  }

  if (!server.hasArg("p")) {
    server.send(400, "application/json", "{\"ok\":0,\"err\":\"Parámetro p (punto) faltante\"}");
    return;
  }

  int punto = server.arg("p").toInt();
  if (punto != 4 && punto != 7 && punto != 10) {
    server.send(400, "application/json", "{\"ok\":0,\"err\":\"Punto de calibración inválido (use 4, 7 o 10)\"}");
    return;
  }

  char errMsg[160] = {0};
  float estab = 0.0f;
  bool ok = ejecutarCalibracionPH((uint8_t)punto, errMsg, sizeof(errMsg), &estab);

  float v = (punto == 7) ? v7_ph : (punto == 4 ? v4_ph : v10_ph);
  float m = m_ph;

  logSistema(LOG_LVL_INFO, "PH", "Calibracion Sensor Dedicado A1 Punto pH %d: %s (V=%.3f, m=%.1f, estab=%.1f mV)",
             punto, ok ? "OK" : "FALLIDA", v, m, estab);

  char json[256];
  if (ok) {
    snprintf(json, sizeof(json),
             "{\"ok\":1,\"v\":\"%.3f\",\"slope\":\"%.2f\",\"estab\":\"%.1f\","
             "\"v7\":\"%.3f\",\"v4\":\"%.3f\",\"v10\":\"%.3f\"}",
             v, m, estab, v7_ph, v4_ph, v10_ph);
  } else {
    snprintf(json, sizeof(json), "{\"ok\":0,\"err\":\"%s\"}", errMsg[0] ? errMsg : "Fallo en calibración");
  }
  server.send(200, "application/json", json);
}

/**
 * @brief Restablece la calibración del sensor dedicado a los valores teóricos de fábrica y limpia la NVS.
 */
static void handleResetCalPH() {
  if (phInterlockActivo()) {
    server.send(403, "application/json", "{\"ok\":0,\"err\":\"Interlock activo: apague la fuente y calefacción antes de restablecer.\"}");
    return;
  }

  bool ok = resetCalibracionPH();
  if (ok) {
    server.send(200, "application/json", "{\"ok\":1,\"msg\":\"Calibración restablecida a valores de fábrica (Flash NVS limpia)\"}");
  } else {
    server.send(500, "application/json", "{\"ok\":0,\"err\":\"No se pudo restablecer la calibración\"}");
  }
}

/**
 * @brief Registra formalmente los endpoints del módulo de pH en el servidor HTTP.
 */
void registrarRutasPH() {
  server.on("/ph", handlePH);
  server.on("/get_ph", handleGetPH);
  server.on("/get_ph_dual", handleGetPH); // Alias retrocompatible
  server.on("/data_ph_raw", handleDataPHRaw);
  server.on("/act_ph", handleActPH);
  server.on("/set_cal_mode", handleSetCalMode);
  server.on("/do_cal_ph", handleDoCalPH);
  server.on("/reset_cal_ph", handleResetCalPH);
}
