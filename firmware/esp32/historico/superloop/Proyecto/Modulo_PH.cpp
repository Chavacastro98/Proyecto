#include "Modulo_PH.h"
#include "config.h"

/**
 * =================================================================================
 * IMPLEMENTACIÓN DEL MÓDULO DE PH DUAL (Modulo_PH.cpp)
 * =================================================================================
 * Este archivo implementa la lectura de pH de las 2 tinas del sistema.
 *
 * CÓMO FUNCIONA EL MUESTREO ASÍNCRONO:
 * En vez de leer 10 muestras seguidas (lo cual bloquearía el programa ~12 ms),
 * se toma 1 sola muestra por llamada y se alterna entre las 2 tinas. Como se
 * llama cada 20 ms, cada tina recibe 1 muestra cada 40 ms, completando 10
 * muestras en 400 ms con solo ~1.2 ms de tiempo de CPU por llamada.
 *
 * VELOCIDAD DEL ADC:
 * El ADS1115 está configurado a 860 muestras por segundo, lo que significa
 * que cada conversión toma solo 1.16 ms (en vez de 7.8 ms a velocidad
 * estándar).
 * =================================================================================
 */

/**
 * Estructura que guarda el estado de muestreo de cada canal de pH.
 * Acumula lecturas parciales hasta completar 10 muestras para promediar.
 */
struct EstadoCanalPH {
  long acumulador;  // Suma de lecturas ADC crudas (se promedian al llegar a 10)
  uint8_t muestras; // Cantidad de muestras tomadas hasta ahora (0 a 10)
  bool
      primeraLectura; // true en la primera lectura (salta el filtro suavizador)
};

// Estado de muestreo para cada canal: Canal 0 (Tina 1) y Canal 1 (Tina 2)
static EstadoCanalPH canalesPH[2] = {{0, 0, true}, {0, 0, true}};

// Indica cuál de los 2 canales se mide en esta iteración (alterna entre 0 y 1)
static uint8_t canalActual = 0;

/**
 * Inicializa el ADC ADS1115 a velocidad máxima (860 muestras por segundo).
 */
void inicializarModuloPH() {
  ads.begin();
  ads.setDataRate(RATE_ADS1115_860SPS);
}

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

/**
 * Procesa una muestra ADC de un canal de pH. Al completar 10 muestras,
 * calcula el pH usando la ecuación de calibración y aplica un filtro
 * suavizador para eliminar ruido.
 *
 * @param ch        Canal del ADS1115 (0 o 1)
 * @param v7        Voltaje de referencia del buffer pH 7.0
 * @param m_ph      Pendiente de la recta de calibración (pH por Voltio)
 * @param calibrado true si el canal completó la calibración de 2 puntos
 * @param phActual  Variable donde se guarda el pH filtrado
 */
static void procesarCanalPH(uint8_t ch, float v7, float m_ph, bool calibrado,
                            volatile float &phActual) {
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

    // Calcular el pH:
    // - Si está calibrado: usar la ecuación de la recta de calibración
    // - Si no: usar la ecuación teórica de Nernst con offset a 3.3V (1.650V)
    float phCalc = calibrado ? 7.0f + (voltaje - v7) * m_ph
                             : 7.0f + (1.650f - voltaje) * 4.242f;

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

/**
 * Función del bucle principal: toma una muestra de pH alternando entre las 2
 * tinas. Se ejecuta cada 20 ms, completando 10 muestras por tina en ~400 ms.
 */
void procesarLecturaPH() {
  float v7;
  float m;
  bool cal;

  portENTER_CRITICAL(&muxPH);
  if (canalActual == 0) {
    v7 = v7_1;
    m = m_ph1;
    cal = calibradoPH1;
  } else {
    v7 = v7_2;
    m = m_ph2;
    cal = calibradoPH2;
  }
  portEXIT_CRITICAL(&muxPH);

  if (canalActual == 0) {
    procesarCanalPH(0, v7, m, cal, phActual1);
  } else {
    procesarCanalPH(1, v7, m, cal, phActual2);
  }
  canalActual ^= 1; // Alternar entre 0 y 1 usando XOR
}