#include "Modulo_PH.h"
#include "Modulo_Termico.h"
#include "config.h"

/**
 * =================================================================================
 * IMPLEMENTACIÓN DEL MÓDULO DE PH DUAL (Modulo_PH.cpp) — Versión 4.0
 * =================================================================================
 */

// ---------------------------------------------------------------------------------
// FILTRO DE MEDIANA DE 3 ELEMENTOS
// ---------------------------------------------------------------------------------
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

// ---------------------------------------------------------------------------------
// ESTRUCTURA DE ESTADO POR CANAL
// ---------------------------------------------------------------------------------
struct EstadoCanalPH {
  long acumulador;     // Suma de lecturas ADC crudas
  uint8_t muestras;    // Cantidad de muestras tomadas
  bool primeraLectura; // true en la primera lectura (salta el filtro suavizador)
  float historial[3];  // Buffer de los 3 últimos voltajes promediados
  uint8_t histIdx;     // Índice de escritura en el buffer circular
  uint8_t histCount;   // Cantidad de promedios acumulados
};

static EstadoCanalPH canalesPH[2] = {
    {0, 0, true, {0.0f, 0.0f, 0.0f}, 0, 0},
    {0, 0, true, {0.0f, 0.0f, 0.0f}, 0, 0}};

static uint8_t canalActual = 0;

static bool adsConectado = false;

void inicializarModuloPH() {
  Wire.beginTransmission(0x48);
  if (Wire.endTransmission() == 0) {
    ads.begin(0x48);
    ads.setGain(GAIN_TWOTHIRDS); // 2/3x gain +/- 6.144V (1 bit = 0.1875mV)
    ads.setDataRate(RATE_ADS1115_860SPS);
    adsConectado = true;
    Serial.println("[PH] ADC ADS1115 en línea en dirección I2C 0x48.");
  } else {
    adsConectado = false;
    Serial.println("[PH] ⚠️ Advertencia: ADC ADS1115 no detectado en I2C (0x48). Modo simulación seguro activo.");
  }
}

float leerVoltajePH(uint8_t canal) {
  if (!adsConectado) {
    return PH_OFFSET_TEORICO;
  }
  long suma = 0;
  const int MUESTRAS = 5;

  for (int i = 0; i < MUESTRAS; i++) {
    suma += ads.readADC_SingleEnded(canal);
    delayMicroseconds(50);
  }

  return (float)(suma / (float)MUESTRAS) * 0.1875f / 1000.0f;
}

float leerVoltajeCrudoPH() {
  if (!adsConectado) {
    return PH_OFFSET_TEORICO;
  }
  long suma = 0;
  const int MUESTRAS = 20;

  for (int i = 0; i < MUESTRAS; i++) {
    suma += ads.readADC_SingleEnded(0);
    delayMicroseconds(50);
  }

  return (float)(suma / (float)MUESTRAS) * 0.1875f / 1000.0f;
}

float calcularPH(uint8_t tina, float voltaje) {
  uint8_t modo;
  float vRef7, pendiente, mAc, mBa;

  portENTER_CRITICAL(&muxPH);
  if (tina == 0) {
    modo = tipoCalPH1;
    vRef7 = v7_1;
    pendiente = m_ph1;
    mAc = mAcida1;
    mBa = mBasica1;
  } else {
    modo = tipoCalPH2;
    vRef7 = v7_2;
    pendiente = m_ph2;
    mAc = mAcida2;
    mBa = mBasica2;
  }
  portEXIT_CRITICAL(&muxPH);

  switch (modo) {
  case 0: // Teórico / Provisional (Zero-Config)
    return 7.0f + (PH_OFFSET_TEORICO - voltaje) * PH_PENDIENTE_TEORICA;

  case 1: // 2 Puntos (Lineal: pH 7 + pH 4)
    return 7.0f + (voltaje - vRef7) * pendiente;

  case 2: // 3 Puntos (Dual-Slope Segmentado: pH 4, 7 y 10)
    if (voltaje >= vRef7) {
      // Lado ácido (V ≥ V7 → pH ≤ 7)
      return 7.0f + (voltaje - vRef7) * mAc;
    } else {
      // Lado básico (V < V7 → pH > 7)
      return 7.0f + (voltaje - vRef7) * mBa;
    }

  default:
    return 7.0f + (PH_OFFSET_TEORICO - voltaje) * PH_PENDIENTE_TEORICA;
  }
}

bool phInterlockActivo() {
  portENTER_CRITICAL(&muxTermico);
  bool termicoOn = false;
  for (int i = 0; i < 4; i++) {
    if (canales[i].activo) {
      termicoOn = true;
      break;
    }
  }
  portEXIT_CRITICAL(&muxTermico);

  portENTER_CRITICAL(&muxFuente);
  bool fOn = fuenteActiva;
  portEXIT_CRITICAL(&muxFuente);

  return termicoOn || fOn;
}

static void procesarCanalPH(uint8_t ch, volatile float &phActual) {
  if (!adsConectado) {
    portENTER_CRITICAL(&muxPH);
    phActual = 7.00f; // Valor neutro seguro si no hay sensor físico conectado
    portEXIT_CRITICAL(&muxPH);
    return;
  }

  int16_t adc = ads.readADC_SingleEnded(ch);
  EstadoCanalPH &e = canalesPH[ch];
  e.acumulador += adc;
  e.muestras++;

  if (e.muestras >= 10) {
    float voltaje = (float)(e.acumulador / 10.0f) * 0.1875f / 1000.0f;
    e.acumulador = 0;
    e.muestras = 0;

    e.historial[e.histIdx] = voltaje;
    e.histIdx = (e.histIdx + 1) % 3;
    if (e.histCount < 3)
      e.histCount++;

    float voltajeFiltrado;
    if (e.histCount >= 3) {
      voltajeFiltrado = mediana3(e.historial[0], e.historial[1], e.historial[2]);
    } else {
      voltajeFiltrado = voltaje;
    }

    float phCalc = calcularPH(ch, voltajeFiltrado);

    portENTER_CRITICAL(&muxPH);
    if (e.primeraLectura || fabsf(phCalc - phActual) > 0.35f) {
      phActual = phCalc;
      e.primeraLectura = false;
    } else {
      phActual = (phActual * 0.70f) + (phCalc * 0.30f);
    }
    portEXIT_CRITICAL(&muxPH);
  }
}

void procesarLecturaPH() {
  if (!phModuloActivo) {
    return;
  }

  if (canalActual == 0) {
    procesarCanalPH(0, phActual1);
  } else {
    procesarCanalPH(1, phActual2);
  }
  canalActual ^= 1;
}
