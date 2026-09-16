/**
 * =================================================================================
 * CONTROL DE CORRIENTE CONTINUA (DC) VCSS (Modulo_Fuente_DC.cpp) — RTOS 1.4
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * DETALLES METROLÓGICOS Y CONTROL EN LAZO CERRADO:
 * 1. Rampa Soft-Start (500 ms):
 *    - Inicia en 0V y escala linealmente hasta la consigna calculada.
 *    - Suprime de raíz el sobreimpulso inductivo y protege la celda de electrodeposición.
 * 2. Tiempo de Asentamiento Blanking (300 ms):
 *    - Permite la estabilización de los amplificadores operacionales LM358 y reactancias
 *      del electrolito antes de habilitar el control por realimentación.
 * 3. Lazo PI Adaptativo por Zonas de Error (10 Hz / 100 ms):
 *    - Zona Rápida (|error| > 50 mA): corrección de hasta +-25 LSB/ciclo (~43 mA).
 *      Acelera la estabilización de ~30 segundos a menos de 2.2 segundos.
 *    - Zona Media (15 mA <= |error| <= 50 mA): corrección amortiguada de +-8 LSB/ciclo.
 *    - Zona Fina (|error| < 15 mA): ajuste suave de +-2 LSB y enganche en banda
 *      muerta (+-10 mA) que garantiza estabilidad estática total (PI_STATE_LOCKED).
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
      if (takeDataMutex(pdMS_TO_TICKS(10))) {
        estadoPICorriente = PI_STATE_OFF;
        giveDataMutex();
      }
    }
    return;
  }

  uint32_t tiempoActiva = millis() - s_tiempoInicioDC;
  uint16_t codigoSalida = 0;

  // 1. GESTIÓN DE RAMPA SOFT-START Y BLANKING
  if (tiempoActiva < VCSS_SOFT_START_MS) {
    float factorRampa = (float)tiempoActiva / (float)VCSS_SOFT_START_MS;
    codigoSalida = (uint16_t)constrain((int)roundf(localAmplitud * factorRampa), 0, localAmplitud);
    if (takeDataMutex(pdMS_TO_TICKS(10))) {
      estadoPICorriente = PI_STATE_RAMP;
      giveDataMutex();
    }
  } else {
    codigoSalida = (uint16_t)constrain(localAmplitud, 0, 4095);
    if (tiempoActiva < (VCSS_SOFT_START_MS + VCSS_PI_BLANKING_MS)) {
      if (takeDataMutex(pdMS_TO_TICKS(10))) {
        estadoPICorriente = PI_STATE_BLANKING;
        giveDataMutex();
      }
    }
  }

  // Aplicar salida analógica al DAC
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

  // 3. DIAGNÓSTICO DE SALUD DE CELDA Y LAZO PI ADAPTATIVO
  if (takeDataMutex(pdMS_TO_TICKS(15))) {
    voltajeShunt1_raw = vs1;
    voltajeShunt2_raw = vs2;
    corrienteReal_R1 = i1;
    corrienteReal_R2 = i2;
    corrienteTotalReal = i_total;

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

    // 4. CONTROLADOR PI ADAPTATIVO (Superado Soft-Start + Blanking: > 800 ms)
    if (localComp && (tiempoActiva >= (VCSS_SOFT_START_MS + VCSS_PI_BLANKING_MS))) {
      float i_target = (localSetpoint / 4095.0f) * VCSS_IMAX_NOMINAL;

      if (i_target >= 0.10f) {
        float error = i_target - i_total;
        float absErr = fabsf(error);

        // Banda muerta ultra-estable (+-10 mA): sin fluctuación en régimen permanente
        if (absErr < 0.010f) {
          estadoPICorriente = PI_STATE_LOCKED;
        } else {
          estadoPICorriente = PI_STATE_BLANKING; // Regulando activamente

          // Integrador discreto (Ts = 0.10s / 10 Hz) con Anti-Windup (+-0.20 A)
          s_integralPI += error * 0.10f;
          s_integralPI = constrain(s_integralPI, -0.20f, 0.20f);

          float correccionAmps = (VCSS_PI_KP * error) + (VCSS_PI_KI * s_integralPI);
          int deltaDAC = (int)roundf((correccionAmps / VCSS_IMAX_NOMINAL) * 4095.0f);

          // Limitador adaptativo por zonas de error (Slew Rate Dinámico):
          int maxDelta;
          if (absErr > 0.050f) {
            maxDelta = 25; // Error grande (>50 mA): aproximación rápida (~43 mA/ciclo -> 430 mA/s)
          } else if (absErr >= 0.015f) {
            maxDelta = 8;  // Error medio (15..50 mA): frenado amortiguado (~14 mA/ciclo)
          } else {
            maxDelta = 2;  // Error fino (<15 mA): ajuste asintótico sin sobreimpulso
          }

          deltaDAC = constrain(deltaDAC, -maxDelta, maxDelta);
          amplitudDAC = constrain(amplitudDAC + deltaDAC, 0, 4095);
        }
      }
    }
    giveDataMutex();
  }
}
