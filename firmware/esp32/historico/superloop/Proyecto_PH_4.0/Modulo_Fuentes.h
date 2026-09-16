#ifndef MODULO_FUENTES_H
#define MODULO_FUENTES_H

/**
 * =================================================================================
 * MÓDULO DE CONTROL DE LA FUENTE DE CORRIENTE (Modulo_Fuentes.h) — Versión 4.0
 * =================================================================================
 * Este módulo controla la corriente que se aplica a las piezas durante el proceso
 * de electrodeposición, usando un convertidor digital-analógico (DAC) MCP4725
 * conectado por I2C.
 *
 * MODOS DE OPERACIÓN:
 * 1. Corriente Continua (DC): salida fija proporcional a los Amperios deseados.
 * 2. Corriente Pulsada: genera una onda cuadrada de corriente con frecuencia
 *    y ciclo de trabajo configurables.
 *
 * ESCALA DEL DAC:
 *   Valor 0    → 0.0 V → 0.0 A
 *   Valor 4095 → 3.3 V → 6.6 A (máximo)
 */

#include "config.h"
#include <Adafruit_MCP4725.h>

// DAC MCP4725 (creado en Proyecto_PH_4.0.ino)
extern Adafruit_MCP4725 dac;

/** Inicializa el DAC y establece la salida a 0 Amperios. Carga parámetros NVS. */
void inicializarFuente();

/** Actualiza la salida del DAC en cada ciclo del bucle principal. */
void actualizarFuente();

/** Conmuta el encendido/apagado de la fuente con la secuencia de seguridad Zero-Current Switching (ZCS) y control del relé de +12V. */
void setEstadoFuente(bool encender);

/** Muestreo de corriente en shunts (A2 y A3 del ADS1115) y compensación digital suave. */
void actualizarSensadoVCSS();

/** Ejecuta un ciclo de calibración de transconductancia VCSS con carga de prueba de 1.50 A. */
bool autoCalibrarVCSS();

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

/** Activa o desactiva la compensación de lazo cerrado digital (outer loop). */
void setCompensacionLazoCerrado(bool habilitar);

#endif // MODULO_FUENTES_H
