#ifndef MODULO_PH_H
#define MODULO_PH_H

/**
 * =================================================================================
 * MÓDULO DE LECTURA DE PH DUAL — Versión 2.0 (Modulo_PH.h)
 * =================================================================================
 * Este módulo mide el pH de 2 tinas del proceso de electrodeposición usando
 * sondas analógicas conectadas al convertidor ADC ADS1115 de 16 bits (I2C).
 *
 * TINAS MONITOREADAS:
 *   - Tina 1 (Zincado):   Canal 0 del ADS1115
 *   - Tina 2 (Niquelado): Canal 1 del ADS1115
 *
 * NOVEDADES v2.0:
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

/** Inicializa el ADC ADS1115 a la velocidad máxima de 860 muestras por segundo.
 */
void inicializarModuloPH();

/**
 * Toma una muestra de pH de forma asíncrona (sin pausar el programa).
 * Se llama cada 20 ms en el bucle principal, alternando entre las 2 tinas.
 * NUEVA: Retorna inmediatamente si phModuloActivo == false (standby).
 */
void procesarLecturaPH();

/**
 * Lee el voltaje de una sonda de pH promediando varias muestras.
 * Se usa durante la calibración para obtener una lectura estable.
 * NOTA: Esta función SÍ bloquea brevemente (~6 ms). Solo se llama desde
 * los endpoints de calibración del servidor web.
 * @param canal 0 para Tina 1, 1 para Tina 2
 * @return Voltaje medido en Voltios
 */
float leerVoltajePH(uint8_t canal);

/**
 * NUEVA v2.0: Lee el voltaje crudo del canal 0 con alta resolución (20 muestras)
 * para la calibración de hardware del offset de la placa PH-4502C.
 * Devuelve el voltaje con 3 decimales de precisión.
 * NOTA: Funciona independientemente del estado On/Off del módulo (es una
 * lectura de diagnóstico de hardware).
 * @return Voltaje crudo en Voltios (esperado: ~1.650V con BNC en corto)
 */
float leerVoltajeCrudoPH();

/**
 * NUEVA v2.0: Calcula el pH a partir del voltaje usando el modo de calibración
 * seleccionado para la tina indicada (Teórico, 2 Puntos o 3 Puntos).
 * Accede a las variables de calibración dentro de sección crítica (muxPH).
 * @param tina 0 para Tina 1, 1 para Tina 2
 * @param voltaje Voltaje medido en Voltios por el ADS1115
 * @return Valor de pH calculado
 */
float calcularPH(uint8_t tina, float voltaje);

/**
 * NUEVA v2.0: Verifica si existe una condición de enclavamiento (Interlock)
 * que impide activar el módulo de pH.
 * Condiciones de bloqueo:
 *   - Algún canal térmico activo (riesgo de daño al electrodo por temperatura)
 *   - Fuente de corriente activa (riesgo de electrólisis del electrodo)
 * @return true si hay un interlock activo (NO se debe activar el pH)
 */
bool phInterlockActivo();

#endif // MODULO_PH_H
