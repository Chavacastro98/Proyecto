#include "Modulo_Fuentes.h"
#include "config.h"
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

/**
 * =================================================================================
 * IMPLEMENTACIÓN DE LA FUENTE DE CORRIENTE (Modulo_Fuentes.cpp)
 * =================================================================================
 * Este archivo implementa el control del DAC MCP4725 para generar corriente
 * continua (DC) o corriente pulsada en el proceso de electrodeposición.
 *
 * OPTIMIZACIÓN IMPORTANTE:
 * La función actualizarFuente() se ejecuta en cada ciclo del loop() sin
 * delay(). Para evitar enviar datos por I2C innecesariamente (lo cual consume
 * tiempo), se guarda el último valor enviado al DAC en una variable caché. Solo
 * se transmite por I2C cuando el valor cambia. En modo DC, esto significa cero
 * transmisiones I2C después del primer envío.
 * =================================================================================
 */

// Caché del último valor enviado al DAC (evita escrituras I2C repetidas)
static uint16_t ultimoCodigoDAC = 0xFFFF;

// Indica si el DAC se encontró correctamente al arrancar
static bool dacInicializado = false;

/**
 * Busca el DAC MCP4725 en la dirección I2C 0x60 y pone la salida a 0V (0
 * Amperios).
 */
void inicializarFuente() {
  dacInicializado = dac.begin(0x60);
  if (!dacInicializado) {
    Serial.println(
        "[FUENTE] ❌ Error: DAC MCP4725 no detectado en dirección I2C 0x60.");
  } else {
    dac.setVoltage(0, false); // Salida a 0V al encender
    ultimoCodigoDAC = 0;
    Serial.println("[FUENTE] DAC MCP4725 (12-bit) en línea en dirección 0x60.");
  }
}

/**
 * Convierte Amperios a valor digital del DAC y activa el modo continuo.
 * Fórmula: valor_DAC = (Amperios / 6.6) × 4095
 */
void setCorrienteContinua(float amperios) {
  portENTER_CRITICAL(&muxFuente);
  modoPulsado = false;
  amplitudDAC = (int)constrain((amperios / 6.6f) * 4095.0f, 0.0f, 4095.0f);
  portEXIT_CRITICAL(&muxFuente);
}

/**
 * Configura los parámetros de frecuencia y ciclo de trabajo para corriente
 * pulsada.
 */
void setConfigPulsado(float amperiosPico, float hz, float duty) {
  portENTER_CRITICAL(&muxFuente);
  amplitudDAC = (int)constrain((amperiosPico / 6.6f) * 4095.0f, 0.0f, 4095.0f);
  frecuencia = (hz > 0.0f) ? (int)hz : 1;
  dutyCycle = (int)constrain(duty, 0.0f, 100.0f);
  portEXIT_CRITICAL(&muxFuente);
}

/**
 * Cambia entre corriente continua y corriente pulsada.
 */
void conmutarModoFuente(bool usarPulsado) {
  portENTER_CRITICAL(&muxFuente);
  modoPulsado = usarPulsado;
  portEXIT_CRITICAL(&muxFuente);
}

/**
 * Genera la señal de salida del DAC en tiempo real (se llama en cada ciclo del
 * loop).
 *
 * En modo DC: pone la amplitud configurada como valor fijo.
 * En modo pulsado: usa micros() para calcular si estamos en la fase alta o baja
 * del pulso, alternando entre la amplitud y cero sin usar delay().
 *
 * Solo envía datos al DAC por I2C cuando el valor cambia (caché en RAM).
 */
void actualizarFuente() {
  if (!dacInicializado)
    return;

  int vOut = 0;

  // Obtener copias locales de las variables compartidas con el servidor web
  portENTER_CRITICAL(&muxFuente);
  bool localActiva = fuenteActiva;
  bool localPulsado = modoPulsado;
  int localAmplitud = amplitudDAC;
  int localFreq = frecuencia;
  int localDuty = dutyCycle;
  portEXIT_CRITICAL(&muxFuente);

  if (localActiva) {
    vOut = localAmplitud; // En DC, la salida es siempre la amplitud configurada

    // En modo pulsado, alternar entre amplitud y cero según el tiempo
    if (localPulsado) {
      int freqVal = constrain(localFreq, 1, 100);
      unsigned long periodoMicros =
          1000000UL / (unsigned long)freqVal; // Duración de un ciclo completo
      if (periodoMicros == 0)
        periodoMicros = 1;

      unsigned long tiempoCiclo =
          micros() % periodoMicros; // Posición dentro del ciclo actual
      unsigned long tiempoAlto = (periodoMicros * (unsigned long)localDuty) /
                                 100UL; // Duración del nivel alto

      // Si estamos en la parte alta del pulso → amplitud, si no → cero
      vOut = (tiempoCiclo < tiempoAlto) ? localAmplitud : 0;
    }
  }

  uint16_t codigoDAC = (uint16_t)constrain(vOut, 0, 4095);

  // Solo enviar al DAC si el valor cambió respecto al último envío
  if (codigoDAC != ultimoCodigoDAC) {
    dac.setVoltage(
        codigoDAC,
        false); // false = escribir en RAM del DAC (rápido, sin EEPROM)
    ultimoCodigoDAC = codigoDAC;
  }
}