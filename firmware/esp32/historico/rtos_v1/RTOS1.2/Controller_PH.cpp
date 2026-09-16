/**
 * =================================================================================
 * CONTROLADOR: MEDICIÓN Y CALIBRACIÓN DE PH DUAL (Controller_PH.cpp) — RTOS 1.0
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * DESCRIPCIÓN DEL MÓDULO:
 * Procesa las peticiones HTTP del subsistema de pH dual. Gestiona los modelos
 * de calibración multipunto, el cálculo de eficiencia de electrodo respecto a
 * la pendiente teórica de Nernst y la salvaguarda de interlock que impide
 * medir o calibrar con perturbaciones eléctricas en el electrolito.
 * =================================================================================
 */

#include "Controller_PH.h"
#include "views/View_PH.h"
#include "Modulo_PH.h"
#include "RTOS_Core.h"
#include "config.h"
#include <math.h>

/**
 * @brief Entrega la vista web HTML de monitoreo y calibración de pH dual (HTML_PH).
 */
static void handlePH() {
  server.send_P(200, "text/html", HTML_PH);
}

/**
 * @brief Endpoint JSON que entrega el estado de ambas sondas de pH:
 * lecturas actuales, voltajes analógicos reales (ADC y Sonda), pendientes y banderas.
 */
static void handleGetPHDual() {
  char json[320];
  float p1 = 7.0f, p2 = 7.0f;
  float v1 = PH_OFFSET_TEORICO, v2 = PH_OFFSET_TEORICO;
  float vs1 = 2.50f, vs2 = 2.50f;
  bool activo = false;
  uint8_t m1 = 0, m2 = 0;
  float slope_m1 = -PH_PENDIENTE_TEORICA, slope_m2 = -PH_PENDIENTE_TEORICA;
  float sAc1 = -PH_PENDIENTE_TEORICA, sBa1 = -PH_PENDIENTE_TEORICA;
  float sAc2 = -PH_PENDIENTE_TEORICA, sBa2 = -PH_PENDIENTE_TEORICA;
  bool cal1 = false, cal2 = false;

  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    p1 = phActual1;
    p2 = phActual2;
    v1 = voltajeADC1;
    v2 = voltajeADC2;
    vs1 = voltajeSonda1;
    vs2 = voltajeSonda2;
    activo = phModuloActivo;
    m1 = tipoCalPH1;
    m2 = tipoCalPH2;
    slope_m1 = m_ph1;
    slope_m2 = m_ph2;
    sAc1 = mAcida1;
    sBa1 = mBasica1;
    sAc2 = mAcida2;
    sBa2 = mBasica2;
    cal1 = calibradoPH1;
    cal2 = calibradoPH2;
    giveDataMutex();
  }

  float sl1 = 0.0f, sl2 = 0.0f;

  // Cálculo de Eficiencia de Pendiente para Tina 1 (% respecto al valor teórico 5.70 pH/V)
  if (m1 == 0) {
    sl1 = 100.0f;
  } else if (m1 == 1 && cal1) {
    sl1 = fabsf(slope_m1) / PH_PENDIENTE_TEORICA * 100.0f;
  } else if (m1 == 2 && cal1) {
    float pctAc = fabsf(sAc1) / PH_PENDIENTE_TEORICA * 100.0f;
    float pctBa = fabsf(sBa1) / PH_PENDIENTE_TEORICA * 100.0f;
    sl1 = (pctAc + pctBa) / 2.0f;
  }

  // Cálculo de Eficiencia de Pendiente para Tina 2
  if (m2 == 0) {
    sl2 = 100.0f;
  } else if (m2 == 1 && cal2) {
    sl2 = fabsf(slope_m2) / PH_PENDIENTE_TEORICA * 100.0f;
  } else if (m2 == 2 && cal2) {
    float pctAc = fabsf(sAc2) / PH_PENDIENTE_TEORICA * 100.0f;
    float pctBa = fabsf(sBa2) / PH_PENDIENTE_TEORICA * 100.0f;
    sl2 = (pctAc + pctBa) / 2.0f;
  }

  bool il = phInterlockActivo();

  snprintf(json, sizeof(json),
           "{\"p1\":\"%.2f\",\"p2\":\"%.2f\","
           "\"v1\":\"%.3f\",\"v2\":\"%.3f\","
           "\"vs1\":\"%.2f\",\"vs2\":\"%.2f\","
           "\"on\":%d,\"m1\":%d,\"m2\":%d,"
           "\"sl1\":\"%.1f\",\"sl2\":\"%.1f\","
           "\"c1\":%d,\"c2\":%d,\"il\":%d}",
           p1, p2, v1, v2, vs1, vs2, activo ? 1 : 0, m1, m2, sl1, sl2, cal1 ? 1 : 0,
           cal2 ? 1 : 0, il ? 1 : 0);
  server.send(200, "application/json", json);
}

/**
 * @brief Endpoint JSON que entrega el voltaje directo sin procesar de AMBOS canales
 * para calibración de hardware (offset con BNC en cortocircuito).
 */
static void handleDataPHRaw() {
  float v0 = 0.0f, v1 = 0.0f;
  leerVoltajeCrudoDual(v0, v1);

  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    voltajeCrudoPH = v0;
    giveDataMutex();
  }

  char json[128];
  snprintf(json, sizeof(json),
           "{\"v1\":\"%.3f\",\"mv1\":\"%.1f\",\"v2\":\"%.3f\",\"mv2\":\"%.1f\"}",
           v0, v0 * 1000.0f, v1, v1 * 1000.0f);
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
      server.send(403, "text/plain", "Interlock: termico o fuente activos");
      return;
    }
  }

  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    phModuloActivo = activar;
    giveDataMutex();
  }

  logSistema(LOG_LVL_INFO, "PH", "Modulo pH %s por operador", activar ? "ACTIVADO" : "APAGADO");
  server.send(200, "text/plain", "OK");
}

/**
 * @brief Selecciona el modelo metrológico de calibración (0: Teórico, 1: 2 Puntos, 2: 3 Puntos).
 */
static void handleSetCalMode() {
  if (!server.hasArg("id") || !server.hasArg("m")) {
    server.send(400, "text/plain", "Parámetros insuficientes");
    return;
  }

  int id = server.arg("id").toInt();
  int modo = server.arg("m").toInt();

  if ((id != 1 && id != 2) || modo < 0 || modo > 2) {
    server.send(400, "text/plain", "ID o modo inválido");
    return;
  }

  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    if (id == 1) {
      tipoCalPH1 = (uint8_t)modo;
      if (modo == 0) calibradoPH1 = true;
    } else {
      tipoCalPH2 = (uint8_t)modo;
      if (modo == 0) calibradoPH2 = true;
    }
    giveDataMutex();
  }

  char key[8];
  snprintf(key, sizeof(key), "tcal%d", id);
  memoria.putUChar(key, (uint8_t)modo);

  server.send(200, "text/plain", "OK");
}

/**
 * @brief Ejecuta el registro de un punto tampón (pH 4, 7 o 10) con análisis de estabilidad,
 * coherencia de buffer y cálculo de pendientes.
 */
static void handleDoCalPH() {
  if (!server.hasArg("id") || !server.hasArg("p")) {
    server.send(400, "application/json", "{\"ok\":0,\"err\":\"Parámetros insuficientes\"}");
    return;
  }

  int id = server.arg("id").toInt();
  int punto = server.arg("p").toInt();

  if ((id != 1 && id != 2) || (punto != 4 && punto != 7 && punto != 10)) {
    server.send(400, "application/json", "{\"ok\":0,\"err\":\"Parámetros de calibración inválidos\"}");
    return;
  }

  char errMsg[160] = {0};
  float estab = 0.0f;
  bool ok = ejecutarCalibracionPH((uint8_t)id, (uint8_t)punto, errMsg, sizeof(errMsg), &estab);

  float v = (id == 1) ? ((punto == 7) ? v7_1 : (punto == 4 ? v4_1 : v10_1))
                      : ((punto == 7) ? v7_2 : (punto == 4 ? v4_2 : v10_2));
  float m = (id == 1) ? m_ph1 : m_ph2;

  logSistema(LOG_LVL_INFO, "PH", "Calibracion Tina %d Punto pH %d: %s (V=%.3f, m=%.1f, estab=%.1f mV)",
             id, punto, ok ? "OK" : "FALLIDA", v, m, estab);

  char json[220];
  if (ok) {
    snprintf(json, sizeof(json), "{\"ok\":1,\"v\":\"%.3f\",\"slope\":\"%.2f\",\"estab\":\"%.1f\"}",
             v, m, estab);
  } else {
    snprintf(json, sizeof(json), "{\"ok\":0,\"err\":\"%s\"}", errMsg[0] ? errMsg : "Fallo en calibración");
  }
  server.send(200, "application/json", json);
}

/**
 * @brief Restablece la calibración de la tina indicada a los valores teóricos de fábrica y limpia la NVS.
 */
static void handleResetCalPH() {
  if (!server.hasArg("id")) {
    server.send(400, "application/json", "{\"ok\":0,\"err\":\"Parámetro id faltante\"}");
    return;
  }

  int id = server.arg("id").toInt();
  if (id != 1 && id != 2) {
    server.send(400, "application/json", "{\"ok\":0,\"err\":\"ID de tina inválido\"}");
    return;
  }

  if (phInterlockActivo()) {
    server.send(403, "application/json", "{\"ok\":0,\"err\":\"Interlock activo: apague la fuente y calefacción antes de restablecer.\"}");
    return;
  }

  bool ok = resetCalibracionPH((uint8_t)id);
  if (ok) {
    server.send(200, "application/json", "{\"ok\":1,\"msg\":\"Calibración restablecida a valores de fábrica\"}");
  } else {
    server.send(500, "application/json", "{\"ok\":0,\"err\":\"No se pudo restablecer la calibración\"}");
  }
}

/**
 * @brief Registra formalmente los endpoints del módulo de pH dual en el servidor HTTP.
 */
void registrarRutasPH() {
  server.on("/ph", handlePH);
  server.on("/get_ph_dual", handleGetPHDual);
  server.on("/data_ph_raw", handleDataPHRaw);
  server.on("/act_ph", handleActPH);
  server.on("/set_cal_mode", handleSetCalMode);
  server.on("/do_cal_ph", handleDoCalPH);
  server.on("/reset_cal_ph", handleResetCalPH);
}

