#ifndef MODULO_PH_H
#define MODULO_PH_H

/**
 * =================================================================================
 * MÓDULO DE LECTURA DE PH DUAL (Modulo_PH.h)
 * =================================================================================
 * Este módulo mide el pH de 2 tinas del proceso de electrodeposición usando
 * sondas analógicas conectadas al convertidor ADC ADS1115 de 16 bits (I2C).
 *
 * TINAS MONITOREADAS:
 *   - Tina 1 (Zincado):   Canal 0 del ADS1115
 *   - Tina 2 (Niquelado): Canal 1 del ADS1115
 *
 * CALIBRACIÓN DE 2 PUNTOS (cómo funciona):
 * Para que las lecturas de pH sean precisas, se necesitan 2 soluciones de
 * referencia (buffers) de pH conocido:
 *   1. Sumergir la sonda en buffer pH 7.0 → el sistema guarda el voltaje V7
 *   2. Sumergir la sonda en buffer pH 4.0 → el sistema guarda el voltaje V4
 *   3. Se calcula la pendiente: m = (4.0 - 7.0) / (V4 - V7)  [pH por Voltio]
 *   4. Lectura en tiempo real: pH = 7.0 + (V_medido - V7) × m
 */

#include "config.h"

/** Inicializa el ADC ADS1115 a la velocidad máxima de 860 muestras por segundo.
 */
void inicializarModuloPH();

/**
 * Toma una muestra de pH de forma asíncrona (sin pausar el programa).
 * Se llama cada 20 ms en el bucle principal, alternando entre las 2 tinas.
 */
void procesarLecturaPH();

/**
 * Lee el voltaje de una sonda de pH promediando varias muestras.
 * Se usa durante la calibración para obtener una lectura estable.
 * @param canal 0 para Tina 1, 1 para Tina 2
 * @return Voltaje medido en Voltios
 */
float leerVoltajePH(uint8_t canal);

#endif // MODULO_PH_H