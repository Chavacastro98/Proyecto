/**
 * =================================================================================
 * MÓDULO DE SALIDA DE CORRIENTE VCSS (Modulo_Fuentes.cpp) — Versión RTOS 1.4
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * ARQUITECTURA GENERAL:
 * - Actúa como fachada y orquestador central de potencia VCSS.
 * - Conmutación segura en cruce por cero (ZCS) en el relé de +12V (GPIO 20).
 * - Delega la regulación continua a Modulo_Fuente_DC y la modulación a Modulo_Fuente_Pulsado.
 * - Mantiene el interlock estricto de autocalibración de shunts.
 * =================================================================================
 */

#include "Modulo_Fuentes.h"
#include "Modulo_Fuente_DC.h"
#include "Modulo_Fuente_Pulsado.h"
#include "RTOS_Core.h"
#include "config.h"

/** @brief Último código digital de 12 bits enviado al DAC */
static uint16_t ultimoCodigoDAC = 0xFFFF;

/** @brief Bandera que valida la detección física y comunicación I2C con el MCP4725 */
static bool dacInicializado = false;

/**
 * @brief Configura pines de control, realiza sondeo I2C del DAC MCP4725 y restaura calibración.
 */
void inicializarFuente() {
  pinMode(PIN_RELE_VCSS, OUTPUT);
  digitalWrite(PIN_RELE_VCSS, !RELE_NIVEL_ACTIVO); // Estado inicial: Desenergizado (0V)
  estadoReleVDD = false;

  if (takeI2CMutex(pdMS_TO_TICKS(100))) {
    uint8_t dacAddr = 0;
    uint8_t posibles[] = {0x60, 0x61, 0x62, 0x63};
    for (uint8_t i = 0; i < 4; i++) {
      Wire.beginTransmission(posibles[i]);
      if (Wire.endTransmission() == 0) {
        if (Wire.requestFrom((int)posibles[i], 3) == 3) {
          uint8_t b1 = Wire.read();
          Wire.read(); Wire.read();
          if ((b1 & 0x80) != 0 && b1 != 0xFF) {
            dacAddr = posibles[i];
            break;
          }
        }
      }
      delayMicroseconds(200);
    }

    if (dacAddr != 0) {
      dacInicializado = dac.begin(dacAddr);
      if (dacInicializado) {
        dac.setVoltage(0, false);
        ultimoCodigoDAC = 0;
        Serial.printf("[FUENTE] DAC MCP4725 (12-bit) en línea en I2C 0x%02X.\n", dacAddr);
      }
    } else {
      dacInicializado = false;
      Serial.println("[FUENTE] ❌ Error: DAC MCP4725 no detectado en I2C (0x60..0x63).");
    }
    giveI2CMutex();
  }

  // Cargar factor de calibración de transconductancia y estado de compensación desde Flash NVS
  if (memoria.isKey("gvcss")) {
    factorGananciaVCSS = memoria.getFloat("gvcss", 1.000f);
    Serial.printf("[FUENTE] Factor de Ganancia VCSS cargado de NVS: %.4f\n", factorGananciaVCSS);
  } else {
    factorGananciaVCSS = 1.000f;
  }

  if (memoria.isKey("comp_f")) {
    compensacionLazoCerrado = memoria.getBool("comp_f", false);
  } else {
    compensacionLazoCerrado = false;
  }

  // Inicializar submódulos especializados
  inicializarFuenteDC();
  inicializarFuentePulsada();
}

/**
 * @brief Retorna si el DAC MCP4725 está operativo en el bus I2C.
 */
bool isDACInicializado() {
  return dacInicializado;
}

/**
 * @brief Enciende o apaga la etapa de potencia aplicando la secuencia ZCS estricta.
 */
void setEstadoFuente(bool encender) {
  if (g_failsafe_latched && encender) {
    Serial.println("[FUENTE] ❌ Rechazado: Sistema bloqueado por enclavamiento fail-safe.");
    return;
  }

  if (encender) {
    // --- SECUENCIA DE ENCENDIDO SEGURO (ZCS) ---
    if (takeI2CMutex(pdMS_TO_TICKS(50))) {
      dac.setVoltage(0, false);
      ultimoCodigoDAC = 0;
      giveI2CMutex();
    }

    // Cerrar relé de +12V
    digitalWrite(PIN_RELE_VCSS, RELE_NIVEL_ACTIVO);
    if (takeDataMutex(pdMS_TO_TICKS(20))) {
      estadoReleVDD = true;
      giveDataMutex();
    }

    // Retardo de asentamiento mecánico de contactos (80 ms)
    vTaskDelay(pdMS_TO_TICKS(80));

    if (takeDataMutex(pdMS_TO_TICKS(20))) {
      fuenteActiva = true;
      float factor = (factorGananciaVCSS > 0.5f && factorGananciaVCSS < 1.5f) ? factorGananciaVCSS : 1.0f;
      if (modoPulsado) {
        amplitudDAC = constrain((int)roundf(amplitudDAC_Setpoint / factor), 0, 4095);
        estadoPICorriente = PI_STATE_OFF;
        resetLazoPulsado();
      } else {
        amplitudDAC = constrain((int)roundf(amplitudDAC_Setpoint / factor), 0, 4095);
        estadoPICorriente = PI_STATE_RAMP;
        resetLazoDC();
      }
      estadoSaludCelda = CELDA_OK;
      giveDataMutex();
    }
  } else {
    // --- SECUENCIA DE APAGADO SEGURO (ZCS) ---
    if (takeDataMutex(pdMS_TO_TICKS(20))) {
      fuenteActiva = false;
      amplitudDAC = 0;
      corrienteReal_R1 = 0.0f;
      corrienteReal_R2 = 0.0f;
      corrienteTotalReal = 0.0f;
      voltajeShunt1_raw = 0.0f;
      voltajeShunt2_raw = 0.0f;
      estadoPICorriente = PI_STATE_OFF;
      giveDataMutex();
    }

    if (takeI2CMutex(pdMS_TO_TICKS(50))) {
      dac.setVoltage(0, false);
      ultimoCodigoDAC = 0;
      giveI2CMutex();
    }

    // Pausa para disipación de corriente remanente (30 ms)
    vTaskDelay(pdMS_TO_TICKS(30));

    // Abrir contactos del relé mecánico a corriente cero
    digitalWrite(PIN_RELE_VCSS, !RELE_NIVEL_ACTIVO);
    if (takeDataMutex(pdMS_TO_TICKS(20))) {
      estadoReleVDD = false;
      giveDataMutex();
    }
  }
}

/**
 * @brief Configura la intensidad objetivo para modo continuo (DC).
 */
void setCorrienteContinua(float amperios) {
  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    modoPulsado = false;
    int dacVal = (int)constrain((amperios / VCSS_IMAX_NOMINAL) * 4095.0f, 0.0f, 4095.0f);
    amplitudDAC_Setpoint = dacVal;
    float factor = (factorGananciaVCSS > 0.5f && factorGananciaVCSS < 1.5f) ? factorGananciaVCSS : 1.0f;
    amplitudDAC = constrain((int)roundf(amplitudDAC_Setpoint / factor), 0, 4095);
    if (fuenteActiva) {
      resetLazoDC();
    }
    giveDataMutex();
  }
}

/**
 * @brief Configura los parámetros de la onda pulsada de corriente.
 */
void setConfigPulsado(float amperiosPico, float hz, float duty) {
  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    int dacVal = (int)constrain((amperiosPico / VCSS_IMAX_NOMINAL) * 4095.0f, 0.0f, 4095.0f);
    amplitudDAC_Setpoint = dacVal;
    float factor = (factorGananciaVCSS > 0.5f && factorGananciaVCSS < 1.5f) ? factorGananciaVCSS : 1.0f;
    amplitudDAC = constrain((int)roundf(amplitudDAC_Setpoint / factor), 0, 4095);
    frecuencia = (hz > 0.0f) ? (int)hz : 1;
    dutyCycle = (int)constrain(duty, 0.0f, 100.0f);
    estadoPICorriente = PI_STATE_OFF;
    if (fuenteActiva) {
      resetLazoPulsado();
    }
    giveDataMutex();
  }
}

/**
 * @brief Conmuta el modo de modulación (Pulsado vs Continuo).
 */
void conmutarModoFuente(bool usarPulsado) {
  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    modoPulsado = usarPulsado;
    float factor = (factorGananciaVCSS > 0.5f && factorGananciaVCSS < 1.5f) ? factorGananciaVCSS : 1.0f;
    amplitudDAC = constrain((int)roundf(amplitudDAC_Setpoint / factor), 0, 4095);
    if (usarPulsado) {
      estadoPICorriente = PI_STATE_OFF;
      resetLazoPulsado();
    } else {
      if (fuenteActiva) {
        resetLazoDC();
      }
    }
    giveDataMutex();
  }
}

/**
 * @brief Habilita o deshabilita el lazo digital de compensación automática de ganancia.
 */
void setCompensacionLazoCerrado(bool habilitar) {
  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    compensacionLazoCerrado = habilitar;
    giveDataMutex();
  }
  memoria.putBool("comp_f", habilitar);
}

/**
 * @brief Envoltura de compatibilidad hacia Modulo_Fuente_DC.
 */
void actualizarFuenteDAC() {
  ejecutarCicloFuenteDC();
}

/**
 * @brief Envoltura de compatibilidad (la regulación ahora se gestiona directamente en Modulo_Fuente_DC).
 */
void actualizarSensadoVCSS() {
  // En RTOS 1.4, Modulo_Fuente_DC ejecuta el sensado analógico y PI a 10 Hz dentro de Task_Fuente
}

/**
 * @brief Envoltura de compatibilidad hacia Modulo_Fuente_Pulsado.
 */
void actualizarTelemetriaPulsada() {
  actualizarTelemetriaPulsadaEstimada();
}

/**
 * @brief Rutina metrológica de calibración de transconductancia.
 */
bool autoCalibrarVCSS() {
  if (g_failsafe_latched || phModuloActivo) return false;

  bool activa = false;
  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    activa = fuenteActiva;
    giveDataMutex();
  }

  // Interlock estricto: la fuente DEBE estar apagada previamente
  if (activa) {
    Serial.println("[VCSS] ❌ Calibración rechazada: La fuente está encendida. Apague la fuente antes de autocalibrar los shunts.");
    return false;
  }

  Serial.println("[VCSS] Iniciando auto-calibración de transconductancia (RTOS 1.4)...");

  // Asegurar relé mecánico cerrado a 0A
  digitalWrite(PIN_RELE_VCSS, RELE_NIVEL_ACTIVO);
  vTaskDelay(pdMS_TO_TICKS(80));

  // Consigna patrón de prueba: 1.50 A
  const float I_CALIB = 1.50f;
  uint16_t dacCal = (uint16_t)roundf((I_CALIB / VCSS_IMAX_NOMINAL) * 4095.0f);

  if (takeI2CMutex(pdMS_TO_TICKS(100))) {
    dac.setVoltage(dacCal, false);
    ultimoCodigoDAC = dacCal;
    giveI2CMutex();
  }

  // Tiempo de asentamiento térmico y de transitorios (600 ms)
  vTaskDelay(pdMS_TO_TICKS(600));

  // Promediar 5 lecturas de corriente
  float sumaCorriente = 0.0f;
  int muestrasValidas = 0;

  for (int m = 0; m < 5; m++) {
    int16_t r2 = 0, r3 = 0;
    bool ok = false;
    if (takeI2CMutex(pdMS_TO_TICKS(50))) {
      r2 = ads.readADC_SingleEnded(2);
      r3 = ads.readADC_SingleEnded(3);
      ok = true;
      giveI2CMutex();
    }
    if (ok) {
      float v1 = max(0.0f, r2 * 0.0001875f);
      float v2 = max(0.0f, r3 * 0.0001875f);
      sumaCorriente += (v1 / 1.0f) + (v2 / 1.0f);
      muestrasValidas++;
    }
    vTaskDelay(pdMS_TO_TICKS(40));
  }

  // Extinguir corriente antes de desconectar
  if (takeI2CMutex(pdMS_TO_TICKS(50))) {
    dac.setVoltage(0, false);
    ultimoCodigoDAC = 0;
    giveI2CMutex();
  }
  vTaskDelay(pdMS_TO_TICKS(30));

  // Abrir relé mecánico ZCS
  digitalWrite(PIN_RELE_VCSS, !RELE_NIVEL_ACTIVO);
  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    estadoReleVDD = false;
    giveDataMutex();
  }

  if (muestrasValidas < 3) {
    Serial.println("[VCSS] ❌ Error de comunicación I2C durante calibración.");
    return false;
  }

  float iMedida = sumaCorriente / (float)muestrasValidas;
  Serial.printf("[VCSS] Corriente medida durante calibración: %.4f A (Objetivo: %.2f A)\n", iMedida, I_CALIB);

  if (iMedida < 0.50f || iMedida > 3.00f) {
    Serial.println("[VCSS] ❌ Calibración fallida: Corriente fuera de rango plausible.");
    return false;
  }

  float nuevoFactor = iMedida / I_CALIB;
  nuevoFactor = constrain(nuevoFactor, 0.70f, 1.30f);

  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    factorGananciaVCSS = nuevoFactor;
    giveDataMutex();
  }

  memoria.putFloat("gvcss", nuevoFactor);
  Serial.printf("[VCSS] ✅ Calibración exitosa. Nuevo Factor de Ganancia: %.4f guardado en NVS.\n", nuevoFactor);
  return true;
}

/**
 * @brief Restablece la ganancia de transconductancia a su valor de fábrica.
 */
void resetCalibracionVCSS() {
  bool activa = false;
  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    activa = fuenteActiva;
    giveDataMutex();
  }

  // Interlock estricto: la fuente DEBE estar apagada previamente
  if (activa) {
    Serial.println("[VCSS] ❌ Reset de calibración rechazado: La fuente está encendida. Apague la fuente antes de resetear.");
    return;
  }

  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    factorGananciaVCSS = 1.000f;
    giveDataMutex();
  }
  memoria.putFloat("gvcss", 1.000f);
  Serial.println("[VCSS] ✅ Factor de Ganancia restablecido a 1.000 (Fábrica).");
}
