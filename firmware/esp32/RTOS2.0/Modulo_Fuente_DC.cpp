/**
 * =================================================================================
 * CONTROL DE CORRIENTE CONTINUA (DC) VCSS (Modulo_Fuente_DC.cpp) — RTOS 2.0
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * DETALLES METROLÓGICOS Y CONTROL EN LAZO CERRADO ANALÓGICO:
 * 1. Escalón Directo Calibrado al DAC MCP4725:
 *    - Se aplica la consigna directa sin rampa de software.
 *    - La capacitancia de la doble capa electroquímica (Cdl) en la interfase
 *      electrodo/solución amortigua transitorios naturalmente, favoreciendo
 *      la sobretensión inicial necesaria para una nucleación óptima de zinc.
 * 2. Adquisición y Balance de Shunts (Canales A2 y A3 del ADS1115):
 *    - Cada rama MOSFET cuenta con su propio lazo local de transconductancia y shunt de 1.0 Ω.
 *    - Muestreo diferencial individual para calcular corrientes de rama i1 e i2.
 * 3. Diagnóstico Continuo de Salud de Celda (SaludCelda_t):
 *    - Detección de saturación / pasivación: tensión de cumplimiento excedida
 *      (i_total < 70% de la esperada a fondo de escala DAC).
 *    - Detección de desbalance térmico o asimetría de compuerta entre ramas (|i1 - i2| > 0.35 A).
 * =================================================================================
 */

#include "Modulo_Fuente_DC.h"
#include "Modulo_Fuentes.h"
#include "Modulo_PH.h"
#include "RTOS_Core.h"

static uint16_t s_ultimoCodigoDAC_DC = 0xFFFF;
static uint32_t s_tiempoInicioDC = 0;
static float    s_integralPI = 0.0f;

void inicializarFuenteDC() {
  s_ultimoCodigoDAC_DC = 0xFFFF;
  s_tiempoInicioDC = 0;
  s_integralPI = 0.0f;
}

void resetLazoDC() {
  s_tiempoInicioDC = millis();
  s_integralPI = 0.0f;
  s_ultimoCodigoDAC_DC = 0xFFFF;
}

void escribirDAC_DC(uint16_t codigoDAC) {
  if (codigoDAC == s_ultimoCodigoDAC_DC) return;
  if (!isDACInicializado()) return;

  if (takeI2CMutex(pdMS_TO_TICKS(20))) {
    dac.setVoltage(codigoDAC, false);
    s_ultimoCodigoDAC_DC = codigoDAC;
    giveI2CMutex();
  }
}

void ejecutarCicloFuenteDC() {
  if (g_failsafe_latched) {
    escribirDAC_DC(0);
    return;
  }

  bool localActiva = false;
  bool localPulsado = false;
  bool localComp = false;
  int  localSetpoint = 0;
  int  localAmplitud = 0;

  if (takeDataMutex(pdMS_TO_TICKS(10))) {
    localActiva = fuenteActiva;
    localPulsado = modoPulsado;
    localComp = compensacionLazoCerrado;
    localSetpoint = amplitudDAC_Setpoint;
    localAmplitud = amplitudDAC;
    giveDataMutex();
  } else {
    return;
  }

  // Si la fuente no está activa o se encuentra en modo pulsado, salir
  if (!localActiva || localPulsado) {
    if (!localActiva) {
      escribirDAC_DC(0);
      resetLazoDC();
      if (takeDataMutex(pdMS_TO_TICKS(10))) {
        estadoPICorriente = PI_STATE_OFF;
        giveDataMutex();
      }
    }
    return;
  }

  uint32_t tiempoActiva = millis() - s_tiempoInicioDC;
  uint16_t codigoSalida = 0;

  // 1. SALIDA DIRECTA AL DAC (Escalón directo calibrado, sin rampa de software)
  codigoSalida = (uint16_t)constrain(localAmplitud, 0, 4095);
  escribirDAC_DC(codigoSalida);

  // 2. ADQUISICIÓN ANALÓGICA DE SHUNTS EN ADS1115 (Canales A2 y A3)
  int16_t raw2 = 0, raw3 = 0;
  bool okADS = false;

  if (isADSConectado()) {
    if (takeI2CMutex(pdMS_TO_TICKS(25))) {
      raw2 = ads.readADC_SingleEnded(2);
      raw3 = ads.readADC_SingleEnded(3);
      okADS = true;
      giveI2CMutex();
    }
  }

  if (!okADS) return;

  // Conversión metrológica (0.1875 mV/LSB a Gain 2/3, Shunts 1.0 Ohm)
  float vs1 = max(0.0f, raw2 * 0.0001875f);
  float vs2 = max(0.0f, raw3 * 0.0001875f);
  float i1 = vs1 / 1.0f;
  float i2 = vs2 / 1.0f;
  float i_total = i1 + i2;

  // 3. DIAGNÓSTICO DE SALUD DE CELDA Y TELEMETRÍA METROLÓGICA (Lazo Analógico Puro)
  if (takeDataMutex(pdMS_TO_TICKS(15))) {
    voltajeShunt1_raw = vs1;
    voltajeShunt2_raw = vs2;
    corrienteReal_R1 = i1;
    corrienteReal_R2 = i2;
    corrienteTotalReal = i_total;
    estadoPICorriente = PI_STATE_LOCKED; // Operación en lazo analógico puro calibrado (sin oscilaciones)

    // Diagnóstico continuo de celda electroquímica
    if (i_total > 0.05f) {
      float desbalance = fabsf(i1 - i2);
      float i_esperada = (localSetpoint / 4095.0f) * VCSS_IMAX_NOMINAL;
      if (i_total < (i_esperada * 0.70f) && localAmplitud >= 3800) {
        estadoSaludCelda = CELDA_SATURADA; // Cumplimiento alcanzado o pasivación
      } else if (desbalance > 0.35f) {
        estadoSaludCelda = CELDA_DESBALANCE; // Desbalance de ramas MOSFET
      } else {
        estadoSaludCelda = CELDA_OK;
      }
    } else {
      estadoSaludCelda = CELDA_OK;
    }

    giveDataMutex();
  }
}
