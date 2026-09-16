/**
 * =================================================================================
 * MÓDULO DE MEDICIÓN Y CALIBRACIÓN DE PH DUAL (Modulo_PH.cpp) — Versión
 * RTOS 1.0
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * DETALLES METROLÓGICOS Y PROCESAMIENTO DIGITAL DE SEÑAL:
 * Las sondas potenciométricas combinadas de pH generan un potencial
 * proporcional a la actividad de iones de hidrógeno según la ley electroquímica
 * de Nernst.
 *
 * ETAPAS DE FILTRADO DIGITAL EN CASCADA:
 * 1. Promediado de Bloque: Cada lectura es la media aritmética de 10
 * conversiones A/D.
 * 2. Filtro de Mediana de 3 Puntos: Rechaza perturbaciones impulsivas
 * (glitches), espigas de conmutación electromagnética (EMI) y ruido de línea
 * sin retrasar la fase de la señal como lo haría un filtro lineal de orden
 * alto.
 * 3. Filtro Pasabajas Adaptativo de Primer Orden:
 *      y(k) = (1 - alpha) * y(k-1) + alpha * x(k)
 *    - Si |x(k) - y(k-1)| > 0.5 pH -> alpha = 0.30 (Respuesta ágil ante
 * inmersión en buffer).
 *    - Si |x(k) - y(k-1)| <= 0.5 pH -> alpha = 0.08 (Rechazo severo de ruido en
 * régimen estacionario).
 *
 * PERSISTENCIA NVS FUERA DE SECCIÓN CRÍTICA:
 * Las escrituras en memoria Flash SPI conllevan latencias de varios
 * milisegundos. Para no bloquear las tareas de control térmico o fuente, los
 * valores calculados se transfieren a variables locales bajo xDataMutex y la
 * persistencia NVS se realiza inmediatamente después de liberar el mutex.
 * =================================================================================
 */

#include "Modulo_PH.h"
#include "Modulo_Termico.h"
#include "RTOS_Core.h"
#include "config.h"

/**
 * @brief Algoritmo óptimo de ordenamiento para calcular la mediana de 3
 * muestras. Ejecuta en un máximo de 3 comparaciones sin usar memoria dinámica
 * ni bucles.
 */
static float mediana3(float a, float b, float c) {
  if (a > b) {
    float t = a;
    a = b;
    b = t;
  }
  if (b > c) {
    float t = b;
    b = c;
    c = t;
  }
  if (a > b) {
    float t = a;
    a = b;
    b = t;
  }
  return b;
}

/**
 * @brief Estado interno de filtrado y acumulación para cada canal analógico de
 * pH.
 */
struct EstadoCanalPH {
  long acumulador;     /**< Sumatoria de códigos brutos del ADC ADS1115 */
  uint8_t muestras;    /**< Contador de muestras acumuladas en el bloque actual
                          (0..10) */
  bool primeraLectura; /**< Inicializador de estado para bypass de filtro en la
                          1ra muestra */
  float historial[3]; /**< Búfer circular para el filtro no lineal de mediana */
  uint8_t histIdx;    /**< Índice de inserción en el búfer de mediana */
  uint8_t histCount;  /**< Cantidad de muestras válidas en el búfer de mediana
                         (0..3) */
};

/** @brief Instancias de filtrado para Tina 1 (Canal 0) y Tina 2 (Canal 1) */
static EstadoCanalPH canalesPH[2] = {{0, 0, true, {0.0f, 0.0f, 0.0f}, 0, 0},
                                     {0, 0, true, {0.0f, 0.0f, 0.0f}, 0, 0}};

/** @brief Puntero de canal activo para el multiplexado temporal a 50 Hz */
static uint8_t canalActual = 0;

/** @brief Bandera que valida la presencia física del ADC ADS1115 en el bus I2C
 */
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
      ads.setGain(
          GAIN_TWOTHIRDS); // Rango de entrada +-6.144V (1 LSB = 0.1875 mV)
      ads.setDataRate(RATE_ADS1115_860SPS); // Máxima velocidad para minimizar
                                            // tiempo de mutex
      adsConectado = true;
      Serial.printf("[PH] ADC ADS1115 en línea en I2C 0x%02X (860 SPS).\n",
                    adsAddr);
    } else {
      adsConectado = false;
      Serial.println("[PH] ⚠️ Advertencia: ADC ADS1115 no detectado en I2C "
                     "(0x48..0x4B).");
    }
    giveI2CMutex();
  }
}

/**
 * @brief Retorna si el ADC ADS1115 está operativo en el bus I2C.
 */
bool isADSConectado() { return adsConectado; }

/**
 * @brief Adquiere 5 muestras consecutivas con promediado para calibración
 * metrológica.
 *
 * @param canal 0 para Tina 1 (A0); 1 para Tina 2 (A1).
 * @return Voltaje medido en Voltios.
 */
float leerVoltajePH(uint8_t canal) {
  if (!adsConectado)
    return PH_OFFSET_TEORICO;

  long suma = 0;
  const int MUESTRAS = 5;

  if (takeI2CMutex(pdMS_TO_TICKS(50))) {
    for (int i = 0; i < MUESTRAS; i++) {
      suma += ads.readADC_SingleEnded(canal);
      delayMicroseconds(50);
    }
    giveI2CMutex();
    return (float)(suma / (float)MUESTRAS) * 0.1875f / 1000.0f;
  }

  return PH_OFFSET_TEORICO;
}

/**
 * @brief Lectura de diagnóstico de 20 muestras en el canal A0.
 * @return Voltaje directo en Voltios.
 */
/**
 * @brief Lectura de diagnóstico de 20 muestras en el canal especificado.
 * @param canal 0 para Tina 1 (A0); 1 para Tina 2 (A1).
 * @return Voltaje directo en Voltios.
 */
float leerVoltajeCrudoPH(uint8_t canal) {
  if (!adsConectado)
    return PH_OFFSET_TEORICO;
  if (canal > 1)
    canal = 0;

  long suma = 0;
  const int MUESTRAS = 20;

  if (takeI2CMutex(pdMS_TO_TICKS(50))) {
    for (int i = 0; i < MUESTRAS; i++) {
      suma += ads.readADC_SingleEnded(canal);
      delayMicroseconds(100);
    }
    giveI2CMutex();
    return (float)(suma / (float)MUESTRAS) * 0.1875f / 1000.0f;
  }

  return PH_OFFSET_TEORICO;
}

/**
 * @brief Realiza lectura directa simultánea de ambos canales (A0 y A1) para el
 * panel dual de offset en corto.
 * @param v0 Salida voltaje Canal 0 (Tina 1 A0) en Voltios.
 * @param v1 Salida voltaje Canal 1 (Tina 2 A1) en Voltios.
 */
void leerVoltajeCrudoDual(float &v0, float &v1) {
  if (!adsConectado) {
    v0 = PH_OFFSET_TEORICO;
    v1 = PH_OFFSET_TEORICO;
    return;
  }

  long suma0 = 0, suma1 = 0;
  const int MUESTRAS = 15;

  if (takeI2CMutex(pdMS_TO_TICKS(100))) {
    for (int i = 0; i < MUESTRAS; i++) {
      suma0 += ads.readADC_SingleEnded(0);
      delayMicroseconds(80);
      suma1 += ads.readADC_SingleEnded(1);
      delayMicroseconds(80);
    }
    giveI2CMutex();
    v0 = (float)(suma0 / (float)MUESTRAS) * 0.1875f / 1000.0f;
    v1 = (float)(suma1 / (float)MUESTRAS) * 0.1875f / 1000.0f;
  } else {
    v0 = PH_OFFSET_TEORICO;
    v1 = PH_OFFSET_TEORICO;
  }
}

/**
 * @brief Transforma la señal de tensión en pH según la curva de calibración
 * activa.
 *
 * MODELOS METROLÓGICOS:
 * - Modo 0 (Teórico): pH = 7.0 + (V_7 - V) * PendienteTeórica (-5.70 pH/V).
 * - Modo 1 (2 Puntos): Curva lineal única generada a partir de los tampones pH
 * 7 y pH 4.
 * - Modo 2 (3 Puntos): Función bilineal con pendientes asimétricas para zona
 * ácida y alcalina: Si V >= V_7 (Zona Ácida): pH = 7.0 + (V_7 - V) * m_ácida Si
 * V <  V_7 (Zona Alcalina): pH = 7.0 + (V_7 - V) * m_básica
 *
 * @param voltaje Tensión de la sonda en Voltios.
 * @param canal Índice de canal (0: Tina 1, 1: Tina 2).
 * @return Valor de pH acotado en el intervalo físico [0.00, 14.00].
 */
float calcularPH(float voltaje, uint8_t canal) {
  uint8_t modo = (canal == 0) ? tipoCalPH1 : tipoCalPH2;
  float v7 = (canal == 0) ? v7_1 : v7_2;
  float m = (canal == 0) ? m_ph1 : m_ph2;
  float mAc = (canal == 0) ? mAcida1 : mAcida2;
  float mBa = (canal == 0) ? mBasica1 : mBasica2;
  bool cal = (canal == 0) ? calibradoPH1 : calibradoPH2;

  float ph = 7.0f;

  switch (modo) {
  case 0: // Modo Teórico
    ph = 7.0f + ((PH_OFFSET_TEORICO - voltaje) * PH_PENDIENTE_TEORICA);
    break;

  case 1: // Modo 2 Puntos
    if (cal) {
      ph = 7.0f + ((v7 - voltaje) * m);
    } else {
      ph = 7.0f + ((v7 - voltaje) * PH_PENDIENTE_TEORICA);
    }
    break;

  case 2: // Modo 3 Puntos
    if (cal) {
      if (voltaje >= v7) {
        ph = 7.0f + ((v7 - voltaje) * mAc);
      } else {
        ph = 7.0f + ((v7 - voltaje) * mBa);
      }
    } else {
      ph = 7.0f + ((v7 - voltaje) * PH_PENDIENTE_TEORICA);
    }
    break;

  default:
    ph = 7.0f;
    break;
  }

  return constrain(ph, 0.0f, 14.0f);
}

/**
 * @brief Adquiere una muestra analógica, ejecuta el filtrado en cascada y
 * actualiza las variables globales. Se ejecuta alternadamente entre canales a
 * 50 Hz.
 */
void procesarLecturaPH() {
  if (g_failsafe_latched || !phModuloActivo || !adsConectado)
    return;

  int16_t raw = 0;
  bool ok = false;

  if (takeI2CMutex(pdMS_TO_TICKS(20))) {
    raw = ads.readADC_SingleEnded(canalActual);
    ok = true;
    giveI2CMutex();
  }

  if (!ok)
    return;

  EstadoCanalPH &ec = canalesPH[canalActual];
  ec.acumulador += raw;
  ec.muestras++;

  // Bloque acumulado de 10 muestras completado
  if (ec.muestras >= 10) {
    float vPromedio = ((float)ec.acumulador / 10.0f) * 0.1875f / 1000.0f;
    ec.acumulador = 0;
    ec.muestras = 0;

    // Etapa 2: Filtro No Lineal de Mediana (3 muestras)
    ec.historial[ec.histIdx] = vPromedio;
    ec.histIdx = (ec.histIdx + 1) % 3;
    if (ec.histCount < 3)
      ec.histCount++;

    float vFiltrado = vPromedio;
    if (ec.histCount >= 3) {
      vFiltrado = mediana3(ec.historial[0], ec.historial[1], ec.historial[2]);
    }

    float phNuevo = calcularPH(vFiltrado, canalActual);

    // Etapa 3: Filtro Pasabajas Adaptativo bajo xDataMutex
    if (takeDataMutex(pdMS_TO_TICKS(20))) {
      volatile float &phDest = (canalActual == 0) ? phActual1 : phActual2;
      volatile float &vAdcDest = (canalActual == 0) ? voltajeADC1 : voltajeADC2;
      volatile float &vSondaDest =
          (canalActual == 0) ? voltajeSonda1 : voltajeSonda2;

      vAdcDest = vFiltrado;
      vSondaDest = vFiltrado * (5.0f / 3.53f);

      if (ec.primeraLectura) {
        phDest = phNuevo;
        ec.primeraLectura = false;
      } else {
        float factorSuavizado =
            (fabsf(phNuevo - phDest) > 0.5f) ? 0.30f : 0.08f;
        phDest =
            (phDest * (1.0f - factorSuavizado)) + (phNuevo * factorSuavizado);
      }
      giveDataMutex();
    }
  }

  // Alternancia de canal para el siguiente ciclo
  canalActual = (canalActual == 0) ? 1 : 0;
}

/**
 * @brief Calibra un punto de tampón estándar (pH 4, 7 o 10) con muestreo
 * temporal, verificación de estabilidad y validación de coherencia de buffer,
 * persistiendo en Flash NVS.
 *
 * @param tina 1 o 2.
 * @param punto Valor nominal del buffer (4, 7 o 10).
 * @param errorMsg Búfer opcional para mensaje explicativo en caso de fallo.
 * @param errorMsgLen Longitud máxima del búfer errorMsg.
 * @param estabilidad Salida opcional con la dispersión en mV.
 * @return true si la calibración fue aceptada; false si falló por interlock,
 * inestabilidad o incoherencia.
 */
bool ejecutarCalibracionPH(uint8_t tina, uint8_t punto, char *errorMsg,
                           size_t errorMsgLen, float *estabilidad) {
  if (g_failsafe_latched || phInterlockActivo()) {
    Serial.println(
        "[PH] ⚠️ Calibración bloqueada: Interlock activo (fuente "
        "o calentadores encendidos).");
    if (errorMsg && errorMsgLen > 0) {
      snprintf(errorMsg, errorMsgLen,
               "Interlock activo: apague la fuente VCSS y la calefacción antes "
               "de calibrar.");
    }
    return false;
  }

  if (tina != 1 && tina != 2)
    return false;
  if (!adsConectado) {
    if (errorMsg && errorMsgLen > 0)
      snprintf(errorMsg, errorMsgLen, "ADC ADS1115 no detectado.");
    return false;
  }

  uint8_t canal = (tina == 1) ? 0 : 1;

  // 1. Muestreo temporal continuo de 25 muestras espaciadas (~1.5 segundos)
  const int NUM_MUESTRAS = 25;
  float muestras[NUM_MUESTRAS];
  float vMin = 10.0f, vMax = -10.0f, vSuma = 0.0f;

  for (int i = 0; i < NUM_MUESTRAS; i++) {
    // Verificar si durante el proceso se activó algún actuador de potencia
    if (phInterlockActivo()) {
      if (errorMsg && errorMsgLen > 0) {
        snprintf(errorMsg, errorMsgLen,
                 "Interlock activado durante el muestreo. Proceso abortado.");
      }
      return false;
    }

    if (takeI2CMutex(pdMS_TO_TICKS(60))) {
      int16_t raw = ads.readADC_SingleEnded(canal);
      giveI2CMutex();
      float v = (float)raw * 0.1875f / 1000.0f;
      muestras[i] = v;
      vSuma += v;
      if (v < vMin)
        vMin = v;
      if (v > vMax)
        vMax = v;
    } else {
      muestras[i] = PH_OFFSET_TEORICO;
      vSuma += PH_OFFSET_TEORICO;
    }
    vTaskDelay(pdMS_TO_TICKS(50)); // Espaciado determinista entre muestras
  }

  float vMedido = vSuma / (float)NUM_MUESTRAS;
  float dispersión = (vMax - vMin) * 1000.0f; // Dispersión pico a pico en mV
  if (estabilidad)
    *estabilidad = dispersión;

  // 2. Criterio Metrológico de Estabilidad: rechazar si la oscilación supera el umbral admisible
  if (dispersión > PH_CAL_MAX_DISPERSION_MV) {
    Serial.printf("[PH] ❌ Calibración rechazada: Lectura inestable (Delta: "
                  "%.1f mV > %.0f mV).\n",
                  dispersión, PH_CAL_MAX_DISPERSION_MV);
    if (errorMsg && errorMsgLen > 0) {
      snprintf(errorMsg, errorMsgLen,
               "Lectura inestable (variación de %.1f mV > %.0f mV). Mantenga el "
               "electrodo inmóvil en el buffer y reintente.",
               dispersión, PH_CAL_MAX_DISPERSION_MV);
    }
    return false;
  }


  // 3. Verificación de límites físicos admisibles del circuito
  if (vMedido < 0.25f || vMedido > 3.10f) {
    Serial.printf(
        "[PH] ❌ Calibración fallida: Voltaje %.3f V fuera de rango.\n",
        vMedido);
    if (errorMsg && errorMsgLen > 0) {
      snprintf(errorMsg, errorMsgLen,
               "Voltaje analógico fuera de rango (%.3f V). Revise la sonda o "
               "el conector BNC.",
               vMedido);
    }
    return false;
  }

  // 4. Verificación de Coherencia de Buffers (Anti-Error de Operador)
  float localV7 = (tina == 1) ? v7_1 : v7_2;

  if (punto == 7) {
    // Buffer pH 7 debe estar cerca del offset analógico central (~1.765 V)
    if (vMedido < 1.40f || vMedido > 2.15f) {
      Serial.printf("[PH] ❌ Calibración pH 7 rechazada: Voltaje %.3f V "
                    "incoherente para Buffer Neutro.\n",
                    vMedido);
      if (errorMsg && errorMsgLen > 0) {
        snprintf(errorMsg, errorMsgLen,
                 "Voltaje incoherente para pH 7 (%.3f V, esperado 1.40 a 2.15 "
                 "V). Verifique que la sonda esté en Buffer 7.0.",
                 vMedido);
      }
      return false;
    }
  } else if (punto == 4) {
    // En la placa PH-4502C, el medio ácido (pH 4) produce voltaje MAYOR que pH
    // 7
    if (vMedido <= localV7 + 0.06f) {
      Serial.printf("[PH] ❌ Calibración pH 4 rechazada: Voltaje %.3f V no es "
                    "mayor que V7 (%.3f V).\n",
                    vMedido, localV7);
      if (errorMsg && errorMsgLen > 0) {
        snprintf(errorMsg, errorMsgLen,
                 "Voltaje de pH 4 (%.3f V) debe ser superior a pH 7 (%.3f V). "
                 "¿Sonda en buffer incorrecto o no ha calibrado pH 7?",
                 vMedido, localV7);
      }
      return false;
    }
  } else if (punto == 10) {
    // En la placa PH-4502C, el medio alcalino (pH 10) produce voltaje MENOR que
    // pH 7
    if (vMedido >= localV7 - 0.06f) {
      Serial.printf("[PH] ❌ Calibración pH 10 rechazada: Voltaje %.3f V no es "
                    "menor que V7 (%.3f V).\n",
                    vMedido, localV7);
      if (errorMsg && errorMsgLen > 0) {
        snprintf(errorMsg, errorMsgLen,
                 "Voltaje de pH 10 (%.3f V) debe ser inferior a pH 7 (%.3f V). "
                 "¿Sonda en buffer incorrecto o no ha calibrado pH 7?",
                 vMedido, localV7);
      }
      return false;
    }
  }

  char k_v7[8], k_v4[8], k_v10[8], k_mph[8], k_mAc[8], k_mBa[8], k_cal[8];
  snprintf(k_v7, sizeof(k_v7), "v7_%d", tina);
  snprintf(k_v4, sizeof(k_v4), "v4_%d", tina);
  snprintf(k_v10, sizeof(k_v10), "v10_%d", tina);
  snprintf(k_mph, sizeof(k_mph), "mph%d", tina);
  snprintf(k_mAc, sizeof(k_mAc), "mAc%d", tina);
  snprintf(k_mBa, sizeof(k_mBa), "mBa%d", tina);
  snprintf(k_cal, sizeof(k_cal), "cal%d", tina);

  // Copias locales para persistencia en Flash NVS fuera del mutex crítico
  float nvsSlope = 0.0f, nvsSlopeAc = 0.0f, nvsSlopeBa = 0.0f;
  bool doSaveSlope = false, doSaveDual = false, doSaveCal = false;
  bool mutexOk = false;

  if (takeDataMutex(pdMS_TO_TICKS(50))) {
    mutexOk = true;

    if (punto == 7) {
      if (tina == 1)
        v7_1 = vMedido;
      else
        v7_2 = vMedido;
    } else if (punto == 4) {
      if (tina == 1)
        v4_1 = vMedido;
      else
        v4_2 = vMedido;
    } else if (punto == 10) {
      if (tina == 1)
        v10_1 = vMedido;
      else
        v10_2 = vMedido;
    }

    localV7 = (tina == 1) ? v7_1 : v7_2;
    float localV4 = (tina == 1) ? v4_1 : v4_2;
    float localV10 = (tina == 1) ? v10_1 : v10_2;
    uint8_t modo = (tina == 1) ? tipoCalPH1 : tipoCalPH2;

    if (modo == 1) { // Calibración de 2 Puntos (pH 7 y pH 4)
      float deltaV = localV4 - localV7;
      if (fabsf(deltaV) > 0.05f) {
        float m = (7.0f - 4.0f) / deltaV;
        if (tina == 1) {
          m_ph1 = m;
          calibradoPH1 = true;
        } else {
          m_ph2 = m;
          calibradoPH2 = true;
        }
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
        if (tina == 1) {
          mAcida1 = mAc;
          mBasica1 = mBa;
          calibradoPH1 = true;
        } else {
          mAcida2 = mAc;
          mBasica2 = mBa;
          calibradoPH2 = true;
        }
        nvsSlopeAc = mAc;
        nvsSlopeBa = mBa;
        doSaveDual = true;
        doSaveCal = true;
      }
    }
    giveDataMutex();
  }

  // Persistencia NVS fuera de sección crítica (evita retención de mutex durante
  // escrituras en Flash)
  if (mutexOk) {
    if (punto == 7)
      memoria.putFloat(k_v7, vMedido);
    else if (punto == 4)
      memoria.putFloat(k_v4, vMedido);
    else if (punto == 10)
      memoria.putFloat(k_v10, vMedido);

    if (doSaveSlope)
      memoria.putFloat(k_mph, nvsSlope);
    if (doSaveDual) {
      memoria.putFloat(k_mAc, nvsSlopeAc);
      memoria.putFloat(k_mBa, nvsSlopeBa);
    }
    if (doSaveCal)
      memoria.putBool(k_cal, true);
  }

  return true;
}

/**
 * @brief Restablece la calibración de una tina a los valores teóricos de
 * fábrica y limpia la NVS.
 * @param tina Número de tina (1 o 2).
 * @return true si se restableció correctamente; false si el interlock está
 * activo.
 */
bool resetCalibracionPH(uint8_t tina) {
  if (g_failsafe_latched || phInterlockActivo()) {
    Serial.println(
        "[PH] ⚠️ Reset bloqueado: Interlock activo o alarma Fail-Safe.");
    return false;
  }
  if (tina != 1 && tina != 2)
    return false;

  char k_v7[8], k_v4[8], k_v10[8], k_mph[8], k_mAc[8], k_mBa[8], k_cal[8],
      k_tcal[8];
  snprintf(k_v7, sizeof(k_v7), "v7_%d", tina);
  snprintf(k_v4, sizeof(k_v4), "v4_%d", tina);
  snprintf(k_v10, sizeof(k_v10), "v10_%d", tina);
  snprintf(k_mph, sizeof(k_mph), "mph%d", tina);
  snprintf(k_mAc, sizeof(k_mAc), "mAc%d", tina);
  snprintf(k_mBa, sizeof(k_mBa), "mBa%d", tina);
  snprintf(k_cal, sizeof(k_cal), "cal%d", tina);
  snprintf(k_tcal, sizeof(k_tcal), "tcal%d", tina);

  if (takeDataMutex(pdMS_TO_TICKS(50))) {
    if (tina == 1) {
      v7_1 = PH_OFFSET_TEORICO;
      v4_1 = 2.0f;
      v10_1 = 1.3f;
      m_ph1 = -PH_PENDIENTE_TEORICA;
      mAcida1 = -PH_PENDIENTE_TEORICA;
      mBasica1 = -PH_PENDIENTE_TEORICA;
      tipoCalPH1 = 0; // Vuelve a teórico
      calibradoPH1 = true;
    } else {
      v7_2 = PH_OFFSET_TEORICO;
      v4_2 = 2.0f;
      v10_2 = 1.3f;
      m_ph2 = -PH_PENDIENTE_TEORICA;
      mAcida2 = -PH_PENDIENTE_TEORICA;
      mBasica2 = -PH_PENDIENTE_TEORICA;
      tipoCalPH2 = 0;
      calibradoPH2 = true;
    }
    giveDataMutex();
  }

  // Persistir valores teóricos limpios en Flash NVS
  memoria.putFloat(k_v7, PH_OFFSET_TEORICO);
  memoria.putFloat(k_v4, 2.0f);
  memoria.putFloat(k_v10, 1.3f);
  memoria.putFloat(k_mph, -PH_PENDIENTE_TEORICA);
  memoria.putFloat(k_mAc, -PH_PENDIENTE_TEORICA);
  memoria.putFloat(k_mBa, -PH_PENDIENTE_TEORICA);
  memoria.putUChar(k_tcal, 0);
  memoria.putBool(k_cal, true);

  logSistema(
      LOG_LVL_WARN, "PH",
      "Calibracion Tina %d RESTABLECIDA a valores de fabrica por operador",
      tina);
  return true;
}

/**
 * @brief Evalúa si los calefactores resistivos o la fuente VCSS están
 * energizados. Protege contra corrientes parásitas que ingresarían al
 * electrolito e inutilizarían la lectura de pH.
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
    if (fuenteActiva)
      activo = true;
    giveDataMutex();
  }
  return activo;
}
