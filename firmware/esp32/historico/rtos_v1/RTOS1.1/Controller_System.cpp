/**
 * =================================================================================
 * CONTROLADOR: SISTEMA, AMBIENTE Y DIAGNÓSTICO (Controller_System.cpp)
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * DESCRIPCIÓN DEL MÓDULO:
 * Implementa las funciones controladoras de la capa MVC para la telemetría general,
 * el diagnóstico de sensores I2C/SPI, el historial de eventos en RAM y la entrega
 * de las interfaces HTML maestras.
 * =================================================================================
 */

#include "Controller_System.h"
#include "views/View_Menu.h"
#include "views/View_Sensores.h"
#include "views/View_Consola.h"
#include "Modulo_Ambiental.h"
#include "Modulo_Termico.h"
#include "Modulo_PH.h"
#include "Modulo_Fuentes.h"
#include "Task_Supervisor.h"
#include "RTOS_Core.h"
#include "config.h"
#include <math.h>

// =================================================================================
// FUNCIONES DE VALIDACIÓN ROBUSTA I2C (Handshake de Registros y Chip IDs)
// =================================================================================
// Descartan falsos positivos generados cuando un bus I2C queda flotante a 0V
// (donde una lectura genérica devolvería falsos ACKs para todas las direcciones).

/**
 * @brief Valida la presencia de un sensor AHT20/AHT10 leyendo su registro de estado.
 * @param addr Dirección I2C (0x38 o 0x39).
 * @return true si el chip respondió con un estado válido y calibrado.
 */
static bool validarAHT20(uint8_t addr) {
  Wire.beginTransmission(addr);
  Wire.write(0x71); // Consulta de registro de estado AHT20/AHT10
  if (Wire.endTransmission() != 0) return false;
  if (Wire.requestFrom((int)addr, 1) != 1) return false;
  uint8_t st = Wire.read();
  return (st != 0x00 && st != 0xFF && (st & 0x08) != 0);
}

/**
 * @brief Valida la presencia de un sensor BMP280 leyendo su registro CHIP_ID (0xD0).
 * @param addr Dirección I2C (0x76 o 0x77).
 * @return true si el identificador coincide con la familia Bosch Sensortec.
 */
static bool validarBMP280(uint8_t addr) {
  Wire.beginTransmission(addr);
  Wire.write(0xD0); // Registro CHIP_ID
  if (Wire.endTransmission() != 0) return false;
  if (Wire.requestFrom((int)addr, 1) != 1) return false;
  uint8_t id = Wire.read();
  return (id == 0x58 || id == 0x60 || id == 0x56 || id == 0x57);
}

/**
 * @brief Valida la presencia de un ADC ADS1115 inspeccionando su registro de configuración.
 * @param addr Dirección I2C (0x48..0x4B).
 * @return true si el registro contiene datos coherentes.
 */
static bool validarADS1115(uint8_t addr) {
  Wire.beginTransmission(addr);
  Wire.write(0x01); // Registro de Configuración
  if (Wire.endTransmission() != 0) return false;
  if (Wire.requestFrom((int)addr, 2) != 2) return false;
  uint8_t msb = Wire.read();
  uint8_t lsb = Wire.read();
  uint16_t cfg = ((uint16_t)msb << 8) | lsb;
  return (cfg != 0x0000 && cfg != 0xFFFF && (cfg & 0x8000) != 0);
}

/**
 * @brief Valida la presencia del DAC MCP4725 leyendo el byte de estado de conversión.
 * @param addr Dirección I2C (0x60..0x63).
 * @return true si el bit RDY está activo.
 */
static bool validarMCP4725(uint8_t addr) {
  Wire.beginTransmission(addr);
  if (Wire.endTransmission() != 0) return false;
  if (Wire.requestFrom((int)addr, 3) != 3) return false;
  uint8_t b1 = Wire.read();
  Wire.read();
  Wire.read();
  return ((b1 & 0x80) != 0 && b1 != 0xFF);
}

/**
 * @brief Sirve la página web del Menú Principal (Dashboard).
 */
static void handleMenu() {
  server.send_P(200, "text/html", HTML_MENU);
}

/**
 * @brief Sirve la página web de Diagnóstico de Sensores.
 */
static void handleSensores() {
  server.send_P(200, "text/html", HTML_SENSORES);
}

/**
 * @brief Sirve la página web de la Consola de Logs del Sistema.
 */
static void handleConsola() {
  server.send_P(200, "text/html", HTML_CONSOLA);
}

/**
 * @brief Endpoint JSON que entrega el contenido cronológico del buffer circular de logs en RAM.
 */
static void handleLogs() {
  static char jsonBuf[3072];
  obtenerLogsJSON(jsonBuf, sizeof(jsonBuf));
  server.send(200, "application/json", jsonBuf);
}

/**
 * @brief Endpoint JSON que entrega magnitudes ambientales y estado de alarma Fail-Safe.
 */
static void handleDataEnv() {
  char json[256];
  float t = 0.0f, h = 0.0f, p = 0.0f;
  bool fs = false;
  uint8_t code = ERR_NONE;
  char reason[64];
  char reasonEscaped[128];

  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    t = amb_temp;
    h = amb_hum;
    p = amb_pres;
    fs = g_failsafe_latched;
    code = g_failsafe_code;
    strncpy(reason, g_failsafe_reason, sizeof(reason) - 1);
    reason[sizeof(reason) - 1] = '\0';
    giveDataMutex();
  }

  escaparJSON(reason, reasonEscaped, sizeof(reasonEscaped));

  snprintf(json, sizeof(json),
           "{\"t\":\"%.1f\",\"h\":\"%.0f\",\"p\":\"%.1f\","
           "\"fs\":{\"latched\":%d,\"code\":%d,\"reason\":\"%s\"}}",
           t, h, p, fs ? 1 : 0, (int)code, reasonEscaped);
  server.send(200, "application/json", json);
}

// =================================================================================
// ENDPOINT UNIFICADO DE TELEMETRÍA (/data_all) — Optimización SCADA 75% Menos Tráfico
// =================================================================================

/**
 * @brief Concatena en una sola respuesta JSON el estado completo de la planta:
 * - Térmico: Temperaturas, setpoints, potencias aplicadas y estado de ejecución.
 * - Salida de Corriente: Modo, amplitud, frecuencia, duty cycle, corriente total y shunts.
 * - Módulo pH: Lecturas de ambas tinas, pendientes de calibración e interlock.
 * - Ambiental: Condiciones del laboratorio de electrodeposición.
 * - Fail-Safe: Estado del pestillo de seguridad y causa de alarma.
 */
static void handleDataAll() {
  char json[1024];

  // 1. Snapshot Térmico
  float t_val[4] = {0.0f}, sp_val[4] = {0.0f};
  int pot_val[4] = {0};
  bool act_val[4] = {false};

  // 2. Snapshot Salida de Corriente
  bool f_act = false, f_modo = false, f_comp = false, f_rele = false;
  int f_amp = 0, f_sp = 0, f_freq = 1, f_duty = 50;
  float f_ireal = 0.0f, f_i1 = 0.0f, f_i2 = 0.0f, f_vs1 = 0.0f, f_vs2 = 0.0f, f_gm = 1.0f;

  // 3. Snapshot pH Dual
  float ph1 = 7.0f, ph2 = 7.0f;
  bool ph_on = false, cal1 = false, cal2 = false;
  uint8_t m1 = 0, m2 = 0;
  float slope_m1 = -PH_PENDIENTE_TEORICA, slope_m2 = -PH_PENDIENTE_TEORICA;
  float sAc1 = -PH_PENDIENTE_TEORICA, sBa1 = -PH_PENDIENTE_TEORICA;
  float sAc2 = -PH_PENDIENTE_TEORICA, sBa2 = -PH_PENDIENTE_TEORICA;

  // 4. Snapshot Ambiental y Fail-Safe
  float env_t = 0.0f, env_h = 0.0f, env_p = 0.0f;
  bool fs_latched = false;
  uint8_t fs_code = ERR_NONE;
  char fs_reason[64] = "OK";
  char fs_reasonEscaped[128] = "OK";

  if (takeDataMutex(pdMS_TO_TICKS(30))) {
    for (int i = 0; i < 4; i++) {
      t_val[i] = canales[i].temperatura;
      sp_val[i] = canales[i].setpoint;
      pot_val[i] = canales[i].potenciaActual;
      act_val[i] = canales[i].activo;
    }

    f_act = fuenteActiva;
    f_modo = modoPulsado;
    f_amp = amplitudDAC;
    f_sp = amplitudDAC_Setpoint;
    f_freq = frecuencia;
    f_duty = dutyCycle;
    f_ireal = corrienteTotalReal;
    f_i1 = corrienteReal_R1;
    f_i2 = corrienteReal_R2;
    f_vs1 = voltajeShunt1_raw;
    f_vs2 = voltajeShunt2_raw;
    f_gm = factorGananciaVCSS;
    f_comp = compensacionLazoCerrado;
    f_rele = estadoReleVDD;

    ph1 = phActual1;
    ph2 = phActual2;
    ph_on = phModuloActivo;
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

    env_t = amb_temp;
    env_h = amb_hum;
    env_p = amb_pres;
    fs_latched = g_failsafe_latched;
    fs_code = g_failsafe_code;
    strncpy(fs_reason, g_failsafe_reason, sizeof(fs_reason) - 1);
    fs_reason[sizeof(fs_reason) - 1] = '\0';

    giveDataMutex();
  }

  escaparJSON(fs_reason, fs_reasonEscaped, sizeof(fs_reasonEscaped));

  float sl1 = 100.0f, sl2 = 100.0f;
  if (m1 == 1 && cal1) sl1 = fabsf(slope_m1) / PH_PENDIENTE_TEORICA * 100.0f;
  else if (m1 == 2 && cal1) sl1 = (fabsf(sAc1) + fabsf(sBa1)) / (2.0f * PH_PENDIENTE_TEORICA) * 100.0f;

  if (m2 == 1 && cal2) sl2 = fabsf(slope_m2) / PH_PENDIENTE_TEORICA * 100.0f;
  else if (m2 == 2 && cal2) sl2 = (fabsf(sAc2) + fabsf(sBa2)) / (2.0f * PH_PENDIENTE_TEORICA) * 100.0f;

  float f_amps = (f_sp / 4095.0f) * VCSS_IMAX_NOMINAL;
  bool il = phInterlockActivo();

  snprintf(json, sizeof(json),
    "{\"t\":[{\"t\":%.1f,\"sp\":%.1f,\"p\":%d,\"run\":%d},"
           "{\"t\":%.1f,\"sp\":%.1f,\"p\":%d,\"run\":%d},"
           "{\"t\":%.1f,\"sp\":%.1f,\"p\":%d,\"run\":%d},"
           "{\"t\":%.1f,\"sp\":%.1f,\"p\":%d,\"run\":%d}],"
    "\"f\":{\"act\":%d,\"modo\":%d,\"amp\":%d,\"sp\":%d,\"freq\":%d,\"duty\":%d,"
           "\"amps\":%.2f,\"i_real\":%.2f,\"i1\":%.2f,\"i2\":%.2f,"
           "\"vs1\":%.3f,\"vs2\":%.3f,\"gm\":%.4f,\"comp\":%d,\"rele\":%d},"
    "\"ph\":{\"p1\":\"%.2f\",\"p2\":\"%.2f\",\"on\":%d,\"m1\":%d,\"m2\":%d,"
             "\"sl1\":\"%.1f\",\"sl2\":\"%.1f\",\"c1\":%d,\"c2\":%d,\"il\":%d},"
    "\"env\":{\"t\":\"%.1f\",\"h\":\"%.0f\",\"p\":\"%.1f\"},"
    "\"fs\":{\"latched\":%d,\"code\":%d,\"reason\":\"%s\"}}",
    t_val[0], sp_val[0], pot_val[0], act_val[0] ? 1 : 0,
    t_val[1], sp_val[1], pot_val[1], act_val[1] ? 1 : 0,
    t_val[2], sp_val[2], pot_val[2], act_val[2] ? 1 : 0,
    t_val[3], sp_val[3], pot_val[3], act_val[3] ? 1 : 0,
    f_act ? 1 : 0, f_modo ? 1 : 0, f_amp, f_sp, f_freq, f_duty,
    f_amps, f_ireal, f_i1, f_i2, f_vs1, f_vs2, f_gm, f_comp ? 1 : 0, f_rele ? 1 : 0,
    ph1, ph2, ph_on ? 1 : 0, m1, m2, sl1, sl2, cal1 ? 1 : 0, cal2 ? 1 : 0, il ? 1 : 0,
    env_t, env_h, env_p,
    fs_latched ? 1 : 0, (int)fs_code, fs_reasonEscaped
  );

  server.send(200, "application/json", json);
}

/**
 * @brief Endpoint JSON que informa la salud del hardware I2C y SPI en tiempo real.
 */
static void handleDataSensors() {
  char json[256];
  bool i2c_aht = false, i2c_bmp = false, i2c_ads = false, i2c_dac = false;

  // Escaneo I2C protegido por xI2CMutex
  if (takeI2CMutex(pdMS_TO_TICKS(150))) {
    i2c_aht = validarAHT20(0x38) || validarAHT20(0x39);
    i2c_bmp = validarBMP280(0x76) || validarBMP280(0x77);
    i2c_ads = validarADS1115(0x48) || validarADS1115(0x49) || validarADS1115(0x4A) || validarADS1115(0x4B);
    i2c_dac = validarMCP4725(0x60) || validarMCP4725(0x61) || validarMCP4725(0x62);
    giveI2CMutex();
  }

  // Estado de los 4 termopares SPI bajo xDataMutex
  int tc[4] = {0, 0, 0, 0};
  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    for (int i = 0; i < 4; i++) {
      float temp = canales[i].temperatura;
      tc[i] = (temp > 0.0f && temp < 150.0f) ? 1 : 0;
    }
    giveDataMutex();
  }

  snprintf(json, sizeof(json),
           "{\"aht\":%d,\"bmp\":%d,\"ads\":%d,\"dac\":%d,"
           "\"tc\":[%d,%d,%d,%d],\"led\":\"%s\"}",
           i2c_aht ? 1 : 0, i2c_bmp ? 1 : 0,
           i2c_ads ? 1 : 0, i2c_dac ? 1 : 0,
           tc[0], tc[1], tc[2], tc[3],
           obtenerEstadoLedActual());
  server.send(200, "application/json", json);
}

/**
 * @brief Endpoint POST invocado por el operador para restablecer el enclavamiento Fail-Safe.
 */
static void handleFailSafeReset() {
  clearFailSafe();
  server.send(200, "text/plain", "OK");
}

/**
 * @brief Registra formalmente los endpoints de sistema en el servidor HTTP.
 */
void registrarRutasSystem() {
  server.on("/favicon.ico", []() { server.send(204); });
  server.on("/", handleMenu);
  server.on("/sensores", handleSensores);
  server.on("/consola", handleConsola);
  server.on("/logs", handleLogs);
  server.on("/data_env", handleDataEnv);
  server.on("/data_all", handleDataAll);
  server.on("/data_sensors", handleDataSensors);
  server.on("/failsafe_reset", handleFailSafeReset);
}

