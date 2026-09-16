#ifndef MODULO_FUENTES_H
#define MODULO_FUENTES_H

/**
 * =================================================================================
 * MÓDULO DE CONTROL DE LA FUENTE DE CORRIENTE (Modulo_Fuentes.h)
 * =================================================================================
 * Este módulo controla la corriente que se aplica a las piezas durante el proceso
 * de electrodeposición, usando un convertidor digital-analógico (DAC) MCP4725
 * conectado por I2C.
 *
 * MODOS DE OPERACIÓN:
 * 1. Corriente Continua (DC): salida fija proporcional a los Amperios deseados.
 * 2. Corriente Pulsada: genera una onda cuadrada de corriente con frecuencia
 *    y ciclo de trabajo configurables (útil para mejorar la calidad del depósito).
 *
 * ESCALA DEL DAC:
 *   Valor 0    → 0.0 V → 0.0 A
 *   Valor 4095 → 3.3 V → 6.6 A (máximo)
 */

#include "config.h"
#include <Adafruit_MCP4725.h>

// DAC MCP4725 (creado en Proyecto.ino)
extern Adafruit_MCP4725 dac;

/** Inicializa el DAC y establece la salida a 0 Amperios. */
void inicializarFuente();

/** Actualiza la salida del DAC en cada ciclo del bucle principal. */
void actualizarFuente();

/**
 * Configura la corriente de salida en modo continuo.
 * @param amperios Corriente deseada (0.0 a 6.6 A)
 */
void setCorrienteContinua(float amperios);

/**
 * Configura los parámetros del modo de corriente pulsada.
 * @param amperiosPico Corriente durante la fase alta del pulso
 * @param hz           Frecuencia de pulsación (1 a 100 Hz)
 * @param duty         Porcentaje del período en nivel alto (0 a 100 %)
 */
void setConfigPulsado(float amperiosPico, float hz, float duty);

/**
 * Cambia entre modo corriente continua y corriente pulsada.
 * @param usarPulsado true = modo pulsado, false = modo continuo
 */
void conmutarModoFuente(bool usarPulsado);

#endif // MODULO_FUENTES_H