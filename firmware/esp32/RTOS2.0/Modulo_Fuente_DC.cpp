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
static uint32_t s_tiempoSobrecorriente = 0;
static uint32_t s_tiempoCeldaAbierta = 0;
static uint8_t  s_fallosConsecutivosADS = 0;
static uint8_t  s_fallosConsecutivosDAC = 0;

void inicializarFuenteDC() {
  s_ultimoCodigoDAC_DC = 0xFFFF;
  s_tiempoInicioDC = 0;
  s_integralPI = 0.0f;
  s_tiempoSobrecorriente = 0;
  s_tiempoCeldaAbierta = 0;
  s_fallosConsecutivosADS = 0;
  s_fallosConsecutivosDAC = 0;
}

void resetLazoDC() {
  s_tiempoInicioDC = millis();
  s_integralPI = 0.0f;
  s_ultimoCodigoDAC_DC = 0xFFFF;
  s_tiempoSobrecorriente = 0;
  s_tiempoCeldaAbierta = 0;
  s_fallosConsecutivosADS = 0;
  s_fallosConsecutivosDAC = 0;
}

void escribirDAC_DC(uint16_t codigoDAC) {
  if (codigoDAC == s_ultimoCodigoDAC_DC) return;
  if (!isDACInicializado()) return;

  bool ok = false;
  if (takeI2CMutex(pdMS_TO_TICKS(20))) {
    ok = dac.setVoltage(codigoDAC, false);
    if (ok) {
      s_ultimoCodigoDAC_DC = codigoDAC;
      s_fallosConsecutivosDAC = 0;
    }
    giveI2CMutex();
  }

  if (!ok && fuenteActiva) {
    s_fallosConsecutivosDAC++;
    if (s_fallosConsecutivosDAC == 2) {
      i2cRecuperarBus(); // Intento de recuperación antes de declarar fallo fatal
    } else if (s_fallosConsecutivosDAC >= 3) {
      triggerFailSafe((uint8_t)ERR_I2C_DAC_LOST, "Perdida de comunicacion I2C con DAC MCP4725 (3 intentos)");
    }
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

  // 1. SALIDA DIRECTA AL DAC (Escalón directo calibrado, acotado a VCSS_DAC_MAX_PERMITIDO)
  codigoSalida = (uint16_t)constrain(localAmplitud, 0, VCSS_DAC_MAX_PERMITIDO);
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

  if (!okADS) {
    if (localActiva) {
      s_fallosConsecutivosADS++;
      if (s_fallosConsecutivosADS == 2) {
        i2cRecuperarBus(); // Intento de recuperación antes de declarar fallo fatal
      } else if (s_fallosConsecutivosADS >= 3) {
        triggerFailSafe((uint8_t)ERR_I2C_ADS_LOST, "Perdida de comunicacion I2C con ADS1115 (3 lecturas fallidas)");
      }
    }
    return;
  } else {
    s_fallosConsecutivosADS = 0;
  }

  // Conversión metrológica (0.1875 mV/LSB a Gain 2/3, Shunts 1.0 Ohm)
  float vs1 = max(0.0f, raw2 * 0.0001875f);
  float vs2 = max(0.0f, raw3 * 0.0001875f);
  float i1 = vs1 / 1.0f;
  float i2 = vs2 / 1.0f;
  float i_total = i1 + i2;

  // 3. SUPERVISIÓN DE SEGURIDAD (S3: Sobrecorriente y Celda Abierta)
  const uint32_t VENTANA_GRACIA_ARRANQUE_MS = 250;
  if (localActiva && tiempoActiva >= VENTANA_GRACIA_ARRANQUE_MS) {
    // Sobrecorriente medida (> VCSS_IMAX_PERMITIDA durante >= 200 ms)
    if (i_total > VCSS_IMAX_PERMITIDA) {
      if (s_tiempoSobrecorriente == 0) {
        s_tiempoSobrecorriente = millis();
      } else if (millis() - s_tiempoSobrecorriente >= 200) {
        char msg[64];
        snprintf(msg, sizeof(msg), "Sobrecorriente VCSS medida: %.2f A (>%.2f A por 200ms)",
                 i_total, VCSS_IMAX_PERMITIDA);
        triggerFailSafe((uint8_t)ERR_VCSS_OVERCURRENT, msg);
      }
    } else {
      s_tiempoSobrecorriente = 0;
    }

    // Celda abierta (< 0.05 A con consigna > 0.30 A durante >= 1000 ms, solo en DC)
    float i_esperada = (localSetpoint / 4095.0f) * VCSS_IMAX_NOMINAL;
    if (i_esperada > 0.30f && i_total < 0.05f) {
      if (s_tiempoCeldaAbierta == 0) {
        s_tiempoCeldaAbierta = millis();
      } else if (millis() - s_tiempoCeldaAbierta >= 1000) {
        char msg[64];
        snprintf(msg, sizeof(msg), "Celda abierta: %.2f A con consigna %.2f A por 1s",
                 i_total, i_esperada);
        triggerFailSafe((uint8_t)ERR_VCSS_OPEN_CIRCUIT, msg);
      }
    } else {
      s_tiempoCeldaAbierta = 0;
    }
  } else {
    s_tiempoSobrecorriente = 0;
    s_tiempoCeldaAbierta = 0;
  }

  // 4. TELEMETRÍA METROLÓGICA Y DIAGNÓSTICO DE SALUD DE CELDA
  if (takeDataMutex(pdMS_TO_TICKS(15))) {
    voltajeShunt1_raw = vs1;
    voltajeShunt2_raw = vs2;
    corrienteReal_R1 = i1;
    corrienteReal_R2 = i2;
    corrienteTotalReal = i_total;
    estadoPICorriente = PI_STATE_LOCKED; // Operación en lazo analógico puro calibrado

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
