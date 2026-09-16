/**
 * =================================================================================
 * CONTROL DE CORRIENTE PULSADA VCSS (Modulo_Fuente_Pulsado.cpp) — RTOS 1.4
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * DETALLES DE MODULACIÓN Y METROLOGÍA ESTROBOSCÓPICA:
 * - Genera formas de onda cuadrada con conmutación digital limpia sobre el MCP4725.
 * - En nivel ALTO, aplica la consigna completa (amplitudDAC) sin pasar por la rampa lenta
 *   de continua ni lazos PI (previene el windup por presencia de valles de 0A).
 * - En nivel BAJO, garantiza 0V (0 Amperios).
 * - Reconstruye la forma de onda estroboscópica (ETS) de 16 puntos desplazando el instante
 *   de lectura analógica en cada pulso transcurrido.
 * =================================================================================
 */

#include "Modulo_Fuente_Pulsado.h"
#include "Modulo_Fuentes.h"
#include "Modulo_PH.h"
#include "RTOS_Core.h"

static uint16_t s_ultimoCodigoPulsado = 0xFFFF;
static uint16_t s_contadorPulsos = 0;
static uint8_t  s_etsIdx = 0;

void inicializarFuentePulsada() {
  s_ultimoCodigoPulsado = 0xFFFF;
  s_contadorPulsos = 0;
  s_etsIdx = 0;
}

void resetLazoPulsado() {
  s_contadorPulsos = 0;
  s_etsIdx = 0;
  s_ultimoCodigoPulsado = 0xFFFF;
}

void actualizarTelemetriaPulsadaEstimada() {
  if (takeDataMutex(pdMS_TO_TICKS(10))) {
    if (!fuenteActiva || !modoPulsado) {
      giveDataMutex();
      return;
    }
    float iPico = (amplitudDAC_Setpoint / 4095.0f) * VCSS_IMAX_NOMINAL;
    corrienteReal_R1 = iPico / 2.0f;
    corrienteReal_R2 = iPico / 2.0f;
    voltajeShunt1_raw = corrienteReal_R1 * 1.0f;
    voltajeShunt2_raw = corrienteReal_R2 * 1.0f;
    corrienteTotalReal = iPico;
    for (int p = 0; p < ETS_NUM_PUNTOS; p++) {
      s_ondaETS[p] = iPico;
    }
    estadoSaludCelda = CELDA_OK;
    giveDataMutex();
  }
}

void ejecutarCicloFuentePulsada() {
  if (g_failsafe_latched) {
    if (s_ultimoCodigoPulsado != 0) {
      if (takeI2CMutex(pdMS_TO_TICKS(20))) {
        if (isDACInicializado()) {
          dac.setVoltage(0, false);
        }
        s_ultimoCodigoPulsado = 0;
        giveI2CMutex();
      }
    }
    vTaskDelay(pdMS_TO_TICKS(100));
    return;
  }

  // Snapshot atómico de parámetros bajo cerrojo de datos (xDataMutex)
  bool localActiva = false;
  bool localPulsado = false;
  int localAmplitud = 0;
  int localFreq = 1;
  int localDuty = 50;

  if (takeDataMutex(pdMS_TO_TICKS(10))) {
    localActiva = fuenteActiva;
    localPulsado = modoPulsado;
    localAmplitud = amplitudDAC;
    localFreq = frecuencia;
    localDuty = dutyCycle;
    giveDataMutex();
  } else {
    return;
  }

  if (!localActiva || !localPulsado) {
    if (!localActiva && s_ultimoCodigoPulsado != 0) {
      if (takeI2CMutex(pdMS_TO_TICKS(20))) {
        if (isDACInicializado()) {
          dac.setVoltage(0, false);
        }
        s_ultimoCodigoPulsado = 0;
        giveI2CMutex();
      }
    }
    return;
  }

  int freqVal = constrain(localFreq, 1, 100);
  uint32_t periodo_ms = 1000UL / (uint32_t)freqVal;
  if (periodo_ms == 0) periodo_ms = 1;

  uint32_t tAlto_ms = (periodo_ms * (uint32_t)localDuty) / 100UL;
  if (tAlto_ms == 0) tAlto_ms = 1;
  uint32_t tBajo_ms = (periodo_ms > tAlto_ms) ? (periodo_ms - tAlto_ms) : 1;

  s_contadorPulsos++;

  // 1. Transición al Flanco de Subida y Nivel ALTO (DAC a amplitud consignada)
  if (takeI2CMutex(pdMS_TO_TICKS(10))) {
    if (isDACInicializado()) {
      dac.setVoltage((uint16_t)constrain(localAmplitud, 0, 4095), false);
    }
    s_ultimoCodigoPulsado = (uint16_t)localAmplitud;
    giveI2CMutex();
  }

  // 2. MUESTREO ESTROBOSCÓPICO ETS (1 muestra por pulso decodificada en 16 puntos)
  uint16_t divisorPulsos = (freqVal > 10) ? (freqVal / 10) : 1;
  bool tocaMedirEstePulso = (s_contadorPulsos % divisorPulsos == 0);
  bool puedeMuestrearEnAlto = (tAlto_ms >= 5) && isADSConectado();

  if (tocaMedirEstePulso && puedeMuestrearEnAlto) {
    uint32_t tMargen = (tAlto_ms > 5) ? (tAlto_ms - 5) : 0;
    uint32_t tOffset = 2 + (s_etsIdx * tMargen) / ETS_NUM_PUNTOS;

    if (tOffset > 0) {
      vTaskDelay(pdMS_TO_TICKS(tOffset));
    }

    int16_t raw2 = 0, raw3 = 0;
    bool lecturaOK = false;

    if (takeI2CMutex(pdMS_TO_TICKS(10))) {
      raw2 = ads.readADC_SingleEnded(2);
      raw3 = ads.readADC_SingleEnded(3);
      giveI2CMutex();
      lecturaOK = true;
    }

    if (lecturaOK) {
      float vs1 = max(0.0f, raw2 * 0.0001875f);
      float vs2 = max(0.0f, raw3 * 0.0001875f);
      float i1 = vs1 / 1.0f;
      float i2 = vs2 / 1.0f;
      float iMuestra = i1 + i2;

      if (takeDataMutex(pdMS_TO_TICKS(10))) {
        voltajeShunt1_raw = vs1;
        voltajeShunt2_raw = vs2;
        corrienteReal_R1 = i1;
        corrienteReal_R2 = i2;
        corrienteTotalReal = iMuestra;
        s_ondaETS[s_etsIdx] = iMuestra;

        // Diagnóstico de Salud de Celda en Flanco Alto
        float iTeorico = (localAmplitud / 4095.0f) * VCSS_IMAX_NOMINAL;
        if (iTeorico > 0.10f && iMuestra < (0.75f * iTeorico)) {
          estadoSaludCelda = CELDA_SATURADA;
        } else if (iMuestra > 0.20f && fabsf(i1 - i2) > (0.40f * iMuestra)) {
          estadoSaludCelda = CELDA_DESBALANCE;
        } else {
          estadoSaludCelda = CELDA_OK;
        }
        giveDataMutex();
      }

      s_etsIdx = (s_etsIdx + 1) % ETS_NUM_PUNTOS;
    }

    uint32_t tConsumido = tOffset + 3;
    uint32_t tRestanteAlto = (tAlto_ms > tConsumido) ? (tAlto_ms - tConsumido) : 0;
    if (tRestanteAlto > 0) {
      vTaskDelay(pdMS_TO_TICKS(tRestanteAlto));
    }
  } else {
    if (!puedeMuestrearEnAlto && tocaMedirEstePulso) {
      actualizarTelemetriaPulsadaEstimada();
    }
    vTaskDelay(pdMS_TO_TICKS(tAlto_ms));
  }

  // 3. Transición al Flanco de Bajada y Nivel BAJO (DAC a 0V)
  if (takeI2CMutex(pdMS_TO_TICKS(10))) {
    if (isDACInicializado()) {
      dac.setVoltage(0, false);
    }
    s_ultimoCodigoPulsado = 0;
    giveI2CMutex();
  }
  vTaskDelay(pdMS_TO_TICKS(tBajo_ms));
}
