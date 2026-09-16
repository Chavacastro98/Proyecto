#ifndef MODULO_FUENTES_H
#define MODULO_FUENTES_H

/**
 * =================================================================================
 * MÓDULO DE SALIDA DE CORRIENTE VCSS (Modulo_Fuentes.h) — Versión RTOS 1.4
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * ARQUITECTURA DESACOPLADA Y SINGLE-WRITER:
 * Este módulo actúa como fachada central y coordinadora de potencia:
 * 1. Convertidor D/A MCP4725 (12-bit I2C en dirección 0x60..0x63).
 * 2. Relé de potencia de +12V en GPIO 20 con conmutación en cruce por cero (ZCS).
 * 3. Módulo DC (Modulo_Fuente_DC.h): Soft-start (500 ms), blanking rápido (300 ms)
 *    y regulador PI adaptativo por zonas a 10 Hz (estabilización en < 2.5s).
 * 4. Módulo Pulsado (Modulo_Fuente_Pulsado.h): Generación de onda (1..100 Hz),
 *    muestreo estroboscópico ETS (16 puntos) y aislamiento total del lazo continuo.
 * 5. Calibración en Flash NVS con enclavamiento estricto si la fuente está activa.
 * =================================================================================
 */

#include "config.h"
#include "RTOS_Core.h"
#include "Modulo_Fuente_DC.h"
#include "Modulo_Fuente_Pulsado.h"

/**
 * @brief Configura pines GPIO del relé ZCS e inicializa el DAC MCP4725 en el bus I2C.
 * Carga desde Flash NVS el factor de transconductancia y la bandera de lazo cerrado.
 */
void inicializarFuente();

/**
 * @brief Enciende o apaga la salida de corriente aplicando la secuencia determinista ZCS.
 * @param encender true para conectar el relé y aplicar consigna; false para llevar a 0A y aislar.
 */
void setEstadoFuente(bool encender);

/**
 * @brief Configura la salida en modo continuo (DC) para entregar la corriente indicada.
 * @param amperios Intensidad deseada en Amperios (0.0 .. VCSS_IMAX_NOMINAL).
 */
void setCorrienteContinua(float amperios);

/**
 * @brief Configura los parámetros de la onda pulsada (amplitud de pico, frecuencia y duty cycle).
 * @param amperiosPico Corriente de cresta en Amperios (0.0 .. VCSS_IMAX_NOMINAL).
 * @param hz Frecuencia de repetición de pulsos (1 .. 100 Hz).
 * @param duty Ciclo de trabajo en porcentaje (0 .. 100%).
 */
void setConfigPulsado(float amperiosPico, float hz, float duty);

/**
 * @brief Conmuta entre modulación continua (DC) y pulsada conservando la consigna.
 * @param usarPulsado true para activar modo pulsado; false para modo continuo.
 */
void conmutarModoFuente(bool usarPulsado);

/**
 * @brief Habilita o deshabilita el ajuste fino digital automático de ganancia Gm.
 * @param habilitar true para activar la corrección en lazo cerrado a 10 Hz; false para lazo abierto.
 */
void setCompensacionLazoCerrado(bool habilitar);

/**
 * @brief Función puente de compatibilidad para modo continuo.
 */
void actualizarFuenteDAC();

/**
 * @brief Función puente de compatibilidad (la adquisición ahora reside en Modulo_Fuente_DC).
 */
void actualizarSensadoVCSS();

/**
 * @brief Computa analíticamente la corriente teórica de pico en modo pulsado.
 */
void actualizarTelemetriaPulsada();

/**
 * @brief Ejecuta el protocolo automático de calibración inyectando 1.50 A de prueba.
 * Mide la corriente resultante, calcula el factor de corrección Gm y lo persiste en Flash NVS.
 * @return true si la calibración fue satisfactoria; false si la corriente estuvo fuera de rango.
 */
bool autoCalibrarVCSS();

/**
 * @brief Restablece la ganancia de transconductancia a su valor teórico de diseño (Gm = 2.000 S, Factor = 1.000).
 */
void resetCalibracionVCSS();

/**
 * @brief Informa si el convertidor MCP4725 fue detectado y configurado exitosamente en el bus I2C.
 * @return true si el DAC está operativo; false en caso contrario.
 */
bool isDACInicializado();

#endif // MODULO_FUENTES_H
