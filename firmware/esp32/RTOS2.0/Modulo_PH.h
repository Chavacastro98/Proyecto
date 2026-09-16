#ifndef MODULO_PH_H
#define MODULO_PH_H

/**
 * =================================================================================
 * MÓDULO DE MEDICIÓN Y CALIBRACIÓN DE PH (Modulo_PH.h) — Versión RTOS 2.0
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * ESPECIFICACIONES METROLÓGICAS (RTOS 2.0):
 * • Muestreo Potenciométrico de Alta Resolución:
 *   1. Convertidor A/D: ADS1115 (16 bits, Ganancia 2/3: +-6.144V, 1 LSB = 0.1875 mV).
 *   2. Topología de Conexión:
 *      - Modo Pseudo-Diferencial (A1-A0): Electrodo Po en A1 y Kelvin Ground en A0.
 *      - Modo Single-Ended (A1): Sonda referenciada a plano común analógico.
 *   3. Tasa de Conversión: 860 SPS continuo en convertidor I2C dedicado (0x48).
 *   4. Filtrado Digital en Cascada:
 *      - Promediado de bloque de 10 muestras continuas.
 *      - Filtro no lineal de mediana de 3 puntos (elimina picos por conmutación o EMI).
 *      - Filtro pasabajas adaptativo con factor de suavizado dependiente de delta.
 *   5. Modelos de Calibración Soportados:
 *      - Modo 0: Teórico (Offset 1.765V @ 3.53V VDD, Pendiente -4.242 pH/V).
 *      - Modo 1: Dos Puntos (pH 7.0 y pH 4.0 con cálculo de pendiente lineal).
 *      - Modo 2: Tres Puntos (pH 7.0, pH 4.0 y pH 10.0 con pendientes asimétricas para
 *                zona ácida y alcalina, compensando la no linealidad del vidrio).
 *   6. Interlock de Seguridad: Bloquea la calibración y medición si los calentadores
 *      o la salida de corriente VCSS están encendidos (evita campos de fuga en la celda).
 * =================================================================================
 */

#include "config.h"
#include "RTOS_Core.h"

/**
 * @brief Escanea e inicializa el ADC ADS1115 en el bus I2C (0x48..0x4B) a 860 SPS.
 */
void inicializarModuloPH();

/**
 * @brief Adquiere una muestra del canal A1 dedicado, ejecuta el promediado, mediana y filtro adaptativo.
 * Invocado a 50 Hz por Task_Sensado cuando phModuloActivo = true.
 */
void procesarLecturaPH();

/**
 * @brief Realiza una lectura promediada rápida de 5 muestras en el sensor dedicado.
 * @param canal Parámetro opcional (por defecto ADS_CH_PH = Canal A1).
 * @return Voltaje analógico medido en Voltios.
 */
float leerVoltajePH(uint8_t canal = ADS_CH_PH);

/**
 * @brief Realiza una lectura de alta precisión (20 muestras) en el canal A1 para diagnóstico web y offset.
 * @param canal Parámetro opcional (por defecto ADS_CH_PH = Canal A1).
 * @return Voltaje directo de la sonda en Voltios.
 */
float leerVoltajeCrudoPH(uint8_t canal = ADS_CH_PH);

/**
 * @brief Función de compatibilidad para lecturas crudas.
 * @param v0 Salida Canal A0 (retorna 0.0V por canal eliminado).
 * @param v1 Salida con el voltaje medido en Canal A1 (Sensor Dedicado) en Voltios.
 */
void leerVoltajeCrudoDual(float &v0, float &v1);

/**
 * @brief Transforma una lectura de voltaje en unidad de pH según el modelo de calibración activo.
 * @param voltaje Tensión acondicionada de la sonda en Voltios.
 * @param canal Parámetro opcional para retrocompatibilidad.
 * @return Valor de pH acotado entre 0.00 y 14.00.
 */
float calcularPH(float voltaje, uint8_t canal = 0);

/**
 * @brief Registra un punto de calibración (pH 4, 7 o 10) con ventana de muestreo temporal,
 * verificación de estabilidad y comprobación de coherencia de buffer, guardando en Flash NVS.
 * @param punto Valor del buffer estándar (4, 7 o 10).
 * @param errorMsg Búfer opcional para mensaje explicativo en caso de fallo.
 * @param errorMsgLen Longitud máxima del búfer errorMsg.
 * @param estabilidad Salida opcional con la dispersión medida en mV durante el muestreo.
 * @return true si la calibración fue aceptada y guardada; false si falló por interlock, inestabilidad o incoherencia.
 */
bool ejecutarCalibracionPH(uint8_t punto, char* errorMsg = nullptr, size_t errorMsgLen = 0, float* estabilidad = nullptr);

/**
 * @brief Sobrecarga de retrocompatibilidad que ignora el parámetro tina y calibra el sensor único dedicado.
 */
bool ejecutarCalibracionPH(uint8_t tina, uint8_t punto, char* errorMsg = nullptr, size_t errorMsgLen = 0, float* estabilidad = nullptr);

/**
 * @brief Restablece la calibración del sensor dedicado a los valores teóricos predeterminados de fábrica y limpia la NVS.
 * @return true si se restableció correctamente; false si el interlock está activo.
 */
bool resetCalibracionPH();

/**
 * @brief Sobrecarga de retrocompatibilidad que ignora el parámetro tina.
 */
bool resetCalibracionPH(uint8_t tina);

/**
 * @brief Verifica si existen actuadores de potencia activos (fuente o calefacción) que distorsionen el potencial.
 * @return true si el interlock está activo (potencia encendida); false si la celda está en reposo.
 */
bool phInterlockActivo();

/**
 * @brief Informa si el ADS1115 respondió en el bus I2C durante el arranque.
 * @return true si el ADC está conectado y listo.
 */
bool isADSConectado();

#endif // MODULO_PH_H
