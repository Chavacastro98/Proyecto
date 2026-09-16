#include "Controller_PH.h"
#include "views/View_PH.h"
#include "Modulo_PH.h"
#include "config.h"
#include <math.h>

/**
 * =================================================================================
 * IMPLEMENTACIÓN: CONTROLADOR DE PH (Controller_PH.cpp) — Versión 4.0
 * =================================================================================
 */

// Handler de la página HTML del módulo de pH
static void handlePH() {
  server.send_P(200, "text/html", HTML_PH);
}

// Handler de telemetría completa de pH dual (JSON)
static void handleGetPHDual() {
  char json[256];

  portENTER_CRITICAL(&muxPH);
  float p1 = phActual1;
  float p2 = phActual2;
  bool activo = phModuloActivo;
  uint8_t m1 = tipoCalPH1;
  uint8_t m2 = tipoCalPH2;
  float slope_m1 = m_ph1;
  float slope_m2 = m_ph2;
  float sAc1 = mAcida1;
  float sBa1 = mBasica1;
  float sAc2 = mAcida2;
  float sBa2 = mBasica2;
  bool cal1 = calibradoPH1;
  bool cal2 = calibradoPH2;
  portEXIT_CRITICAL(&muxPH);

  float sl1 = 0.0f, sl2 = 0.0f;

  // Tina 1
  if (m1 == 0) {
    sl1 = 100.0f;
  } else if (m1 == 1 && cal1) {
    sl1 = fabsf(slope_m1) / PH_PENDIENTE_TEORICA * 100.0f;
  } else if (m1 == 2 && cal1) {
    float pctAc = fabsf(sAc1) / PH_PENDIENTE_TEORICA * 100.0f;
    float pctBa = fabsf(sBa1) / PH_PENDIENTE_TEORICA * 100.0f;
    sl1 = (pctAc + pctBa) / 2.0f;
  }

  // Tina 2
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
           "{\"p1\":\"%.2f\",\"p2\":\"%.2f\",\"on\":%d,"
           "\"m1\":%d,\"m2\":%d,"
           "\"sl1\":\"%.1f\",\"sl2\":\"%.1f\","
           "\"c1\":%d,\"c2\":%d,\"il\":%d}",
           p1, p2, activo ? 1 : 0, m1, m2, sl1, sl2, cal1 ? 1 : 0,
           cal2 ? 1 : 0, il ? 1 : 0);
  server.send(200, "application/json", json);
}

// Handler de lectura de voltaje crudo para calibración de offset de placa (JSON)
static void handleDataPHRaw() {
  float v = leerVoltajeCrudoPH();

  portENTER_CRITICAL(&muxPH);
  voltajeCrudoPH = v;
  portEXIT_CRITICAL(&muxPH);

  char json[64];
  snprintf(json, sizeof(json), "{\"v\":\"%.3f\",\"mv\":\"%.1f\"}", v, v * 1000.0f);
  server.send(200, "application/json", json);
}

// Handler para encender/apagar el muestreo de pH bajo demanda con interlock
static void handleActPH() {
  if (!server.hasArg("run")) {
    server.send(400, "text/plain", "Parámetro run faltante");
    return;
  }
  bool activar = (server.arg("run") == "1");

  if (activar) {
    if (phInterlockActivo()) {
      server.send(403, "text/plain", "Interlock: termico o fuente activos");
      return;
    }
  }

  portENTER_CRITICAL(&muxPH);
  phModuloActivo = activar;
  portEXIT_CRITICAL(&muxPH);

  server.send(200, "text/plain", "OK");
}

// Handler para seleccionar el modo de calibración (?id=1/2&m=0..2)
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

  portENTER_CRITICAL(&muxPH);
  if (id == 1) {
    tipoCalPH1 = (uint8_t)modo;
    if (modo == 0) calibradoPH1 = true;
  } else {
    tipoCalPH2 = (uint8_t)modo;
    if (modo == 0) calibradoPH2 = true;
  }
  portEXIT_CRITICAL(&muxPH);

  char key[8];
  snprintf(key, sizeof(key), "tcal%d", id);
  memoria.putUChar(key, (uint8_t)modo);

  server.send(200, "text/plain", "OK");
}

// Handler para ejecutar un punto de calibración de buffer (?id=1/2&p=4/7/10)
static void handleDoCalPH() {
  if (!server.hasArg("id") || !server.hasArg("p")) {
    server.send(400, "text/plain", "Parámetros insuficientes");
    return;
  }

  int id = server.arg("id").toInt();
  int punto = server.arg("p").toInt();

  if (id != 1 && id != 2) {
    server.send(400, "text/plain", "Error de ID de Tina");
    return;
  }
  if (punto != 4 && punto != 7 && punto != 10) {
    server.send(400, "text/plain", "Buffer inválido (usar 4, 7 o 10)");
    return;
  }

  if (phInterlockActivo()) {
    server.send(403, "text/plain", "Bloqueado por Interlock: Apaga la fuente y calentadores antes de calibrar pH");
    return;
  }

  float voltajeMedido = leerVoltajePH((uint8_t)(id - 1));
  float pendienteResp = 0.0f;

  portENTER_CRITICAL(&muxPH);
  if (id == 1) {
    uint8_t modo = tipoCalPH1;

    if (punto == 7) {
      v7_1 = voltajeMedido;
    } else if (punto == 4) {
      v4_1 = voltajeMedido;
      if (fabsf(v4_1 - v7_1) > 0.01f) {
        if (modo == 1) {
          m_ph1 = (4.0f - 7.0f) / (v4_1 - v7_1);
          calibradoPH1 = true;
          pendienteResp = m_ph1;
        } else if (modo == 2) {
          mAcida1 = (4.0f - 7.0f) / (v4_1 - v7_1);
          pendienteResp = mAcida1;
          if (fabsf(v10_1 - v7_1) > 0.01f) {
            calibradoPH1 = true;
          }
        }
      }
    } else if (punto == 10) {
      v10_1 = voltajeMedido;
      if (fabsf(v10_1 - v7_1) > 0.01f && modo == 2) {
        mBasica1 = (10.0f - 7.0f) / (v10_1 - v7_1);
        pendienteResp = mBasica1;
        if (fabsf(v4_1 - v7_1) > 0.01f) {
          calibradoPH1 = true;
        }
      }
    }
  } else if (id == 2) {
    uint8_t modo = tipoCalPH2;

    if (punto == 7) {
      v7_2 = voltajeMedido;
    } else if (punto == 4) {
      v4_2 = voltajeMedido;
      if (fabsf(v4_2 - v7_2) > 0.01f) {
        if (modo == 1) {
          m_ph2 = (4.0f - 7.0f) / (v4_2 - v7_2);
          calibradoPH2 = true;
          pendienteResp = m_ph2;
        } else if (modo == 2) {
          mAcida2 = (4.0f - 7.0f) / (v4_2 - v7_2);
          pendienteResp = mAcida2;
          if (fabsf(v10_2 - v7_2) > 0.01f) {
            calibradoPH2 = true;
          }
        }
      }
    } else if (punto == 10) {
      v10_2 = voltajeMedido;
      if (fabsf(v10_2 - v7_2) > 0.01f && modo == 2) {
        mBasica2 = (10.0f - 7.0f) / (v10_2 - v7_2);
        pendienteResp = mBasica2;
        if (fabsf(v4_2 - v7_2) > 0.01f) {
          calibradoPH2 = true;
        }
      }
    }
  }
  portEXIT_CRITICAL(&muxPH);

  if (id == 1) {
    memoria.putFloat("v7_1", v7_1);
    memoria.putFloat("v4_1", v4_1);
    memoria.putFloat("v10_1", v10_1);
    memoria.putFloat("mph1", m_ph1);
    memoria.putFloat("mAc1", mAcida1);
    memoria.putFloat("mBa1", mBasica1);
    memoria.putBool("cal1", calibradoPH1);
  } else {
    memoria.putFloat("v7_2", v7_2);
    memoria.putFloat("v4_2", v4_2);
    memoria.putFloat("v10_2", v10_2);
    memoria.putFloat("mph2", m_ph2);
    memoria.putFloat("mAc2", mAcida2);
    memoria.putFloat("mBa2", mBasica2);
    memoria.putBool("cal2", calibradoPH2);
  }

  char json[128];
  snprintf(json, sizeof(json),
           "{\"ok\":1,\"v\":\"%.3f\",\"slope\":\"%.3f\"}",
           voltajeMedido, pendienteResp);
  server.send(200, "application/json", json);
}

void registrarRutasPH() {
  server.on("/ph", handlePH);
  server.on("/get_ph_dual", handleGetPHDual);
  server.on("/data_ph_raw", handleDataPHRaw);
  server.on("/act_ph", handleActPH);
  server.on("/set_cal_mode", handleSetCalMode);
  server.on("/do_cal_ph", handleDoCalPH);
}
