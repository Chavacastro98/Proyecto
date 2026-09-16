/**
 * =================================================================================
 * MÓDULO DE MEDICIÓN Y CALIBRACIÓN DE PH (Modulo_PH.cpp) — Versión RTOS 2.0
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * ARQUITECTURA Y PRINCIPIO DE OPERACIÓN:
 * 1. Muestreo Potenciométrico con ADS1115 (16 bits @ 860 SPS):
 *    - En Modo Pseudo-Diferencial (ADS_PH_MODO_DIFERENCIAL = 1):
 *      Canal A1 muestrea la señal acondicionada de la sonda (Po).
 *      Canal A0 muestrea la referencia analógica local aislada (Kelvin Ground)
 *      para cancelar ruidos de modo común y caídas óhmicas por corrientes galvánicas.
 *    - En Modo Single-Ended (ADS_PH_MODO_DIFERENCIAL = 0):
 *      Muestreo referenciado a tierra común en Canal A1.
 * 2. Cascada de Filtrado Digital Multietapa:
 *    - Bloque acumulador: Promedio de 10 muestras continuas a 860 SPS.
 *    - Filtro de mediana móvil de 3 puntos: supresión de transitorios y picos EMI.
 *    - Filtro pasabajas adaptativo IIR: respuesta rápida ante saltos y estabilidad en régimen.
 * 3. Metrología Nernstiana y Calibración NVS:
 *    - Modelos: Teórico, 2 Puntos (ácido) y 3 Puntos (ácido y básico asimétrico).
 *    - Persistencia metrológica desacoplada en Flash NVS por modo.
 *    - Interlock de seguridad con etapa de potencia (evita campos de fuga en la celda).
 * =================================================================================
 */

#include "Modulo_PH.h"
#include "Modulo_Termico.h"
#include "RTOS_Core.h"
#include "config.h"

/**
 * @brief Algoritmo óptimo de ordenamiento para calcular la mediana de 3 muestras.
 * Ejecuta en un máximo de 3 comparaciones sin usar memoria dinámica ni bucles.
 */
static float mediana3(float a, float b, float c) {
  if (a > b) { float t = a; a = b; b = t; }
  if (b > c) { float t = b; b = c; c = t; }
  if (a > b) { float t = a; a = b; b = t; }
  return b;
}

/**
 * @brief Estado interno de filtrado y acumulación para el sensor dedicado de pH.
 */
struct EstadoCanalPH {
  long acumulador;     /**< Sumatoria de códigos brutos del ADC ADS1115 */
  uint8_t muestras;    /**< Contador de muestras acumuladas en el bloque actual (0..10) */
  bool primeraLectura; /**< Inicializador de estado para bypass de filtro en la 1ra muestra */
  float historial[3];  /**< Búfer circular para el filtro no lineal de mediana */
  uint8_t histIdx;     /**< Índice de inserción en el búfer de mediana */
  uint8_t histCount;   /**< Cantidad de muestras válidas en el búfer de mediana (0..3) */
};

/** @brief Instancia única de filtrado para el sensor dedicado (Canal A1) */
static EstadoCanalPH estadoPH = {0, 0, true, {0.0f, 0.0f, 0.0f}, 0, 0};

/** @brief Bandera que valida la presencia física del ADC ADS1115 en el bus I2C */
static bool adsConectado = false;

/**
 * @brief Escanea e inicializa el ADS1115 en el bus I2C (0x48..0x4B) a 860 SPS.
 */
void inicializarModuloPH() {
  if (takeI2CMutex(pdMS_TO_TICKS(100))) {
    uint8_t adsAddr = 0;
    uint8_t posibles[] = {0x48, 0x49, 0x4A, 0x4B};
    for (uint8_t i = 0; i < 4; i++) {
      Wire.beginTransmission(posibles[i]);
      Wire.write(0x01); // Apuntar al registro de configuración
      if (Wire.endTransmission() == 0) {
        if (Wire.requestFrom((int)posibles[i], 2) == 2) {
          uint8_t msb = Wire.read();
          uint8_t lsb = Wire.read();
          uint16_t cfg = ((uint16_t)msb << 8) | lsb;
          if (cfg != 0x0000 && cfg != 0xFFFF && (cfg & 0x8000) != 0) {
            adsAddr = posibles[i];
            break;
          }
        }
      }
      delayMicroseconds(200);
    }

    if (adsAddr != 0 && ads.begin(adsAddr)) {
      ads.setGain(GAIN_TWOTHIRDS); // Rango de entrada +-6.144V (1 LSB = 0.1875 mV)
      ads.setDataRate(RATE_ADS1115_860SPS); // Máxima velocidad para minimizar tiempo de mutex
      adsConectado = true;
#if ADS_PH_MODO_DIFERENCIAL
      Serial.printf("[PH-RTOS2.0] ADC ADS1115 en línea en I2C 0x%02X (860 SPS). Modo PSEUDO-DIFERENCIAL A1-A0 (Kelvin Ground) activo.\n", adsAddr);
#else
      Serial.printf("[PH-RTOS2.0] ADC ADS1115 en línea en I2C 0x%02X (860 SPS). Canal dedicado A1 activo.\n", adsAddr);
#endif
    } else {
      adsConectado = false;
      Serial.println("[PH-RTOS2.0] ⚠️ Advertencia: ADC ADS1115 no detectado en I2C (0x48..0x4B).");
    }
    giveI2CMutex();
  }
}

/**
 * @brief Retorna si el ADC ADS1115 está operativo en el bus I2C.
 */
bool isADSConectado() {
  return adsConectado;
}

/**
 * @brief Adquiere una muestra del convertidor ADS1115.
 * 
 * En Modo Pseudo-Diferencial (ADS_PH_MODO_DIFERENCIAL = 1):
 *   ads.readADC_Differential_0_1() calcula internamente (AIN0 - AIN1).
 *   AIN0 = Referencia Kelvin GND2 (a través de divisor 100k/200k + 100nF).
 *   AIN1 = Señal Po de pH (a través de divisor idéntico 100k/200k + 100nF).
 *   Dado que AIN0 ~ 0V y AIN1 ~ V_Po * 2/3, la resta (AIN0 - AIN1) resulta negativa.
 *   Se niega el resultado para obtener: (AIN1 - AIN0) = (Po - GND2),
 *   eliminando caídas IR y ruidos parásitos de masa con >100 dB de CMRR.
 * 
 * En Modo Single-Ended (ADS_PH_MODO_DIFERENCIAL = 0):
 *   ads.readADC_SingleEnded(ADS_CH_PH) mide A1 respecto a la masa local.
 */
static inline int16_t leerMuestraADCPH() {
#if ADS_PH_MODO_DIFERENCIAL
  int16_t rawDiff = ads.readADC_Differential_0_1();
  int32_t val = -(int32_t)rawDiff;
  if (val < 0) val = 0;
  if (val > 32767) val = 32767;
  return (int16_t)val;
#else
  return ads.readADC_SingleEnded(ADS_CH_PH);
#endif
}

/**
 * @brief Adquiere 5 muestras consecutivas con promediado para calibración metrológica.
 * @param canal Ignorado en RTOS 2.0; se utiliza siempre el canal dedicado ADS_CH_PH (A1) o Diferencial (A1-A0).
 * @return Voltaje medido en Voltios.
 */
float leerVoltajePH(uint8_t canal) {
  (void)canal;
  if (!adsConectado) return PH_OFFSET_TEORICO;

  long suma = 0;
  const int MUESTRAS = 5;

  if (takeI2CMutex(pdMS_TO_TICKS(50))) {
    leerMuestraADCPH(); // Asentamiento inicial
    for (int i = 0; i < MUESTRAS; i++) {
      suma += leerMuestraADCPH();
      delayMicroseconds(50);
    }
    giveI2CMutex();
    return (float)(suma / (float)MUESTRAS) * 0.1875f / 1000.0f;
  }

  return PH_OFFSET_TEORICO;
}

/**
 * @brief Lectura de diagnóstico de 20 muestras en el canal A1 (o diferencial A1-A0).
 * @param canal Ignorado en RTOS 2.0.
 * @return Voltaje directo en Voltios.
 */
float leerVoltajeCrudoPH(uint8_t canal) {
  (void)canal;
  if (!adsConectado) return PH_OFFSET_TEORICO;

  long suma = 0;
  const int MUESTRAS = 20;

  if (takeI2CMutex(pdMS_TO_TICKS(50))) {
    leerMuestraADCPH();
    for (int i = 0; i < MUESTRAS; i++) {
      suma += leerMuestraADCPH();
      delayMicroseconds(100);
    }
    giveI2CMutex();
    return (float)(suma / (float)MUESTRAS) * 0.1875f / 1000.0f;
  }

  return PH_OFFSET_TEORICO;
}

/**
 * @brief Salida de diagnóstico para compatibilidad con paneles de telemetría y consola.
 */
void leerVoltajeCrudoDual(float &v0, float &v1) {
  v1 = leerVoltajeCrudoPH(ADS_CH_PH);
#if ADS_PH_MODO_DIFERENCIAL
  if (takeI2CMutex(pdMS_TO_TICKS(50))) {
    int16_t raw0 = ads.readADC_SingleEnded(ADS_CH_PH_REF);
    giveI2CMutex();
    v0 = (float)raw0 * 0.1875f / 1000.0f; // Voltaje real de la línea de masa remota GND2
  } else {
    v0 = 0.0f;
  }
#else
  v0 = 0.0f;
#endif
}

/**
 * @brief Transforma la señal de tensión en pH según la curva de calibración activa.
 *
 * MODELOS METROLÓGICOS:
 * - Modo 0 (Teórico): pH = 7.0 + (V_7 - V) * PendienteTeórica (4.242 pH/V @ 3.53V).
 * - Modo 1 (2 Puntos): Curva lineal calibrada a partir de tampones pH 7 y pH 4.
 * - Modo 2 (3 Puntos): Función bilineal asimétrica para zonas ácida y alcalina.
 *
 * @param voltaje Tensión de la sonda en Voltios.
 * @param canal Parámetro opcional.
 * @return Valor de pH acotado en el intervalo físico [0.00, 14.00].
 */
float calcularPH(float voltaje, uint8_t canal) {
  (void)canal;
  float ph = 7.0f;

  switch (tipoCalPH) {
    case 0: // Modo Teórico
      ph = 7.0f + ((PH_OFFSET_TEORICO - voltaje) * PH_PENDIENTE_TEORICA);
      break;

    case 1: // Modo 2 Puntos
      if (calibradoPH) {
        ph = 7.0f + ((v7_ph - voltaje) * m_ph);
      } else {
        ph = 7.0f + ((PH_OFFSET_TEORICO - voltaje) * PH_PENDIENTE_TEORICA);
      }
      break;

    case 2: // Modo 3 Puntos
      if (calibradoPH) {
        if (voltaje >= v7_ph) {
          ph = 7.0f + ((v7_ph - voltaje) * mAcida_ph);
        } else {
          ph = 7.0f + ((v7_ph - voltaje) * mBasica_ph);
        }
      } else {
        ph = 7.0f + ((PH_OFFSET_TEORICO - voltaje) * PH_PENDIENTE_TEORICA);
      }
      break;

    default:
      ph = 7.0f;
      break;
  }

  return constrain(ph, 0.0f, 14.0f);
}

/**
 * @brief Adquiere una muestra analógica exclusiva del Canal A1, ejecuta el filtrado
 * en cascada y actualiza las variables globales.
 *
 * Aprovechamiento total del bus: Se ejecuta a 50 Hz sin alternar multiplexores.
 */
void procesarLecturaPH() {
  if (g_failsafe_latched || !phModuloActivo || !adsConectado) return;

  int16_t raw = 0;
  bool ok = false;

  if (takeI2CMutex(pdMS_TO_TICKS(20))) {
    raw = leerMuestraADCPH();
    ok = true;
    giveI2CMutex();
  }

  if (!ok) return;

  estadoPH.acumulador += raw;
  estadoPH.muestras++;

  // Bloque acumulado de 10 muestras completado
  if (estadoPH.muestras >= 10) {
    float vPromedio = ((float)estadoPH.acumulador / 10.0f) * 0.1875f / 1000.0f;
    estadoPH.acumulador = 0;
    estadoPH.muestras = 0;

    // Etapa 2: Filtro No Lineal de Mediana (3 muestras)
    estadoPH.historial[estadoPH.histIdx] = vPromedio;
    estadoPH.histIdx = (estadoPH.histIdx + 1) % 3;
    if (estadoPH.histCount < 3) estadoPH.histCount++;

    float vFiltrado = vPromedio;
    if (estadoPH.histCount >= 3) {
      vFiltrado = mediana3(estadoPH.historial[0], estadoPH.historial[1], estadoPH.historial[2]);
    }

    float phNuevo = calcularPH(vFiltrado);

    // Etapa 3: Filtro Pasabajas Adaptativo bajo xDataMutex
    if (takeDataMutex(pdMS_TO_TICKS(20))) {
      voltajeADC_ph = vFiltrado;
      voltajeSonda_ph = vFiltrado * (300.0f / 200.0f); // Factor 1.50x del divisor físico 100k/200k (2/3 de atenuación)

      if (estadoPH.primeraLectura) {
        phActual = phNuevo;
        estadoPH.primeraLectura = false;
      } else {
        float factorSuavizado = (fabsf(phNuevo - phActual) > 0.5f) ? 0.30f : 0.08f;
        phActual = (phActual * (1.0f - factorSuavizado)) + (phNuevo * factorSuavizado);
      }
      giveDataMutex();
    }
  }
}

/**
 * @brief Calibra un punto de tampón estándar (pH 4, 7 o 10) con muestreo temporal continuo,
 * verificación estricta de estabilidad y validación de coherencia química de buffer,
 * persistiendo en Flash NVS los puntos exactos por modo.
 *
 * @param punto Valor nominal del buffer (4, 7 o 10).
 * @param errorMsg Búfer opcional para mensaje explicativo en caso de fallo.
 * @param errorMsgLen Longitud máxima del búfer errorMsg.
 * @param estabilidad Salida opcional con la dispersión en mV.
 * @return true si la calibración fue aceptada; false si falló.
 */
bool ejecutarCalibracionPH(uint8_t punto, char *errorMsg, size_t errorMsgLen, float *estabilidad) {
  if (g_failsafe_latched || phInterlockActivo()) {
    Serial.println("[PH-RTOS2.0] ⚠️ Calibración bloqueada: Interlock activo (fuente o calentadores encendidos).");
    if (errorMsg && errorMsgLen > 0) {
      snprintf(errorMsg, errorMsgLen, "Interlock activo: apague la fuente VCSS y la calefacción antes de calibrar.");
    }
    return false;
  }

  if (!adsConectado) {
    if (errorMsg && errorMsgLen > 0) snprintf(errorMsg, errorMsgLen, "ADC ADS1115 no detectado.");
    return false;
  }

  if (punto != 4 && punto != 7 && punto != 10) {
    if (errorMsg && errorMsgLen > 0) snprintf(errorMsg, errorMsgLen, "Punto de buffer no soportado (use 4, 7 o 10).");
    return false;
  }

  // 1. Muestreo temporal continuo de 25 muestras en Canal A1 dedicado (~1.5 segundos)
  const int NUM_MUESTRAS = 25;
  float muestras[NUM_MUESTRAS];
  float vMin = 10.0f, vMax = -10.0f, vSuma = 0.0f;

  for (int i = 0; i < NUM_MUESTRAS; i++) {
    if (phInterlockActivo()) {
      if (errorMsg && errorMsgLen > 0) {
        snprintf(errorMsg, errorMsgLen, "Interlock activado durante el muestreo. Proceso abortado.");
      }
      return false;
    }

    if (takeI2CMutex(pdMS_TO_TICKS(60))) {
      leerMuestraADCPH();
      int32_t sumaRaw = 0;
      const int OVERSAMPLE_CAL = 5;
      for (int k = 0; k < OVERSAMPLE_CAL; k++) {
        sumaRaw += leerMuestraADCPH();
        delayMicroseconds(50);
      }
      giveI2CMutex();

      float v = ((float)sumaRaw / (float)OVERSAMPLE_CAL) * 0.1875f / 1000.0f;
      muestras[i] = v;
      vSuma += v;
      if (v < vMin) vMin = v;
      if (v > vMax) vMax = v;
    } else {
      muestras[i] = PH_OFFSET_TEORICO;
      vSuma += PH_OFFSET_TEORICO;
    }
    vTaskDelay(pdMS_TO_TICKS(50));
  }

  float vMedido = vSuma / (float)NUM_MUESTRAS;
  float dispersion = (vMax - vMin) * 1000.0f; // Dispersión pico a pico en mV
  if (estabilidad) *estabilidad = dispersion;

  // 2. Criterio Metrológico de Estabilidad: rechazar si la oscilación supera el umbral
  if (dispersion > PH_CAL_MAX_DISPERSION_MV) {
    Serial.printf("[PH-RTOS2.0] ❌ Calibración rechazada: Lectura inestable (Delta: %.1f mV > %.0f mV).\n",
                  dispersion, PH_CAL_MAX_DISPERSION_MV);
    if (errorMsg && errorMsgLen > 0) {
      snprintf(errorMsg, errorMsgLen,
               "Lectura inestable (variación de %.1f mV > %.0f mV). Mantenga el electrodo inmóvil en el buffer y reintente.",
               dispersion, PH_CAL_MAX_DISPERSION_MV);
    }
    return false;
  }

  // 3. Verificación de límites físicos admisibles del circuito
  if (vMedido < 0.25f || vMedido > 3.10f) {
    Serial.printf("[PH-RTOS2.0] ❌ Calibración fallida: Voltaje %.3f V fuera de rango.\n", vMedido);
    if (errorMsg && errorMsgLen > 0) {
      snprintf(errorMsg, errorMsgLen, "Voltaje analógico fuera de rango (%.3f V). Revise la sonda o el conector BNC.", vMedido);
    }
    return false;
  }

  // 4. Verificación de Coherencia de Buffers
  float localV7 = v7_ph;

  if (punto == 7) {
    if (vMedido < 1.40f || vMedido > 2.15f) {
      Serial.printf("[PH-RTOS2.0] ❌ Calibración pH 7 rechazada: Voltaje %.3f V incoherente para Buffer Neutro.\n", vMedido);
      if (errorMsg && errorMsgLen > 0) {
        snprintf(errorMsg, errorMsgLen, "Voltaje incoherente para pH 7 (%.3f V, esperado 1.40 a 2.15 V). Verifique Buffer 7.0.", vMedido);
      }
      return false;
    }
  } else if (punto == 4) {
    if (vMedido <= localV7 + 0.06f) {
      Serial.printf("[PH-RTOS2.0] ❌ Calibración pH 4 rechazada: Voltaje %.3f V no es mayor que V7 (%.3f V).\n", vMedido, localV7);
      if (errorMsg && errorMsgLen > 0) {
        snprintf(errorMsg, errorMsgLen, "Voltaje de pH 4 (%.3f V) debe ser superior a pH 7 (%.3f V). ¿Calibró pH 7 primero?", vMedido, localV7);
      }
      return false;
    }
  } else if (punto == 10) {
    if (vMedido >= localV7 - 0.06f) {
      Serial.printf("[PH-RTOS2.0] ❌ Calibración pH 10 rechazada: Voltaje %.3f V no es menor que V7 (%.3f V).\n", vMedido, localV7);
      if (errorMsg && errorMsgLen > 0) {
        snprintf(errorMsg, errorMsgLen, "Voltaje de pH 10 (%.3f V) debe ser inferior a pH 7 (%.3f V). ¿Calibró pH 7 primero?", vMedido, localV7);
      }
      return false;
    }
  }

  // Copias locales para persistencia en Flash NVS fuera del mutex crítico
  float nvsSlope = 0.0f, nvsSlopeAc = 0.0f, nvsSlopeBa = 0.0f;
  bool doSaveSlope = false, doSaveDual = false, doSaveCal = false;
  bool mutexOk = false;

  if (takeDataMutex(pdMS_TO_TICKS(50))) {
    mutexOk = true;

    if (punto == 7) v7_ph = vMedido;
    else if (punto == 4) v4_ph = vMedido;
    else if (punto == 10) v10_ph = vMedido;

    localV7 = v7_ph;
    float localV4 = v4_ph;
    float localV10 = v10_ph;
    uint8_t modo = tipoCalPH;

    if (modo == 1) { // Calibración de 2 Puntos (pH 7 y pH 4)
      float deltaV = localV4 - localV7;
      if (fabsf(deltaV) > 0.05f) {
        float m = (7.0f - 4.0f) / deltaV;
        m_ph = m;
        calibradoPH = true;
        nvsSlope = m;
        doSaveSlope = true;
        doSaveCal = true;
      }
    } else if (modo == 2) { // Calibración de 3 Puntos (pH 4, pH 7 y pH 10)
      float dV_ac = localV4 - localV7;
      float dV_ba = localV7 - localV10;
      if (fabsf(dV_ac) > 0.05f && fabsf(dV_ba) > 0.05f) {
        float mAc = (7.0f - 4.0f) / dV_ac;
        float mBa = (10.0f - 7.0f) / dV_ba;
        mAcida_ph = mAc;
        mBasica_ph = mBa;
        calibradoPH = true;
        nvsSlopeAc = mAc;
        nvsSlopeBa = mBa;
        doSaveDual = true;
        doSaveCal = true;
      }
    }
    giveDataMutex();
  }

  // Persistencia NVS fuera de sección crítica
  if (mutexOk) {
    if (punto == 7) { memoria.putFloat("v7", vMedido); memoria.putFloat("v7_1", vMedido); }
    else if (punto == 4) { memoria.putFloat("v4", vMedido); memoria.putFloat("v4_1", vMedido); }
    else if (punto == 10) { memoria.putFloat("v10", vMedido); memoria.putFloat("v10_1", vMedido); }

    if (doSaveSlope) {
      memoria.putFloat("mph", nvsSlope);
      memoria.putFloat("mph1", nvsSlope);
    }
    if (doSaveDual) {
      memoria.putFloat("mAc", nvsSlopeAc);
      memoria.putFloat("mBa", nvsSlopeBa);
      memoria.putFloat("mAc1", nvsSlopeAc);
      memoria.putFloat("mBa1", nvsSlopeBa);
    }
    if (doSaveCal) {
      memoria.putBool("cal", true);
      memoria.putBool("cal1", true);
    }
  }

  return true;
}

/**
 * @brief Sobrecarga de compatibilidad.
 */
bool ejecutarCalibracionPH(uint8_t tina, uint8_t punto, char* errorMsg, size_t errorMsgLen, float* estabilidad) {
  (void)tina;
  return ejecutarCalibracionPH(punto, errorMsg, errorMsgLen, estabilidad);
}

/**
 * @brief Restablece la calibración del sensor dedicado a los valores teóricos de fábrica y limpia la NVS.
 * @return true si se restableció correctamente; false si el interlock está activo.
 */
bool resetCalibracionPH() {
  if (g_failsafe_latched || phInterlockActivo()) {
    Serial.println("[PH-RTOS2.0] ⚠️ Reset bloqueado: Interlock activo o alarma Fail-Safe.");
    return false;
  }

  if (takeDataMutex(pdMS_TO_TICKS(50))) {
    v7_ph = PH_OFFSET_TEORICO;
    v4_ph = 2.0f;
    v10_ph = 1.3f;
    m_ph = PH_PENDIENTE_TEORICA;
    mAcida_ph = PH_PENDIENTE_TEORICA;
    mBasica_ph = PH_PENDIENTE_TEORICA;
    tipoCalPH = 0; // Regresa a modo Teórico
    calibradoPH = true;
    giveDataMutex();
  }

  // Persistir valores teóricos limpios en Flash NVS
  memoria.putFloat("v7", PH_OFFSET_TEORICO);
  memoria.putFloat("v4", 2.0f);
  memoria.putFloat("v10", 1.3f);
  memoria.putFloat("mph", PH_PENDIENTE_TEORICA);
  memoria.putFloat("mAc", PH_PENDIENTE_TEORICA);
  memoria.putFloat("mBa", PH_PENDIENTE_TEORICA);
  memoria.putUChar("tcal", 0);
  memoria.putBool("cal", true);

  // Claves legacy para asegurar compatibilidad total
  memoria.putFloat("v7_1", PH_OFFSET_TEORICO);
  memoria.putFloat("v4_1", 2.0f);
  memoria.putFloat("v10_1", 1.3f);
  memoria.putFloat("mph1", PH_PENDIENTE_TEORICA);
  memoria.putUChar("tcal1", 0);
  memoria.putBool("cal1", true);

  logSistema(LOG_LVL_WARN, "PH", "Calibracion pH (Sensor Dedicado A1) RESTABLECIDA a valores de fabrica por operador");
  return true;
}

/**
 * @brief Sobrecarga de compatibilidad.
 */
bool resetCalibracionPH(uint8_t tina) {
  (void)tina;
  return resetCalibracionPH();
}

/**
 * @brief Evalúa si los calefactores resistivos o la fuente VCSS están energizados.
 * Protege contra corrientes parásitas que ingresarían al electrolito e inutilizarían la lectura de pH.
 *
 * @return true si hay actuadores activos; false si el entorno es seguro.
 */
bool phInterlockActivo() {
  bool activo = false;
  if (takeDataMutex(pdMS_TO_TICKS(20))) {
    for (int i = 0; i < 4; i++) {
      if (canales[i].activo) {
        activo = true;
        break;
      }
    }
    if (fuenteActiva) activo = true;
    giveDataMutex();
  }
  return activo;
}
