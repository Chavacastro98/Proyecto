#include "Controller_System.h"
#include "views/View_Menu.h"
#include "views/View_Sensores.h"
#include "Modulo_Ambiental.h"
#include "Modulo_Termico.h"
#include "config.h"

/**
 * =================================================================================
 * IMPLEMENTACIÓN: CONTROLADOR DEL SISTEMA Y DIAGNÓSTICO (Controller_System.cpp)
 * =================================================================================
 */

// Handlers de páginas HTML
static void handleMenu() {
  server.send_P(200, "text/html", HTML_MENU);
}

static void handleSensores() {
  server.send_P(200, "text/html", HTML_SENSORES);
}

// Handler de telemetría ambiental (JSON)
static void handleDataEnv() {
  char json[128];
  snprintf(json, sizeof(json),
           "{\"t\":\"%.1f\",\"h\":\"%.0f\",\"p\":\"%.1f\"}",
           amb_temp, amb_hum, amb_pres);
  server.send(200, "application/json", json);
}

// Handler de diagnóstico integral de sensores (JSON bajo demanda)
static void handleDataSensors() {
  char json[192];

  // --- Escaneo I2C en caliente (no destructivo) ---
  Wire.beginTransmission(0x38); // AHT20
  bool i2c_aht = (Wire.endTransmission() == 0);

  Wire.beginTransmission(0x76); // BMP280 dir 1
  bool i2c_bmp = (Wire.endTransmission() == 0);
  if (!i2c_bmp) {
    Wire.beginTransmission(0x77); // BMP280 dir 2
    i2c_bmp = (Wire.endTransmission() == 0);
  }

  Wire.beginTransmission(0x48); // ADS1115
  bool i2c_ads = (Wire.endTransmission() == 0);

  Wire.beginTransmission(0x60); // MCP4725
  bool i2c_dac = (Wire.endTransmission() == 0);

  // --- Termopares SPI: reutilizar última lectura del lazo térmico ---
  int tc[4];
  portENTER_CRITICAL(&muxTermico);
  for (int i = 0; i < 4; i++) {
    float t = canales[i].temperatura;
    tc[i] = (t > 0.0f && t < 150.0f) ? 1 : 0;
  }
  portEXIT_CRITICAL(&muxTermico);

  snprintf(json, sizeof(json),
           "{\"aht\":%d,\"bmp\":%d,\"ads\":%d,\"dac\":%d,"
           "\"tc\":[%d,%d,%d,%d]}",
           i2c_aht ? 1 : 0, i2c_bmp ? 1 : 0,
           i2c_ads ? 1 : 0, i2c_dac ? 1 : 0,
           tc[0], tc[1], tc[2], tc[3]);
  server.send(200, "application/json", json);
}

void registrarRutasSystem() {
  server.on("/favicon.ico", []() { server.send(204); });
  server.on("/", handleMenu);
  server.on("/sensores", handleSensores);
  server.on("/data_env", handleDataEnv);
  server.on("/data_sensors", handleDataSensors);
}
