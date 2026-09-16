#include "Modulo_PH.h"
#include "Modulo_Termico.h"
#include "config.h"

/**
 * =================================================================================
 * IMPLEMENTACIÓN DEL MÓDULO DE PH DUAL — Versión 2.0 (Modulo_PH.cpp)
 * =================================================================================
 * Este archivo implementa la lectura de pH de las 2 tinas del sistema con
 * las siguientes mejoras respecto a la versión 1.0:
 *
 * 1. MÓDULO ON/OFF: procesarLecturaPH() retorna inmediatamente si el módulo
 *    está en standby, sin realizar lecturas I2C ni consumir CPU.
 *
 * 2. FILTRO DE MEDIANA: Antes del suavizado adaptativo, se aplica un filtro
 *    de mediana de 3 sobre los últimos promedios completados para eliminar
 *    outliers de ruido impulsivo (picos espurios del ADC o EMI).
 *
 * 3. CÁLCULO MULTI-MODO: La función calcularPH() unifica los 3 modos de
 *    calibración (Teórico, 2 Puntos, 3 Puntos) en una sola función con
 *    protección de sección crítica.
 *
 * 4. INTERLOCK: phInterlockActivo() consulta el estado del módulo térmico
 *    y la fuente de corriente para impedir la activación simultánea.
 *
 * 5. VOLTAJE CRUDO: leerVoltajeCrudoPH() proporciona una lectura de alta
 *    resolución (20 muestras) para la calibración del potenciómetro de
 *    offset de la placa PH-4502C.
 *
 * VELOCIDAD DEL ADC:
 * El ADS1115 está configurado a 860 muestras por segundo, lo que significa
 * que cada conversión toma solo 1.16 ms (en vez de 7.8 ms a velocidad
 * estándar).
 * =================================================================================
 */

// ---------------------------------------------------------------------------------
// FILTRO DE MEDIANA DE 3 ELEMENTOS
// ---------------------------------------------------------------------------------
/**
 * Calcula la mediana de 3 valores flotantes usando una red de ordenamiento
 * (sorting network) de 3 comparaciones. Tiempo constante O(1), sin bucles
 * ni asignación dinámica.
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

// ---------------------------------------------------------------------------------
// ESTRUCTURA DE ESTADO POR CANAL
// ---------------------------------------------------------------------------------
/**
 * Guarda el estado de muestreo de cada canal de pH.
 * v2.0: Añade buffer circular de 3 promedios para filtro de mediana.
 */
struct EstadoCanalPH {
  long acumulador;  // Suma de lecturas ADC crudas (se promedian al llegar a 10)
  uint8_t muestras; // Cantidad de muestras tomadas hasta ahora (0 a 10)
  bool primeraLectura; // true en la primera lectura (salta el filtro suavizador)

  // Historial circular para filtro de mediana (3 últimos promedios de voltaje)
  float historial[3]; // Buffer de los 3 últimos voltajes promediados
  uint8_t histIdx;    // Índice de escritura en el buffer circular
  uint8_t histCount;  // Cantidad de promedios acumulados (0 a 3, luego 3 fijo)
};

// Estado de muestreo para cada canal: Canal 0 (Tina 1) y Canal 1 (Tina 2)
static EstadoCanalPH canalesPH[2] = {
    {0, 0, true, {0.0f, 0.0f, 0.0f}, 0, 0},
    {0, 0, true, {0.0f, 0.0f, 0.0f}, 0, 0}};

// Indica cuál de los 2 canales se mide en esta iteración (alterna entre 0 y 1)
static uint8_t canalActual = 0;

// ---------------------------------------------------------------------------------
// INICIALIZACIÓN
// ---------------------------------------------------------------------------------
/**
 * Inicializa el ADC ADS1115 a velocidad máxima (860 muestras por segundo).
 */
void inicializarModuloPH() {
  ads.begin();
  ads.setGain(GAIN_TWOTHIRDS); // 2/3x gain +/- 6.144V (1 bit = 0.1875mV)
  ads.setDataRate(RATE_ADS1115_860SPS);
}

// ---------------------------------------------------------------------------------
// LECTURA DE VOLTAJE PARA CALIBRACIÓN (BLOQUEANTE)
// ---------------------------------------------------------------------------------
/**
 * Lee el voltaje de una sonda de pH promediando 5 muestras.
 * Esta función SÍ bloquea brevemente (~6 ms) y se usa solo durante la
 * calibración (llamada desde el servidor web al presionar "Calibrar").
 *
 * @param canal Canal del ADS1115 (0 para Tina 1, 1 para Tina 2)
 * @return Voltaje en Voltios
 */
float leerVoltajePH(uint8_t canal) {
  long suma = 0;
  const int MUESTRAS = 5;

  for (int i = 0; i < MUESTRAS; i++) {
    suma += ads.readADC_SingleEnded(canal);
    delayMicroseconds(
        50); // Breve pausa para que el multiplexor interno se estabilice
  }

  // Convertir el valor digital a Voltios:
  // Con ganancia por defecto (GAIN_TWOTHIRDS), cada bit = 0.1875 mV
  // Dividir entre 1000 para pasar de mV a V
  return (float)(suma / (float)MUESTRAS) * 0.1875f / 1000.0f;
}

// ---------------------------------------------------------------------------------
// LECTURA DE VOLTAJE CRUDO PARA CALIBRACIÓN DE HARDWARE (OFFSET DE PLACA)
// ---------------------------------------------------------------------------------
/**
 * Lee el voltaje del canal 0 del ADS1115 con alta resolución (20 muestras
 * promediadas) para la calibración del potenciómetro de offset de la placa
 * PH-4502C.
 *
 * FUNCIONA INDEPENDIENTEMENTE DEL ESTADO ON/OFF DEL MÓDULO, ya que es una
 * lectura de diagnóstico de hardware que se invoca bajo demanda desde el
 * endpoint /data_ph_raw del servidor web.
 *
 * @return Voltaje crudo en Voltios con resolución de ~0.001V
 */
float leerVoltajeCrudoPH() {
  long suma = 0;
  const int MUESTRAS = 20;

  for (int i = 0; i < MUESTRAS; i++) {
    suma += ads.readADC_SingleEnded(0);
    delayMicroseconds(50);
  }

  return (float)(suma / (float)MUESTRAS) * 0.1875f / 1000.0f;
}

// ---------------------------------------------------------------------------------
// CÁLCULO DE PH MULTI-MODO
// ---------------------------------------------------------------------------------
/**
 * Calcula el valor de pH a partir del voltaje medido, usando el modo de
 * calibración seleccionado para la tina indicada.
 *
 * MODOS:
 *   0 (Teórico): pH = 7.00 + (1.650 - V) × 4.242
 *                 Asume la recta ideal del divisor. No requiere calibración.
 *
 *   1 (2 Puntos): pH = 7.00 + (V - V7) × m
 *                  Calibración lineal clásica con buffers pH 7 y pH 4.
 *
 *   2 (3 Puntos): Dual-slope segmentado:
 *                  Si V ≥ V7 (lado ácido): pH = 7.0 + (V - V7) × m_ácida
 *                  Si V < V7 (lado básico): pH = 7.0 + (V - V7) × m_básica
 *                  Usa buffers pH 4, 7 y 11 para máxima precisión.
 *
 * SECCIÓN CRÍTICA: Todas las variables de calibración se leen dentro de
 * portENTER_CRITICAL(&muxPH) para garantizar atomicidad frente al servidor web.
 *
 * @param tina 0 = Tina 1 (Zincado), 1 = Tina 2 (Niquelado)
 * @param voltaje Voltaje medido en Voltios por el ADS1115
 * @return Valor de pH calculado
 */
float calcularPH(uint8_t tina, float voltaje) {
  uint8_t modo;
  float vRef7, pendiente, mAc, mBa;

  // Leer todas las variables de calibración atómicamente
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

  case 2: // 3 Puntos (Dual-Slope Segmentado: pH 4, 7 y 11)
    if (voltaje >= vRef7) {
      // Lado ácido (V ≥ V7 → pH ≤ 7)
      return 7.0f + (voltaje - vRef7) * mAc;
    } else {
      // Lado básico (V < V7 → pH > 7)
      return 7.0f + (voltaje - vRef7) * mBa;
    }

  default: // Fallback a teórico
    return 7.0f + (PH_OFFSET_TEORICO - voltaje) * PH_PENDIENTE_TEORICA;
  }
}

// ---------------------------------------------------------------------------------
// VERIFICACIÓN DE INTERLOCK
// ---------------------------------------------------------------------------------
/**
 * Verifica si existe un conflicto de seguridad que impide activar el módulo pH.
 *
 * RAZONES DE BLOQUEO:
 * 1. Sistema térmico activo: los electrodos de vidrio de pH se degradan
 *    rápidamente a temperaturas elevadas. El rango operativo típico es
 *    0-60°C, pero las tinas pueden superar los 80°C.
 * 2. Fuente de corriente activa: la corriente de electrodeposición genera
 *    campos eléctricos que interfieren con la medición potenciométrica y
 *    pueden causar electrólisis sobre la membrana de vidrio del electrodo.
 *
 * @return true si hay un interlock activo (prohibido activar pH)
 */
bool phInterlockActivo() {
  // Verificar canales térmicos
  portENTER_CRITICAL(&muxTermico);
  bool termicoOn = false;
  for (int i = 0; i < 4; i++) {
    if (canales[i].activo) {
      termicoOn = true;
      break;
    }
  }
  portEXIT_CRITICAL(&muxTermico);

  // Verificar fuente de corriente
  portENTER_CRITICAL(&muxFuente);
  bool fOn = fuenteActiva;
  portEXIT_CRITICAL(&muxFuente);

  return termicoOn || fOn;
}

// ---------------------------------------------------------------------------------
// PROCESAMIENTO DE MUESTRA POR CANAL (FUNCIÓN INTERNA)
// ---------------------------------------------------------------------------------
/**
 * Procesa una muestra ADC de un canal de pH. Al completar 10 muestras:
 * 1. Promedia las lecturas y convierte a Voltios
 * 2. Almacena en el buffer circular de mediana (3 últimos promedios)
 * 3. Si el buffer está lleno, calcula la mediana de 3
 * 4. Calcula el pH usando calcularPH() con el modo seleccionado
 * 5. Aplica filtro suavizador adaptativo para eliminar ruido fino
 *
 * @param ch        Canal del ADS1115 (0 o 1)
 * @param phActual  Variable donde se guarda el pH filtrado
 */
static void procesarCanalPH(uint8_t ch, volatile float &phActual) {
  // Tomar 1 muestra del ADC (~1.16 ms a 860 SPS)
  int16_t adc = ads.readADC_SingleEnded(ch);
  EstadoCanalPH &e = canalesPH[ch];
  e.acumulador += adc;
  e.muestras++;

  // Al completar 10 muestras, calcular el pH
  if (e.muestras >= 10) {
    // Promediar las 10 lecturas y convertir a Voltios
    float voltaje = (float)(e.acumulador / 10.0f) * 0.1875f / 1000.0f;
    e.acumulador = 0;
    e.muestras = 0;

    // Almacenar en el buffer circular de mediana
    e.historial[e.histIdx] = voltaje;
    e.histIdx = (e.histIdx + 1) % 3;
    if (e.histCount < 3)
      e.histCount++;

    // Si aún no hay 3 promedios, usar el voltaje directo
    float voltajeFiltrado;
    if (e.histCount >= 3) {
      // Filtro de mediana de 3: elimina outliers impulsivos
      voltajeFiltrado =
          mediana3(e.historial[0], e.historial[1], e.historial[2]);
    } else {
      voltajeFiltrado = voltaje;
    }

    // Calcular el pH usando el modo de calibración seleccionado
    float phCalc = calcularPH(ch, voltajeFiltrado);

    // Filtro suavizador adaptativo:
    // - Si el cambio es grande (> 0.35 pH): aceptar inmediatamente (respuesta rápida)
    // - Si el cambio es pequeño: suavizar con filtro 70/30 (eliminar ruido fino)
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

// ---------------------------------------------------------------------------------
// FUNCIÓN DEL BUCLE PRINCIPAL
// ---------------------------------------------------------------------------------
/**
 * Función del bucle principal: toma una muestra de pH alternando entre las 2
 * tinas. Se ejecuta cada 20 ms, completando 10 muestras por tina en ~400 ms.
 *
 * v2.0: GUARD ON/OFF — Si phModuloActivo == false, retorna inmediatamente
 * sin realizar ninguna lectura I2C ni consumir CPU.
 */
void procesarLecturaPH() {
  // *** GUARD ON/OFF: No tocar el bus I2C en standby ***
  if (!phModuloActivo) {
    return;
  }

  if (canalActual == 0) {
    procesarCanalPH(0, phActual1);
  } else {
    procesarCanalPH(1, phActual2);
  }
  canalActual ^= 1; // Alternar entre 0 y 1 usando XOR
}
