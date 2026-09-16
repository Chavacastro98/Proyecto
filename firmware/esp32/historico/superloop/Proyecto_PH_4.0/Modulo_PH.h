#ifndef MODULO_PH_H
#define MODULO_PH_H

/**
 * =================================================================================
 * MÓDULO DE LECTURA DE PH DUAL — Versión 4.0 (Modulo_PH.h)
 * =================================================================================
 * Este módulo mide el pH de 2 tinas del proceso de electrodeposición usando
 * sondas analógicas conectadas al convertidor ADC ADS1115 de 16 bits (I2C).
 *
 * TINAS MONITOREADAS:
 *   - Tina 1 (Zincado):   Canal 0 del ADS1115
 *   - Tina 2 (Niquelado): Canal 1 del ADS1115
 *
 * CARACTERÍSTICAS:
 *   - Módulo On/Off bajo demanda (no consume I2C/CPU en standby)
 *   - Enclavamiento de seguridad (Interlock) con térmico y fuente
 *   - 3 modos de calibración: Teórico, 2 Puntos, 3 Puntos Dual-Slope
 *   - Filtro de mediana de 3 muestras para eliminación de ruido impulsivo
 *   - Función de voltaje crudo para calibración de hardware (offset BNC)
 *
 * MODOS DE CALIBRACIÓN:
 *   Modo 0 (Teórico): pH = 7.00 + (1.650 - V) × 4.242  (Zero-config)
 *   Modo 1 (2 Puntos): pH = 7.00 + (V - V7) × m         (Buffer pH 7 + pH 4)
 *   Modo 2 (3 Puntos): Dual-slope con m_ácida y m_básica  (Buffers 4, 7, 10)
 */

#include "config.h"

/** Inicializa el ADC ADS1115 a la velocidad máxima de 860 muestras por segundo. */
void inicializarModuloPH();

/**
 * Toma una muestra de pH de forma asíncrona (sin pausar el programa).
 * Se llama cada 20 ms en el bucle principal, alternando entre las 2 tinas.
 */
void procesarLecturaPH();

/**
 * Lee el voltaje de una sonda de pH promediando varias muestras.
 * @param canal 0 para Tina 1, 1 para Tina 2
 * @return Voltaje medido en Voltios
 */
float leerVoltajePH(uint8_t canal);

/**
 * Lee el voltaje crudo del canal 0 con alta resolución (20 muestras)
 * para la calibración de hardware del offset de la placa PH-4502C.
 * @return Voltaje crudo en Voltios (esperado: ~1.650V con BNC en corto)
 */
float leerVoltajeCrudoPH();

/**
 * Calcula el pH a partir del voltaje usando el modo de calibración
 * seleccionado para la tina indicada (Teórico, 2 Puntos o 3 Puntos).
 * @param tina 0 para Tina 1, 1 para Tina 2
 * @param voltaje Voltaje medido en Voltios por el ADS1115
 * @return Valor de pH calculado
 */
float calcularPH(uint8_t tina, float voltaje);

/**
 * Verifica si existe una condición de enclavamiento (Interlock)
 * que impide activar el módulo de pH.
 * @return true si hay un interlock activo (NO se debe activar el pH)
 */
bool phInterlockActivo();

#endif // MODULO_PH_H
