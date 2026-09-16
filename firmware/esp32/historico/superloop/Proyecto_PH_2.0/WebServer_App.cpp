#include "WebServer_App.h"
#include "Modulo_Fuentes.h"
#include "Modulo_PH.h"
#include "Modulo_Termico.h"
#include "config.h"
#include <math.h>

/**
 * =================================================================================
 * IMPLEMENTACIÓN DEL SERVIDOR WEB — Versión 2.0 (WebServer_App.cpp)
 * =================================================================================
 * Este archivo contiene toda la lógica del servidor web: las rutas de datos
 * (JSON), las rutas de acción (comandos), y las páginas HTML de la interfaz
 * gráfica.
 *
 * CAMBIOS v2.0:
 * - Nuevos endpoints: /act_ph, /set_cal_mode, /do_cal_ph (expandido), /data_ph_raw
 * - Interlock bidireccional en /act_t y /act_f (suspende pH automáticamente)
 * - Página /ph rediseñada: toggle On/Off, voltímetro, selector de modo,
 *   calibración 3 puntos con % Slope
 *
 * NOTAS TÉCNICAS IMPORTANTES:
 * - Se usan buffers de texto fijos (char buffer[N]) en lugar de la clase String
 *   de Arduino para evitar problemas de memoria después de muchos días
 * encendido.
 * - Se usa fabsf() en vez de abs() para calcular valores absolutos de números
 *   decimales, porque abs() solo funciona correctamente con números enteros.
 * - Se usan secciones críticas (portENTER_CRITICAL) al leer/escribir datos de
 *   los canales térmicos y pH para evitar lecturas corruptas.
 * =================================================================================
 */

void inicializarWebServer() {
  // --- PÁGINA PRINCIPAL ---
  server.on("/", handleMenu);

  // --- PÁGINAS DE CONTROL ---
  server.on("/termico", handleTermico);
  server.on("/fuente", handleFuente);
  server.on("/ph", handlePH);

  // --- RUTAS DE DATOS (responden con JSON para actualización automática) ---

  // Datos ambientales: temperatura, humedad y presión
  server.on("/data_env", []() {
    char json[128];
    snprintf(json, sizeof(json),
             "{\"t\":\"%.1f\",\"h\":\"%.0f\",\"p\":\"%.1f\"}", amb_temp,
             amb_hum, amb_pres);
    server.send(200, "application/json", json);
  });

  // =====================================================================
  // ENDPOINT v2.0: Lecturas de pH con estado completo del módulo
  // Retorna: pH de ambas tinas, estado On/Off, modo de calibración,
  //          porcentaje de slope (eficiencia de membrana), e interlock
  // =====================================================================
  server.on("/get_ph_dual", []() {
    char json[256];

    // Leer variables del módulo pH con sección crítica
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

    // Calcular % Slope para cada tina según el modo de calibración
    float sl1 = 0.0f, sl2 = 0.0f;

    // Tina 1
    if (m1 == 0) {
      sl1 = 100.0f; // Teórico = 100% por definición
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
  });

  // =====================================================================
  // ENDPOINT v2.0: Voltaje crudo de alta resolución para offset de placa
  // Se usa para calibrar el potenciómetro de la placa PH-4502C con BNC
  // en cortocircuito. Objetivo: lectura ≈ 1.650V
  // =====================================================================
  server.on("/data_ph_raw", []() {
    float v = leerVoltajeCrudoPH();

    // Actualizar la variable global para referencia
    portENTER_CRITICAL(&muxPH);
    voltajeCrudoPH = v;
    portEXIT_CRITICAL(&muxPH);

    char json[64];
    snprintf(json, sizeof(json), "{\"v\":\"%.3f\",\"mv\":\"%.1f\"}", v,
             v * 1000.0f);
    server.send(200, "application/json", json);
  });

  // Datos de los 4 canales térmicos: temperatura actual, setpoint y estado
  server.on("/data_t", []() {
    char json[256];
    int offset = 0;
    offset += snprintf(json + offset, sizeof(json) - offset, "[");

    for (int i = 0; i < 4; i++) {
      // Leer datos del canal dentro de sección crítica para evitar lecturas
      // corruptas
      portENTER_CRITICAL(&muxTermico);
      float temp = canales[i].temperatura;
      float sp = canales[i].setpoint;
      bool act = canales[i].activo;
      portEXIT_CRITICAL(&muxTermico);

      offset += snprintf(json + offset, sizeof(json) - offset,
                         "{\"t\":%.1f,\"sp\":%.1f,\"run\":%d}%s", temp, sp,
                         act ? 1 : 0, (i < 3) ? "," : "");
    }
    snprintf(json + offset, sizeof(json) - offset, "]");
    server.send(200, "application/json", json);
  });

  // Estado actual de la fuente de corriente
  server.on("/data_f", []() {
    char json[160];
    portENTER_CRITICAL(&muxFuente);
    bool act = fuenteActiva;
    bool modo = modoPulsado;
    int amp = amplitudDAC;
    int freq = frecuencia;
    int duty = dutyCycle;
    portEXIT_CRITICAL(&muxFuente);

    float amps = (amp / 4095.0f) * 6.6f;
    snprintf(json, sizeof(json),
             "{\"act\":%d,\"modo\":%d,\"amp\":%d,\"freq\":%d,\"duty\":%d,"
             "\"amps\":%.2f}",
             act ? 1 : 0, modo ? 1 : 0, amp, freq, duty, amps);
    server.send(200, "application/json", json);
  });

  // --- RUTAS DE ACCIÓN (reciben comandos de la interfaz web) ---

  // Cambiar la temperatura objetivo de un canal térmico
  // Parámetros: ?id=0..3 (canal) y ?v=temperatura (en °C)
  server.on("/set_t", []() {
    if (!server.hasArg("id") || !server.hasArg("v")) {
      server.send(400, "text/plain", "Parámetros faltantes");
      return;
    }
    int id = server.arg("id").toInt();
    if (id >= 0 && id < 4) {
      // Solo se permite cambiar el setpoint si el canal está apagado
      portENTER_CRITICAL(&muxTermico);
      bool canalActivo = canales[id].activo;
      portEXIT_CRITICAL(&muxTermico);

      if (!canalActivo) {
        float nuevoSP = server.arg("v").toFloat();

        // Validar que el setpoint esté en un rango razonable (0°C a 150°C)
        if (isnan(nuevoSP) || nuevoSP < 0.0f || nuevoSP > 150.0f) {
          server.send(400, "text/plain", "Setpoint fuera de rango (0-150°C)");
          return;
        }

        // Guardar el nuevo setpoint en la estructura del canal
        portENTER_CRITICAL(&muxTermico);
        canales[id].setpoint = nuevoSP;
        portEXIT_CRITICAL(&muxTermico);

        // Guardar en la memoria Flash para que se conserve al reiniciar
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
  });

  // =====================================================================
  // Encender o apagar el control térmico de todos los canales
  // v2.0: INTERLOCK CONDICIONAL — Rechazar encendido si el pH está activo
  // =====================================================================
  server.on("/act_t", []() {
    if (!server.hasArg("run")) {
      server.send(400, "text/plain", "Parámetro run faltante");
      return;
    }
    bool estado = (server.arg("run") == "1");

    if (estado) {
      // Bloqueo condicional: Prohibir encender térmico si el pH está activo
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
        canales[i].limitePotencia =
            0.0;                   // Reiniciar rampa de arranque al apagar
        canales[i].integral = 0.0; // Limpiar acumulador integral
      }
    }
    portEXIT_CRITICAL(&muxTermico);

    server.send(200, "text/plain", "OK");
  });

  // Modificar un parámetro de la fuente de corriente
  // Parámetros: ?p=a (amplitud), ?p=f (frecuencia), ?p=d (duty cycle) y ?v=valor
  server.on("/set_f", []() {
    if (!server.hasArg("p") || server.arg("p").length() == 0 ||
        !server.hasArg("v")) {
      server.send(400, "text/plain", "Parámetros insuficientes");
      return;
    }

    char parametro = server.arg("p")[0];
    int valor = server.arg("v").toInt();

    portENTER_CRITICAL(&muxFuente);
    if (parametro == 'a') {
      amplitudDAC = constrain(valor, 0, 4095); // 0-4095 (12 bits)
      memoria.putInt("dac_amp", amplitudDAC);
    } else if (parametro == 'f') {
      frecuencia = constrain(valor, 1, 100); // 1-100 Hz
      memoria.putInt("dac_freq", frecuencia);
    } else if (parametro == 'd') {
      dutyCycle = constrain(valor, 0, 100); // 0-100 %
      memoria.putInt("dac_duty", dutyCycle);
    }
    portEXIT_CRITICAL(&muxFuente);

    server.send(200, "text/plain", "OK");
  });

  // Cambiar entre modo corriente continua (DC) y corriente pulsada
  // Parámetro: ?v=1 (pulsado) o ?v=0 (continua)
  server.on("/modo_f", []() {
    if (!server.hasArg("v")) {
      server.send(400, "text/plain", "Parámetro v faltante");
      return;
    }
    bool usarPulsado = (server.arg("v") == "1");

    portENTER_CRITICAL(&muxFuente);
    modoPulsado = usarPulsado;
    memoria.putBool("dac_modo", usarPulsado);
    portEXIT_CRITICAL(&muxFuente);

    server.send(200, "text/plain", "OK");
  });

  // =====================================================================
  // Encender o apagar la salida de corriente
  // v2.0: INTERLOCK CONDICIONAL — Rechazar encendido si el pH está activo
  // =====================================================================
  server.on("/act_f", []() {
    if (!server.hasArg("run")) {
      server.send(400, "text/plain", "Parámetro run faltante");
      return;
    }
    bool estado = (server.arg("run") == "1");

    if (estado) {
      // Bloqueo condicional: Prohibir encender fuente si el pH está activo
      portENTER_CRITICAL(&muxPH);
      bool phOn = phModuloActivo;
      portEXIT_CRITICAL(&muxPH);
      if (phOn) {
        server.send(403, "text/plain", "Interlock: modulo pH activo. Apaguelo primero.");
        return;
      }
    }

    portENTER_CRITICAL(&muxFuente);
    fuenteActiva = estado;
    portEXIT_CRITICAL(&muxFuente);

    server.send(200, "text/plain", "OK");
  });

  // =====================================================================
  // ENDPOINT v2.0: Activar/Desactivar el módulo de pH
  // Parámetro: ?run=1 (activar) o ?run=0 (desactivar / standby)
  // Rechaza activación con HTTP 403 si hay interlock activo
  // =====================================================================
  server.on("/act_ph", []() {
    if (!server.hasArg("run")) {
      server.send(400, "text/plain", "Parámetro run faltante");
      return;
    }
    bool activar = (server.arg("run") == "1");

    if (activar) {
      // Verificar interlock antes de activar
      if (phInterlockActivo()) {
        server.send(403, "text/plain",
                    "Interlock: termico o fuente activos");
        return;
      }
    }

    portENTER_CRITICAL(&muxPH);
    phModuloActivo = activar;
    portEXIT_CRITICAL(&muxPH);

    // NO se persiste en NVS — siempre arranca apagado por seguridad
    server.send(200, "text/plain", "OK");
  });

  // =====================================================================
  // ENDPOINT v2.0: Seleccionar modo de calibración de pH
  // Parámetros: ?id=1 o 2 (tina) y ?m=0, 1 o 2 (modo)
  // Persiste el modo en NVS Flash
  // =====================================================================
  server.on("/set_cal_mode", []() {
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
      // Al cambiar de modo, marcar como no calibrado (excepto teórico)
      if (modo == 0)
        calibradoPH1 = true;
    } else {
      tipoCalPH2 = (uint8_t)modo;
      if (modo == 0)
        calibradoPH2 = true;
    }
    portEXIT_CRITICAL(&muxPH);

    // Persistir en NVS
    char key[8];
    snprintf(key, sizeof(key), "tcal%d", id);
    memoria.putUChar(key, (uint8_t)modo);

    server.send(200, "text/plain", "OK");
  });

  // =====================================================================
  // ENDPOINT v2.0: Ejecutar un punto de calibración de pH
  // Parámetros: ?id=1 o 2 (tina) y ?p=7, 4 u 11 (buffer de referencia)
  // Retorna JSON con voltaje medido, pendiente y % slope calculados
  // =====================================================================
  server.on("/do_cal_ph", []() {
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
    if (punto != 4 && punto != 7 && punto != 11) {
      server.send(400, "text/plain", "Buffer inválido (usar 4, 7 u 11)");
      return;
    }

    // Leer el voltaje actual de la sonda de pH
    float voltajeMedido = leerVoltajePH((uint8_t)(id - 1));

    // Variables para la respuesta JSON
    float pendienteResp = 0.0f;
    float slopePct = 0.0f;

    portENTER_CRITICAL(&muxPH);

    if (id == 1) {
      uint8_t modo = tipoCalPH1;

      if (punto == 7) {
        v7_1 = voltajeMedido;
      } else if (punto == 4) {
        v4_1 = voltajeMedido;
        if (fabsf(v4_1 - v7_1) > 0.01f) {
          if (modo == 1) {
            // Modo 2 Puntos: pendiente lineal simple
            m_ph1 = (4.0f - 7.0f) / (v4_1 - v7_1);
            calibradoPH1 = true;
            pendienteResp = m_ph1;
          } else if (modo == 2) {
            // Modo 3 Puntos: pendiente ácida
            mAcida1 = (4.0f - 7.0f) / (v4_1 - v7_1);
            pendienteResp = mAcida1;
            // Calibración completa solo si también tenemos pH 11
            if (fabsf(v11_1 - v7_1) > 0.01f) {
              calibradoPH1 = true;
            }
          }
        }
      } else if (punto == 11) {
        v11_1 = voltajeMedido;
        if (fabsf(v11_1 - v7_1) > 0.01f && modo == 2) {
          // Modo 3 Puntos: pendiente básica
          mBasica1 = (11.0f - 7.0f) / (v11_1 - v7_1);
          pendienteResp = mBasica1;
          // Calibración completa solo si también tenemos pH 4
          if (fabsf(v4_1 - v7_1) > 0.01f) {
            calibradoPH1 = true;
          }
        }
      }
      // Calcular % Slope para la respuesta
      if (modo == 1 && calibradoPH1) {
        slopePct = fabsf(m_ph1) / PH_PENDIENTE_TEORICA * 100.0f;
      } else if (modo == 2 && calibradoPH1) {
        float pA = fabsf(mAcida1) / PH_PENDIENTE_TEORICA * 100.0f;
        float pB = fabsf(mBasica1) / PH_PENDIENTE_TEORICA * 100.0f;
        slopePct = (pA + pB) / 2.0f;
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
            if (fabsf(v11_2 - v7_2) > 0.01f) {
              calibradoPH2 = true;
            }
          }
        }
      } else if (punto == 11) {
        v11_2 = voltajeMedido;
        if (fabsf(v11_2 - v7_2) > 0.01f && modo == 2) {
          mBasica2 = (11.0f - 7.0f) / (v11_2 - v7_2);
          pendienteResp = mBasica2;
          if (fabsf(v4_2 - v7_2) > 0.01f) {
            calibradoPH2 = true;
          }
        }
      }
      if (modo == 1 && calibradoPH2) {
        slopePct = fabsf(m_ph2) / PH_PENDIENTE_TEORICA * 100.0f;
      } else if (modo == 2 && calibradoPH2) {
        float pA = fabsf(mAcida2) / PH_PENDIENTE_TEORICA * 100.0f;
        float pB = fabsf(mBasica2) / PH_PENDIENTE_TEORICA * 100.0f;
        slopePct = (pA + pB) / 2.0f;
      }
    }

    portEXIT_CRITICAL(&muxPH);

    // Persistir todos los coeficientes en NVS
    if (id == 1) {
      memoria.putFloat("v7_1", v7_1);
      memoria.putFloat("v4_1", v4_1);
      memoria.putFloat("v11_1", v11_1);
      memoria.putFloat("mph1", m_ph1);
      memoria.putFloat("mAc1", mAcida1);
      memoria.putFloat("mBa1", mBasica1);
      memoria.putBool("cal1", calibradoPH1);
    } else {
      memoria.putFloat("v7_2", v7_2);
      memoria.putFloat("v4_2", v4_2);
      memoria.putFloat("v11_2", v11_2);
      memoria.putFloat("mph2", m_ph2);
      memoria.putFloat("mAc2", mAcida2);
      memoria.putFloat("mBa2", mBasica2);
      memoria.putBool("cal2", calibradoPH2);
    }

    // Responder con JSON informativo
    char json[128];
    snprintf(json, sizeof(json),
             "{\"ok\":1,\"v\":\"%.3f\",\"slope\":\"%.3f\",\"pct\":\"%.1f\"}",
             voltajeMedido, pendienteResp, slopePct);
    server.send(200, "application/json", json);
  });

  server.begin(); // Poner en marcha el servidor web
}

// =================================================================================
// PÁGINAS WEB DE LA INTERFAZ GRÁFICA (almacenadas en la memoria Flash del
// ESP32)
// =================================================================================
// Las páginas se guardan en la Flash (PROGMEM) en vez de la RAM porque son
// textos grandes y la RAM del ESP32 es limitada. Cada página incluye su HTML,
// CSS y JavaScript.

// --- MENU PRINCIPAL ---
const char HTML_MENU[] PROGMEM = R"rawliteral(
<!DOCTYPE html><html><head><meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Control Galvanoplastia</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:'Inter',system-ui,sans-serif;background:#0b1120;color:#e2e8f0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px;}
.menu-card{background:linear-gradient(165deg,rgba(30,41,59,0.95),rgba(15,23,42,0.9));padding:32px 28px;border-radius:20px;box-shadow:0 12px 40px rgba(0,0,0,0.5);width:100%;max-width:480px;border:1px solid rgba(56,189,248,0.1);text-align:center;}
h2{font-size:1.4em;color:#fff;font-weight:800;letter-spacing:-0.5px;}
.sub-title{color:#64748b;font-size:0.82em;font-weight:600;margin-top:4px;margin-bottom:24px;}
.env-box{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;background:rgba(15,23,42,0.6);padding:14px;border-radius:14px;margin-bottom:24px;border:1px solid rgba(51,65,85,0.4);}
.env-item{font-size:0.68em;color:#38bdf8;font-weight:700;letter-spacing:0.5px;text-transform:uppercase;}
.env-val{font-size:1.25em;display:block;color:#f8fafc;font-weight:800;margin-top:4px;letter-spacing:-0.5px;}
.btn-menu{display:flex;align-items:center;justify-content:space-between;padding:16px 20px;margin:12px 0;background:linear-gradient(135deg,#1e293b,#0f172a);color:#f1f5f9;text-decoration:none;font-weight:700;border-radius:12px;border:1px solid rgba(56,189,248,0.12);transition:all 0.25s;font-size:0.9em;}
.btn-menu:hover{border-color:#38bdf8;background:linear-gradient(135deg,#1e3a8a,#1e40af);color:#fff;transform:translateY(-2px);box-shadow:0 6px 20px rgba(59,130,246,0.25);}
.btn-menu .badge{font-size:0.7em;background:rgba(56,189,248,0.15);color:#38bdf8;padding:4px 8px;border-radius:6px;font-weight:800;}
</style></head>
<body>
    <div class='menu-card'>
        <h2>Panel de Control</h2>
        <div class='sub-title'>Tesis de Electrodeposici&oacute;n / Zincado</div>
        <div class='env-box'>
            <div class='env-item'>Temp. Amb.<span class='env-val' id='amb_t'>0.0 &deg;C</span></div>
            <div class='env-item'>Humedad<span class='env-val' id='amb_h'>0 %</span></div>
            <div class='env-item'>Presi&oacute;n<span class='env-val' id='amb_p'>0 hPa</span></div>
        </div>
        <a href='/termico' class='btn-menu'><span>Control T&eacute;rmico</span><span class='badge'>4 CANALES</span></a>
        <a href='/fuente' class='btn-menu'><span>Fuente de Corriente</span><span class='badge'>DAC MCP4725</span></a>
        <a href='/ph' class='btn-menu'><span>M&oacute;dulo de pH 2.0</span><span class='badge' style='background:rgba(34,197,94,0.15);color:#34d399;'>DUAL / DEDICADO</span></a>
    </div>
    <script>
        function updEnv(){
            fetch('/data_env').then(function(r){return r.json();}).then(function(d){
                document.getElementById('amb_t').innerHTML=d.t+' &deg;C';
                document.getElementById('amb_h').innerText=d.h+' %';
                document.getElementById('amb_p').innerText=d.p+' hPa';
            }).catch(function(){});
        }
        setInterval(updEnv, 3000); updEnv();
    </script>
</body></html>)rawliteral";

// --- CONTROL TERMICO (4 canales) ---
const char HTML_TERMICO[] PROGMEM = R"rawliteral(
<!DOCTYPE html><html><head><meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Control T&eacute;rmico</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:'Inter',system-ui,sans-serif;background:#0b1120;color:#e2e8f0;min-height:100vh;padding:16px 14px;}
.container{max-width:760px;margin:0 auto;}
.hdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;padding:16px 20px;background:rgba(15,23,42,0.7);border-radius:14px;border:1px solid rgba(56,189,248,0.08);}
.nav-back{color:#38bdf8;text-decoration:none;font-weight:700;font-size:0.82em;}
.nav-back:hover{color:#7dd3fc;}
.hdr-t{font-size:1.1em;font-weight:800;color:#fff;}
.btn-group{display:flex;gap:10px;justify-content:center;margin-bottom:20px;}
.btn{padding:12px 22px;cursor:pointer;border-radius:10px;border:none;font-weight:800;font-size:0.85em;transition:all 0.2s;letter-spacing:0.3px;}
.btn-act{background:#059669;color:#fff;box-shadow:0 4px 14px rgba(5,150,105,0.3);}
.btn-act:hover{background:#10b981;}
.btn-stop{background:#dc2626;color:#fff;box-shadow:0 4px 14px rgba(220,38,38,0.3);}
.btn-stop:hover{background:#ef4444;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;}
.card{background:linear-gradient(165deg,rgba(30,41,59,0.95),rgba(15,23,42,0.9));border-radius:16px;padding:18px;border:1px solid rgba(56,189,248,0.08);box-shadow:0 4px 20px rgba(0,0,0,0.35);border-left:4px solid #38bdf8;transition:border-color 0.3s;}
.card h3{font-size:0.92em;color:#94a3b8;margin-bottom:10px;font-weight:700;}
.temp-val{font-size:1.8em;font-weight:900;color:#38bdf8;letter-spacing:-1px;margin:6px 0;}
.sp-box{margin-top:12px;background:rgba(15,23,42,0.6);padding:10px;border-radius:10px;display:flex;align-items:center;justify-content:space-between;border:1px solid rgba(51,65,85,0.4);}
.sp-lbl{font-size:0.75em;color:#94a3b8;font-weight:600;}
.sp-val{font-size:1em;font-weight:800;color:#fff;}
.btn-step{background:#1e293b;color:#38bdf8;border:1px solid #334155;width:32px;height:32px;border-radius:6px;font-weight:900;cursor:pointer;font-size:1.1em;display:flex;align-items:center;justify-content:center;transition:0.2s;}
.btn-step:hover:not(:disabled){background:#38bdf8;color:#0f172a;}
.btn-step:disabled{opacity:0.3;cursor:not-allowed;}
.status-row{margin-top:10px;font-size:0.75em;font-weight:700;}
.badge-error{background:rgba(220,38,38,0.2);color:#fca5a5;border:1px solid rgba(239,68,68,0.4);padding:4px 8px;border-radius:6px;font-size:0.75em;font-weight:800;display:inline-block;}
</style></head>
<body>
    <div class='container'>
        <div class='hdr'>
            <a href='/' class='nav-back'>&larr; Men&uacute;</a>
            <span class='hdr-t'>Lazos de Control T&eacute;rmico</span>
            <div></div>
        </div>
        <div class='btn-group'>
            <button class='btn btn-act' onclick='toggleT(1)'>ENCENDER SISTEMA</button>
            <button class='btn btn-stop' onclick='toggleT(0)'>APAGAR SISTEMA</button>
        </div>
        <div class='grid' id='t-cards'></div>
    </div>
    <script>
        const nombres = ["Limpieza", "Decapado", "Zincado (Celda Hull)", "Niquelado"];
        function loadThermal(){
            fetch('/data_t').then(function(r){return r.json();}).then(function(data){
                let h = '';
                data.forEach(function(c, i){
                    let esError = (c.t <= 0.0 || c.t >= 150.0);
                    let colorBorde = esError ? '#ef4444' : (c.run==1?'#10b981':'#38bdf8');
                    let estadoHtml = esError ? 
                        '<div class="badge-error">FALLA TERMOPAR (PARADA)</div>' : 
                        (c.run==1?'<span style="color:#10b981">Activo</span>':'<span style="color:#ef4444">Bloqueado</span>');

                    h += '<div class="card" style="border-left-color:'+colorBorde+'">' +
                        '<h3>' + nombres[i] + '</h3>' +
                        '<div class="temp-val" style="color:' + (esError?'#ef4444':'#38bdf8') + '">' + (esError?'ERROR':c.t.toFixed(1)+' &deg;C') + '</div>' +
                        '<div class="sp-box">' +
                            '<div><span class="sp-lbl">Setpoint: </span><span class="sp-val">' + c.sp + ' &deg;C</span></div>' +
                            '<div style="display:flex;gap:4px;">' +
                                '<button class="btn-step" ' + (c.run==1||esError?'disabled':'') + ' onclick="setSP(' + i + ',' + (c.sp-1) + ')">-</button>' +
                                '<button class="btn-step" ' + (c.run==1||esError?'disabled':'') + ' onclick="setSP(' + i + ',' + (c.sp+1) + ')">+</button>' +
                            '</div>' +
                        '</div>' +
                        '<div class="status-row">Estado: ' + estadoHtml + '</div>' +
                    '</div>';
                });
                document.getElementById('t-cards').innerHTML = h;
            }).catch(function(){});
        }
        function setSP(id, val){ 
            if(val < 0) val = 0; if(val > 150) val = 150;
            fetch('/set_t?id=' + id + '&v=' + val).then(function(r){
                if(r.status === 403) alert('Detenga el sistema termico primero para cambiar el setpoint.');
                loadThermal();
            }); 
        }
        function toggleT(run){ 
            fetch('/act_t?run=' + run).then(function(r){
                if(r.status === 403) alert('¡Bloqueado por Interlock!\nEl módulo de pH está activo.\nDebes apagar el pH manualmente en su menú antes de encender la calefacción.');
                loadThermal();
            }); 
        }
        setInterval(loadThermal, 2000); loadThermal();
    </script>
</body></html>)rawliteral";

// =================================================================================
// MODULO DE PH 2.0 -- INTERFAZ WEB COMPLETA
// =================================================================================
// Todos los caracteres especiales usan entidades HTML para compatibilidad
// garantizada con cualquier navegador y codificacion del compilador.
// =================================================================================
const char HTML_PH[] PROGMEM = R"rawliteral(
<!DOCTYPE html><html><head><meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>M&oacute;dulo pH 2.0</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:'Inter',system-ui,sans-serif;background:#0b1120;color:#e2e8f0;min-height:100vh;padding:0;}
.page{max-width:760px;margin:0 auto;padding:16px 14px 32px;}

/* Header */
.hdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;padding:16px 20px;background:rgba(15,23,42,0.7);border-radius:14px;border:1px solid rgba(56,189,248,0.08);}
.nav-back{color:#38bdf8;text-decoration:none;font-weight:700;font-size:0.82em;transition:0.2s;}
.nav-back:hover{color:#7dd3fc;}
.hdr-title{font-size:1.1em;color:white;font-weight:800;letter-spacing:-0.3px;}
.hdr-sub{font-size:0.65em;color:#64748b;font-weight:600;display:block;margin-top:2px;letter-spacing:0.5px;}

/* Toggle Switch */
.tog-wrap{display:flex;align-items:center;gap:10px;}
.tog{position:relative;width:54px;height:28px;background:#334155;border-radius:14px;cursor:pointer;transition:all 0.35s cubic-bezier(.4,0,.2,1);border:2px solid #475569;outline:none;}
.tog.on{background:#059669;border-color:#34d399;box-shadow:0 0 16px rgba(5,150,105,0.4);}
.tog::after{content:'';position:absolute;width:20px;height:20px;background:#f8fafc;border-radius:50%;top:2px;left:3px;transition:all 0.35s cubic-bezier(.4,0,.2,1);box-shadow:0 1px 4px rgba(0,0,0,0.3);}
.tog.on::after{left:27px;}
.tog-lbl{font-size:0.68em;color:#64748b;font-weight:800;letter-spacing:1px;min-width:58px;text-align:right;}
.tog-lbl.act{color:#34d399;}

/* Interlock Alert */
.il-alert{background:linear-gradient(135deg,rgba(127,29,29,0.25),rgba(153,27,27,0.15));border:1px solid rgba(239,68,68,0.4);color:#fca5a5;padding:12px 18px;border-radius:12px;text-align:center;margin-bottom:18px;font-weight:700;font-size:0.82em;display:none;letter-spacing:0.2px;}
.il-alert.vis{display:flex;align-items:center;justify-content:center;gap:8px;animation:pulse 2.5s ease-in-out infinite;}
.il-icon{width:18px;height:18px;background:#ef4444;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:10px;color:white;font-weight:900;flex-shrink:0;}

/* Grid */
.grid{display:flex;flex-wrap:wrap;justify-content:center;gap:16px;margin-bottom:20px;}

/* Card */
.card{background:linear-gradient(165deg,rgba(30,41,59,0.95),rgba(15,23,42,0.9));border-radius:18px;padding:22px 20px;width:350px;border:1px solid rgba(56,189,248,0.08);box-shadow:0 4px 24px rgba(0,0,0,0.4),inset 0 1px 0 rgba(255,255,255,0.03);transition:all 0.3s;}
.card:hover{border-color:rgba(56,189,248,0.2);box-shadow:0 8px 40px rgba(0,0,0,0.5),inset 0 1px 0 rgba(255,255,255,0.05);}
.card-t{display:flex;align-items:center;gap:8px;margin-bottom:14px;}
.card-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0;}
.card-dot.t1{background:#38bdf8;box-shadow:0 0 6px rgba(56,189,248,0.5);}
.card-dot.t2{background:#a78bfa;box-shadow:0 0 6px rgba(167,139,250,0.5);}
.card-name{font-size:0.88em;color:#94a3b8;font-weight:700;}

/* pH Display */
.ph-wrap{text-align:center;padding:16px 0 12px;position:relative;}
.ph-ring{width:120px;height:120px;border-radius:50%;margin:0 auto;display:flex;align-items:center;justify-content:center;border:3px solid #1e293b;background:rgba(15,23,42,0.6);transition:all 0.5s;}
.ph-ring.active{border-color:rgba(34,197,94,0.3);box-shadow:0 0 30px rgba(34,197,94,0.08);}
.ph-val{font-size:36px;font-weight:900;font-variant-numeric:tabular-nums;transition:color 0.4s;letter-spacing:-1px;}
.ph-val.off{color:#334155;font-size:28px;}
.ph-label{font-size:0.65em;color:#475569;font-weight:600;margin-top:6px;letter-spacing:0.5px;}

/* Mode Selector */
.mode-sel{display:flex;gap:4px;margin:12px 0;background:#0f172a;border-radius:10px;padding:3px;}
.mode-b{flex:1;padding:8px 4px;border-radius:8px;border:none;background:transparent;color:#64748b;font-size:0.68em;font-weight:800;cursor:pointer;transition:all 0.25s;text-align:center;letter-spacing:0.3px;}
.mode-b.act{background:linear-gradient(135deg,#1e40af,#3b82f6);color:#fff;box-shadow:0 2px 8px rgba(59,130,246,0.3);}
.mode-b:hover:not(.act){color:#94a3b8;background:rgba(30,41,59,0.5);}

/* Calibration */
.cal-sec{background:rgba(15,23,42,0.5);border-radius:12px;padding:12px 14px;margin-top:12px;border:1px solid rgba(51,65,85,0.4);}
.cal-title{color:#475569;font-size:0.7em;font-weight:700;letter-spacing:0.5px;margin-bottom:8px;text-transform:uppercase;}
.cal-btn{width:100%;padding:10px 12px;margin:4px 0;border-radius:8px;border:none;font-weight:700;cursor:pointer;font-size:0.78em;transition:all 0.2s;display:flex;align-items:center;gap:8px;text-align:left;}
.cal-btn .dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;}
.cb7{background:rgba(6,78,59,0.5);color:#6ee7b7;border:1px solid rgba(34,197,94,0.2);}
.cb7 .dot{background:#22c55e;}
.cb4{background:rgba(127,29,29,0.35);color:#fca5a5;border:1px solid rgba(239,68,68,0.2);}
.cb4 .dot{background:#ef4444;}
.cb11{background:rgba(30,58,138,0.35);color:#93c5fd;border:1px solid rgba(59,130,246,0.2);}
.cb11 .dot{background:#3b82f6;}
.cal-btn:hover{filter:brightness(1.3);transform:translateY(-1px);}

/* Slope */
.sl-wrap{margin-top:14px;padding-top:12px;border-top:1px solid rgba(51,65,85,0.3);}
.sl-bar{height:4px;background:#1e293b;border-radius:2px;overflow:hidden;}
.sl-fill{height:100%;border-radius:2px;transition:width 0.6s ease,background 0.4s;}
.sl-lbl{font-size:0.7em;color:#475569;margin-top:5px;font-weight:600;}

/* Offset Panel */
.off-panel{background:linear-gradient(165deg,rgba(30,41,59,0.95),rgba(15,23,42,0.9));border-radius:18px;padding:20px;border:1px solid rgba(251,191,36,0.1);box-shadow:0 4px 24px rgba(0,0,0,0.4);}
.off-hdr{display:flex;align-items:center;justify-content:space-between;}
.off-t{display:flex;align-items:center;gap:8px;font-weight:700;font-size:0.88em;}
.off-t-icon{width:28px;height:28px;border-radius:8px;background:rgba(251,191,36,0.12);display:flex;align-items:center;justify-content:center;font-size:14px;color:#fbbf24;}
.off-t-text{color:#fbbf24;}
.off-tog{background:#1e293b;color:#94a3b8;border:1px solid #334155;padding:7px 16px;border-radius:8px;cursor:pointer;font-size:0.75em;font-weight:800;transition:all 0.2s;letter-spacing:0.5px;}
.off-tog:hover{background:#334155;color:#e2e8f0;}
.off-tog.open{background:rgba(146,64,14,0.4);color:#fcd34d;border-color:rgba(251,191,36,0.3);}
.off-body{display:none;margin-top:16px;}
.off-desc{font-size:0.75em;color:#64748b;line-height:1.5;margin-bottom:14px;padding:10px 12px;background:rgba(15,23,42,0.5);border-radius:8px;border-left:3px solid #fbbf24;}

/* Voltmeter */
.vm-wrap{text-align:center;padding:10px 0;}
.vm-val{font-size:48px;font-weight:900;font-variant-numeric:tabular-nums;letter-spacing:-2px;line-height:1;}
.vm-unit{font-size:18px;color:#64748b;font-weight:600;margin-left:4px;}
.vm-mv{font-size:0.8em;color:#475569;margin-top:4px;}

/* Gauge */
.gauge-wrap{padding:4px 0 0;}
.gauge{position:relative;height:16px;border-radius:8px;overflow:visible;margin:20px 0 24px;background:linear-gradient(90deg,#dc2626 0%,#f59e0b 30%,#22c55e 42%,#22c55e 58%,#f59e0b 70%,#dc2626 100%);}
.gauge-tgt{position:absolute;top:-6px;left:50%;width:2px;height:28px;background:rgba(255,255,255,0.8);transform:translateX(-50%);z-index:2;}
.gauge-tgt::before{content:'1.650V';position:absolute;top:-18px;left:50%;transform:translateX(-50%);font-size:0.6em;color:rgba(255,255,255,0.6);white-space:nowrap;font-weight:700;}
.gauge-ndl{position:absolute;top:-4px;width:8px;height:24px;background:#f8fafc;border-radius:4px;transform:translateX(-50%);transition:left 0.3s ease-out;box-shadow:0 0 8px rgba(255,255,255,0.5),0 2px 4px rgba(0,0,0,0.3);z-index:3;}

/* Diff & Badge */
.off-diff{text-align:center;font-size:1.1em;font-weight:800;margin:8px 0 12px;letter-spacing:-0.5px;}
.off-badge-wrap{text-align:center;}
.off-badge{display:inline-block;padding:7px 18px;border-radius:20px;font-weight:800;font-size:0.78em;letter-spacing:0.3px;}

/* Animations */
@keyframes pulse{0%,100%{opacity:1;}50%{opacity:0.6;}}

/* Responsive */
@media(max-width:440px){
  .card{width:100%;}
  .ph-val{font-size:30px;}
  .ph-ring{width:100px;height:100px;}
  .vm-val{font-size:38px;}
  .hdr{flex-wrap:wrap;gap:8px;}
  .hdr-title{font-size:0.95em;}
}
</style></head>
<body>
<div class='page'>

<!-- Header -->
<div class='hdr'>
  <a href='/' class='nav-back'>&larr; Men&uacute;</a>
  <div style='text-align:center'>
    <span class='hdr-title'>M&oacute;dulo de pH 2.0</span>
    <span class='hdr-sub'>ADS1115 &middot; 16-BIT &middot; DUAL CHANNEL</span>
  </div>
  <div class='tog-wrap'>
    <span class='tog-lbl' id='tog-lbl'>STANDBY</span>
    <button class='tog' id='ph-tog' onclick='togglePH()'></button>
  </div>
</div>

<!-- Interlock Alert -->
<div class='il-alert' id='il-alert'>
  <span class='il-icon'>!</span>
  INTERLOCK &mdash; Apague el sistema t&eacute;rmico y la fuente antes de activar pH
</div>

<!-- pH Cards -->
<div class='grid'>

  <!-- TINA 1 -->
  <div class='card'>
    <div class='card-t'><span class='card-dot t1'></span><span class='card-name'>Electrodo pH 1 &mdash; Zincado</span></div>
    <div class='ph-wrap'>
      <div class='ph-ring' id='ring1'>
        <span class='ph-val off' id='ph1'>&mdash;</span>
      </div>
      <div class='ph-label'>CANAL 0 &middot; ADS1115</div>
    </div>
    <div class='mode-sel'>
      <button class='mode-b act' id='m1-0' onclick='setMode(1,0)'>TE&Oacute;RICO</button>
      <button class='mode-b' id='m1-1' onclick='setMode(1,1)'>2 PUNTOS</button>
      <button class='mode-b' id='m1-2' onclick='setMode(1,2)'>3 PUNTOS</button>
    </div>
    <div class='cal-sec'>
      <div class='cal-title'>Calibraci&oacute;n de Electrodos</div>
      <button class='cal-btn cb7' onclick='calibrar(1,7)'><span class='dot'></span>Calibrar Buffer pH 7.0</button>
      <button class='cal-btn cb4' id='cal-1-4' onclick='calibrar(1,4)' style='display:none'><span class='dot'></span>Calibrar Buffer pH 4.0</button>
      <button class='cal-btn cb11' id='cal-1-11' onclick='calibrar(1,11)' style='display:none'><span class='dot'></span>Calibrar Buffer pH 11.0</button>
    </div>
    <div class='sl-wrap'>
      <div class='sl-bar'><div class='sl-fill' id='sf1' style='width:0%;background:#334155'></div></div>
      <div class='sl-lbl' id='sl1'>Sin calibraci&oacute;n</div>
    </div>
  </div>

  <!-- TINA 2 -->
  <div class='card'>
    <div class='card-t'><span class='card-dot t2'></span><span class='card-name'>Electrodo pH 2 &mdash; Niquelado</span></div>
    <div class='ph-wrap'>
      <div class='ph-ring' id='ring2'>
        <span class='ph-val off' id='ph2'>&mdash;</span>
      </div>
      <div class='ph-label'>CANAL 1 &middot; ADS1115</div>
    </div>
    <div class='mode-sel'>
      <button class='mode-b act' id='m2-0' onclick='setMode(2,0)'>TE&Oacute;RICO</button>
      <button class='mode-b' id='m2-1' onclick='setMode(2,1)'>2 PUNTOS</button>
      <button class='mode-b' id='m2-2' onclick='setMode(2,2)'>3 PUNTOS</button>
    </div>
    <div class='cal-sec'>
      <div class='cal-title'>Calibraci&oacute;n de Electrodos</div>
      <button class='cal-btn cb7' onclick='calibrar(2,7)'><span class='dot'></span>Calibrar Buffer pH 7.0</button>
      <button class='cal-btn cb4' id='cal-2-4' onclick='calibrar(2,4)' style='display:none'><span class='dot'></span>Calibrar Buffer pH 4.0</button>
      <button class='cal-btn cb11' id='cal-2-11' onclick='calibrar(2,11)' style='display:none'><span class='dot'></span>Calibrar Buffer pH 11.0</button>
    </div>
    <div class='sl-wrap'>
      <div class='sl-bar'><div class='sl-fill' id='sf2' style='width:0%;background:#334155'></div></div>
      <div class='sl-lbl' id='sl2'>Sin calibraci&oacute;n</div>
    </div>
  </div>
</div>

<!-- Offset Panel -->
<div class='off-panel'>
  <div class='off-hdr'>
    <div class='off-t'>
      <span class='off-t-icon'>&#9881;</span>
      <span class='off-t-text'>Ajuste de Offset de Placa</span>
    </div>
    <button class='off-tog' id='off-tog' onclick='toggleOffset()'>ABRIR</button>
  </div>
  <div class='off-body' id='off-body'>
    <div class='off-desc'>
      Conecte el BNC en cortocircuito (sin sonda). Ajuste el potenci&oacute;metro de la placa PH-4502C
      hasta que el voltaje sea <b style='color:#fbbf24'>1.650 V</b> (&plusmn;10 mV).
    </div>
    <div class='vm-wrap'>
      <span class='vm-val' id='raw-v'>0.000</span><span class='vm-unit'>V</span>
      <div class='vm-mv' id='raw-mv'>0.0 mV</div>
    </div>
    <div class='gauge-wrap'>
      <div class='gauge'>
        <div class='gauge-tgt'></div>
        <div class='gauge-ndl' id='g-ndl' style='left:50%'></div>
      </div>
    </div>
    <div class='off-diff' id='off-diff'>+0.0 mV</div>
    <div class='off-badge-wrap'>
      <span class='off-badge' id='off-badge'
            style='background:rgba(71,85,105,0.2);color:#64748b;border:1px solid #475569;'>
        Esperando lectura...
      </span>
    </div>
  </div>
</div>

</div><!-- /page -->

<script>
var phOn=false,ilAct=false,curM1=0,curM2=0;
var rawIv=null,offOpen=false;

function fetchPH(){
  fetch('/get_ph_dual').then(function(r){return r.json();}).then(function(d){
    phOn=(d.on==1);ilAct=(d.il==1);
    curM1=parseInt(d.m1);curM2=parseInt(d.m2);
    var tg=document.getElementById('ph-tog');
    tg.className=phOn?'tog on':'tog';
    var tl=document.getElementById('tog-lbl');
    tl.innerText=phOn?'ACTIVO':'STANDBY';
    tl.className=phOn?'tog-lbl act':'tog-lbl';
    var ia=document.getElementById('il-alert');
    ia.className=ilAct?'il-alert vis':'il-alert';
    updPH(1,d.p1,phOn);updPH(2,d.p2,phOn);
    updMode(1,curM1);updMode(2,curM2);
    updCal(1,curM1);updCal(2,curM2);
    updSlope(1,d.sl1,curM1,d.c1);
    updSlope(2,d.sl2,curM2,d.c2);
  }).catch(function(){});
}

function updPH(tina,val,on){
  var el=document.getElementById('ph'+tina);
  var ring=document.getElementById('ring'+tina);
  if(!on){el.innerHTML='&mdash;';el.className='ph-val off';ring.className='ph-ring';return;}
  var v=parseFloat(val);
  if(isNaN(v)||v<0||v>14){el.innerText='ERR';el.className='ph-val';el.style.color='#ef4444';ring.className='ph-ring';return;}
  el.innerText=v.toFixed(2);el.className='ph-val';ring.className='ph-ring active';
  var h;
  if(v<=3)h=0;
  else if(v<=7)h=(v-3)/4*120;
  else if(v<=11)h=120+(v-7)/4*120;
  else{h=240;if(v>11)h+=Math.min((v-11)/3*40,40);}
  el.style.color='hsl('+Math.round(h)+',75%,58%)';
  ring.style.borderColor='hsla('+Math.round(h)+',75%,58%,0.25)';
  ring.style.boxShadow='0 0 24px hsla('+Math.round(h)+',75%,58%,0.1)';
}

function togglePH(){
  if(ilAct&&!phOn){
    alert('¡Bloqueado por Interlock!\nEl sistema térmico o la fuente de corriente están activos.\nDebes apagarlos manualmente en sus menús antes de medir pH.');
    return;
  }
  fetch('/act_ph?run='+(phOn?0:1)).then(function(r){
    if(r.status===403)alert('¡Bloqueado por Interlock!\nDebes apagar el sistema térmico y la fuente de corriente manualmente primero.');
    fetchPH();
  });
}

function setMode(t,m){fetch('/set_cal_mode?id='+t+'&m='+m).then(function(){fetchPH();});}
function updMode(t,m){for(var i=0;i<3;i++){var b=document.getElementById('m'+t+'-'+i);if(b)b.className=(i===m)?'mode-b act':'mode-b';}}

function updCal(t,m){
  var b4=document.getElementById('cal-'+t+'-4');
  var b11=document.getElementById('cal-'+t+'-11');
  if(b4)b4.style.display=(m>=1)?'flex':'none';
  if(b11)b11.style.display=(m===2)?'flex':'none';
}

function calibrar(t,p){
  if(!confirm('Confirmar calibracion pH '+p+'.0 en Tina '+t+'?\nAsegurese de que la sonda este sumergida en el buffer.'))return;
  fetch('/do_cal_ph?id='+t+'&p='+p).then(function(r){return r.json();}).then(function(d){
    if(d.ok==1){
      var info='Punto pH '+p+' guardado en NVS.\nVoltaje: '+d.v+' V';
      if(parseFloat(d.slope)!==0)info+='\nPendiente: '+d.slope+' pH/V';
      if(parseFloat(d.pct)>0)info+='\nEficiencia: '+d.pct+'%';
      alert(info);
    }else{alert('Error de calibracion');}
    fetchPH();
  }).catch(function(){alert('Error de comunicacion');});
}

function updSlope(t,val,m,cal){
  var fill=document.getElementById('sf'+t);
  var lbl=document.getElementById('sl'+t);
  if(m===0){fill.style.width='100%';fill.style.background='linear-gradient(90deg,#0ea5e9,#38bdf8)';lbl.innerText='Teorico (100%)';return;}
  if(parseInt(cal)!==1){fill.style.width='0%';fill.style.background='#334155';lbl.innerText='Sin calibracion';return;}
  var v=parseFloat(val);
  if(isNaN(v)||v<=0){fill.style.width='0%';fill.style.background='#334155';lbl.innerText='Sin datos';return;}
  var pct=Math.min(v,110);
  fill.style.width=(pct/110*100)+'%';
  if(v>=90&&v<=105)fill.style.background='linear-gradient(90deg,#059669,#34d399)';
  else if(v>=80)fill.style.background='linear-gradient(90deg,#d97706,#fbbf24)';
  else fill.style.background='linear-gradient(90deg,#dc2626,#ef4444)';
  lbl.innerText='Eficiencia membrana: '+v+'%';
}

function toggleOffset(){
  offOpen=!offOpen;
  document.getElementById('off-body').style.display=offOpen?'block':'none';
  var btn=document.getElementById('off-tog');
  btn.innerText=offOpen?'CERRAR':'ABRIR';
  btn.className=offOpen?'off-tog open':'off-tog';
  if(offOpen){rawIv=setInterval(fetchRaw,250);fetchRaw();}
  else{if(rawIv){clearInterval(rawIv);rawIv=null;}}
}

function fetchRaw(){
  fetch('/data_ph_raw').then(function(r){return r.json();}).then(function(d){
    var v=parseFloat(d.v);
    document.getElementById('raw-v').innerText=v.toFixed(3);
    document.getElementById('raw-mv').innerText=d.mv+' mV';
    var pct=(v/3.3)*100;if(pct<0)pct=0;if(pct>100)pct=100;
    document.getElementById('g-ndl').style.left=pct+'%';
    var diff=v-1.650;var diffEl=document.getElementById('off-diff');
    var diffMv=diff*1000;
    diffEl.innerText=(diff>=0?'+':'')+diffMv.toFixed(1)+' mV';
    var badge=document.getElementById('off-badge');
    var ad=Math.abs(diff);
    if(ad<0.010){
      diffEl.style.color='#34d399';
      badge.innerText='Calibrado (\u00b110 mV)';
      badge.style.cssText='background:rgba(5,150,105,0.15);color:#34d399;border:1px solid rgba(52,211,153,0.3);display:inline-block;padding:7px 18px;border-radius:20px;font-weight:800;font-size:0.78em;';
    }else if(ad<0.050){
      diffEl.style.color='#fbbf24';
      badge.innerText='Ajustar potenciometro';
      badge.style.cssText='background:rgba(217,119,6,0.15);color:#fbbf24;border:1px solid rgba(251,191,36,0.3);display:inline-block;padding:7px 18px;border-radius:20px;font-weight:800;font-size:0.78em;';
    }else{
      diffEl.style.color='#ef4444';
      badge.innerText='Fuera de rango';
      badge.style.cssText='background:rgba(220,38,38,0.15);color:#ef4444;border:1px solid rgba(239,68,68,0.3);display:inline-block;padding:7px 18px;border-radius:20px;font-weight:800;font-size:0.78em;';
    }
  }).catch(function(){});
}

setInterval(fetchPH,1500);fetchPH();
</script>
</body></html>)rawliteral";

// --- FUENTE DE CORRIENTE ---
const char HTML_FUENTE[] PROGMEM = R"rawliteral(
<!DOCTYPE html><html><head><meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Fuente de Corriente</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:'Inter',system-ui,sans-serif;background:#0b1120;color:#e2e8f0;min-height:100vh;padding:16px 14px;}
.container{max-width:520px;margin:0 auto;}
.hdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;padding:16px 20px;background:rgba(15,23,42,0.7);border-radius:14px;border:1px solid rgba(56,189,248,0.08);}
.nav-back{color:#38bdf8;text-decoration:none;font-weight:700;font-size:0.82em;}
.nav-back:hover{color:#7dd3fc;}
.hdr-t{font-size:1.1em;font-weight:800;color:#fff;}
.card{background:linear-gradient(165deg,rgba(30,41,59,0.95),rgba(15,23,42,0.9));border-radius:20px;padding:26px 22px;border:1px solid rgba(56,189,248,0.1);box-shadow:0 12px 40px rgba(0,0,0,0.5);text-align:center;}
.btn-pwr{width:100%;font-size:1.05em;padding:16px;border-radius:12px;font-weight:800;cursor:pointer;border:none;transition:all 0.25s;letter-spacing:0.5px;}
.btn-pwr-off{background:#059669;color:#fff;box-shadow:0 4px 20px rgba(5,150,105,0.35);}
.btn-pwr-off:hover{background:#10b981;transform:translateY(-1px);}
.btn-pwr-on{background:#dc2626;color:#fff;box-shadow:0 4px 20px rgba(220,38,38,0.35);}
.btn-pwr-on:hover{background:#ef4444;transform:translateY(-1px);}
.status-badge{display:inline-block;padding:6px 16px;border-radius:20px;font-weight:800;font-size:0.8em;margin:16px 0 10px;letter-spacing:0.3px;}
.status-on{background:rgba(5,150,105,0.15);color:#34d399;border:1px solid rgba(52,211,153,0.3);}
.status-off{background:rgba(220,38,38,0.15);color:#fca5a5;border:1px solid rgba(239,68,68,0.3);}
.amp-box{font-size:52px;color:#38bdf8;margin:8px 0 16px;font-weight:900;letter-spacing:-2px;font-variant-numeric:tabular-nums;}
.amp-box span{color:#fff;}
.btn-mode-wrap{display:flex;gap:8px;margin-bottom:18px;}
.btn-m{flex:1;padding:12px;border-radius:10px;border:none;font-weight:800;font-size:0.8em;cursor:pointer;transition:all 0.2s;}
.btn-m.act{background:#2563eb;color:#fff;box-shadow:0 2px 10px rgba(37,99,235,0.35);}
.btn-m.inact{background:#1e293b;color:#64748b;border:1px solid #334155;}
.btn-m.inact:hover{background:#334155;color:#94a3b8;}
.ctrl-group{background:rgba(15,23,42,0.6);padding:14px;border-radius:12px;margin-top:12px;text-align:left;border:1px solid rgba(51,65,85,0.4);}
.ctrl-group label{font-weight:700;font-size:0.8em;color:#94a3b8;display:flex;justify-content:space-between;}
.ctrl-group b{color:#38bdf8;}
input[type=range]{width:100%;accent-color:#38bdf8;margin:10px 0 2px;cursor:pointer;}
</style></head>
<body>
    <div class='container'>
        <div class='hdr'>
            <a href='/' class='nav-back'>&larr; Men&uacute;</a>
            <span class='hdr-t'>Fuente de Corriente</span>
            <div></div>
        </div>
        <div class='card'>
            <button class='btn-pwr btn-pwr-off' id='btn-power' onclick='togglePower()'>ENCENDER FUENTE</button>
            <div><span class='status-badge status-off' id='status-badge'>ESTADO: DESACTIVADA (0.00 A)</span></div>
            <div class='amp-box'><span id='amp-amps'>0.00</span> A</div>
            <div class='btn-mode-wrap'>
                <button class='btn-m act' id='btn-dc' onclick='setModo(0)'>CONTINUA (DC)</button>
                <button class='btn-m inact' id='btn-pulsed' onclick='setModo(1)'>PULSADA (PWM)</button>
            </div>
            <div class='ctrl-group'>
                <label><span>Amplitud DAC: <b id='amp-bits'>1024</b> bits</span><span>(<span id='amp-calc'>1.65</span> A)</span></label>
                <input type='range' id='slide-amp' min='0' max='4095' value='1024' oninput='onAmpChange(this.value)'>
            </div>
            <div id='pulsed-options' style='display:none;'>
                <div class='ctrl-group'>
                    <label><span>Frecuencia</span><b id='freq-val'>1 Hz</b></label>
                    <input type='range' id='slide-freq' min='1' max='100' value='1' oninput='sendParam("f", this.value)'>
                </div>
                <div class='ctrl-group'>
                    <label><span>Ciclo de Trabajo</span><b id='duty-val'>50 %</b></label>
                    <input type='range' id='slide-duty' min='1' max='99' value='50' oninput='sendParam("d", this.value)'>
                </div>
            </div>
        </div>
    </div>
    <script>
        var fuenteActiva = false;
        var isDragging = false;

        function loadFuenteData(){
            if (isDragging) return;
            fetch('/data_f').then(function(r){return r.json();}).then(function(d){
                fuenteActiva = (d.act == 1);
                var btnPwr = document.getElementById('btn-power');
                var badge = document.getElementById('status-badge');
                var ampVal = parseFloat(d.amps).toFixed(2);
                
                if (fuenteActiva) {
                    btnPwr.innerText = "APAGAR FUENTE";
                    btnPwr.className = "btn-pwr btn-pwr-on";
                    badge.innerText = "ESTADO: SALIDA ACTIVA (" + ampVal + " A)";
                    badge.className = "status-badge status-on";
                    document.getElementById('amp-amps').innerText = ampVal;
                } else {
                    btnPwr.innerText = "ENCENDER FUENTE";
                    btnPwr.className = "btn-pwr btn-pwr-off";
                    badge.innerText = "ESTADO: DESACTIVADA (0.00 A)";
                    badge.className = "status-badge status-off";
                    document.getElementById('amp-amps').innerText = "0.00";
                }

                var isPulsed = (d.modo == 1);
                document.getElementById('pulsed-options').style.display = isPulsed ? 'block' : 'none';
                document.getElementById('btn-dc').className = isPulsed ? 'btn-m inact' : 'btn-m act';
                document.getElementById('btn-pulsed').className = isPulsed ? 'btn-m act' : 'btn-m inact';

                document.getElementById('slide-amp').value = d.amp;
                document.getElementById('amp-bits').innerText = d.amp;
                document.getElementById('amp-calc').innerText = ampVal;
                document.getElementById('slide-freq').value = d.freq;
                document.getElementById('freq-val').innerText = d.freq + ' Hz';
                document.getElementById('slide-duty').value = d.duty;
                document.getElementById('duty-val').innerText = d.duty + ' %';
            }).catch(function(){});
        }

        function togglePower(){
            var nuevoEstado = fuenteActiva ? 0 : 1;
            fetch('/act_f?run=' + nuevoEstado).then(function(r){
                if(r.status === 403) alert('¡Bloqueado por Interlock!\nEl módulo de pH está activo.\nDebes apagar el pH manualmente en su menú antes de encender la fuente de corriente.');
                loadFuenteData();
            });
        }

        function setModo(m){
            document.getElementById('pulsed-options').style.display = (m==1) ? 'block' : 'none';
            document.getElementById('btn-dc').className = (m==1) ? 'btn-m inact' : 'btn-m act';
            document.getElementById('btn-pulsed').className = (m==1) ? 'btn-m act' : 'btn-m inact';
            fetch('/modo_f?v=' + m).then(function(){loadFuenteData();});
        }

        function onAmpChange(v){
            isDragging = true;
            document.getElementById('amp-bits').innerText = v;
            var amps = ((v / 4095.0) * 6.6).toFixed(2);
            document.getElementById('amp-calc').innerText = amps;
            if (fuenteActiva) {
                document.getElementById('amp-amps').innerText = amps;
            }
            sendParam("a", v);
            setTimeout(function(){ isDragging = false; }, 1000);
        }

        function sendParam(p, v){
            if(p=='f') document.getElementById('freq-val').innerText = v + ' Hz';
            if(p=='d') document.getElementById('duty-val').innerText = v + ' %';
            fetch('/set_f?p=' + p + '&v=' + v);
        }

        setInterval(loadFuenteData, 2000); 
        loadFuenteData();
    </script>
</body></html>)rawliteral";

// --- FUNCIONES QUE ENVÍAN LAS PÁGINAS AL NAVEGADOR ---

void handleMenu() { server.send_P(200, "text/html", HTML_MENU); }

void handleTermico() { server.send_P(200, "text/html", HTML_TERMICO); }

void handleFuente() { server.send_P(200, "text/html", HTML_FUENTE); }

void handlePH() { server.send_P(200, "text/html", HTML_PH); }
