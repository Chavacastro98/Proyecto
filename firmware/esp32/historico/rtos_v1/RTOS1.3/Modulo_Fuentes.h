#ifndef MODULO_FUENTES_H
#define MODULO_FUENTES_H

/**
 * =================================================================================
 * MÓDULO DE SALIDA DE CORRIENTE VCSS (Modulo_Fuentes.h) — Versión RTOS 1.0
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * ARQUITECTURA DEL SUMIDERO LINEAL DE CORRIENTE:
 * Este módulo gestiona el hardware de potencia para la electrodeposición:
 * 1. Convertidor D/A MCP4725 (12-bit I2C en dirección 0x60..0x63).
 * 2. Relé de potencia de +12V en GPIO 20 con conmutación en cruce por cero (ZCS).
 * 3. Doble etapa MOSFET IRLZ44Z con amplificadores operacionales LM358 en lazo cerrado.
 * 4. Shunts de corriente duales de 1.0 Ohm (ADS1115 canales A2 y A3).
 * 5. Transconductancia nominal combinada: Gm = 2.000 S (Siemens / Amperios por Voltio).
 * 6. Calibración en Flash NVS y lazo digital de compensación de ganancia (2 Hz).
 * =================================================================================
 */

#include "config.h"
#include "RTOS_Core.h"

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
 * @param habilitar true para activar la corrección en lazo cerrado a 2 Hz; false para lazo abierto.
 */
void setCompensacionLazoCerrado(bool habilitar);

/**
 * @brief Transmite al DAC MCP4725 la consigna de voltaje correspondiente (solo en modo continuo).
 */
void actualizarFuenteDAC();

/**
 * @brief Lee los canales A2 y A3 del ADS1115 para calcular la corriente real en los shunts.
 * Si el lazo cerrado está habilitado, ajusta de manera progresiva el factor de transconductancia.
 */
void actualizarSensadoVCSS();

/**
 * @brief Computa analíticamente la corriente teórica de pico en modo pulsado cuando
 * la frecuencia es superior a 30 Hz o el tiempo en alto es menor a 5 ms.
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

