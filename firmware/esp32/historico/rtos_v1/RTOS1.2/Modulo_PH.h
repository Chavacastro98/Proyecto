#ifndef MODULO_PH_H
#define MODULO_PH_H

/**
 * =================================================================================
 * MÓDULO DE MEDICIÓN Y CALIBRACIÓN DE PH DUAL (Modulo_PH.h) — Versión RTOS 1.0
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * ESPECIFICACIONES METROLÓGICAS:
 * Adquisición potenciométrica de electrodos combinados de vidrio para dos tinas
 * de electrodeposición (Tina 1 = ADS1115 Canal A0; Tina 2 = Canal A1):
 * 1. Convertidor A/D: ADS1115 (16 bits, Ganancia 2/3: +-6.144V, 1 LSB = 0.1875 mV).
 * 2. Tasa de Conversión: 860 SPS (muestreo rápido para minimizar retención de mutex).
 * 3. Filtrado Digital en Cascada:
 *    - Promediado de bloque de 10 muestras continuas.
 *    - Filtro no lineal de mediana de 3 puntos (elimina picos por conmutación o EMI).
 *    - Filtro pasabajas adaptativo con factor de suavizado dependiente de delta.
 * 4. Modelos de Calibración Soportados:
 *    - Modo 0: Teórico (Offset 2.50V, Pendiente -5.70 pH/V).
 *    - Modo 1: Dos Puntos (pH 7.0 y pH 4.0 con cálculo de pendiente lineal).
 *    - Modo 2: Tres Puntos (pH 7.0, pH 4.0 y pH 10.0 con pendientes asimétricas para
 *              zona ácida y alcalina, compensando la no linealidad del vidrio).
 * 5. Interlock de Seguridad: Bloquea la calibración y medición si los calentadores
 *    de 450W o la salida de corriente VCSS están encendidos (evita campos de fuga en la celda).
 * =================================================================================
 */

#include "config.h"
#include "RTOS_Core.h"

/**
 * @brief Escanea e inicializa el ADC ADS1115 en el bus I2C (0x48..0x4B) a 860 SPS.
 */
void inicializarModuloPH();

/**
 * @brief Adquiere una muestra del canal activo, ejecuta el promediado, mediana y filtro adaptativo.
 * Invocado a 50 Hz por Task_Sensado cuando phModuloActivo = true.
 */
void procesarLecturaPH();

/**
 * @brief Realiza una lectura promediada rápida de 5 muestras en el canal especificado (para calibración).
 * @param canal 0 para Tina 1 (A0); 1 para Tina 2 (A1).
 * @return Voltaje analógico medido en Voltios.
 */
float leerVoltajePH(uint8_t canal);

/**
 * @brief Realiza una lectura de alta precisión (20 muestras) en el canal especificado para diagnóstico web.
 * @param canal 0 para Tina 1 (A0); 1 para Tina 2 (A1).
 * @return Voltaje directo de la sonda en Voltios.
 */
float leerVoltajeCrudoPH(uint8_t canal = 0);

/**
 * @brief Realiza lectura directa simultánea de ambos canales de pH (A0 y A1) para el panel dual de offset en corto.
 * @param v0 Salida con el voltaje medido en Canal A0 (Tina 1) en Voltios.
 * @param v1 Salida con el voltaje medido en Canal A1 (Tina 2) en Voltios.
 */
void leerVoltajeCrudoDual(float &v0, float &v1);

/**
 * @brief Transforma una lectura de voltaje en unidad de pH según el modelo de calibración activo.
 * @param voltaje Tensión acondicionada de la sonda en Voltios.
 * @param canal Índice de canal (0: Tina 1, 1: Tina 2).
 * @return Valor de pH acotado entre 0.00 y 14.00.
 */
float calcularPH(float voltaje, uint8_t canal);

/**
 * @brief Registra un punto de calibración (pH 4, 7 o 10) con ventana de muestreo temporal,
 * verificación de estabilidad y comprobación de coherencia de buffer, guardando en Flash NVS.
 * @param tina Número de tina (1 o 2).
 * @param punto Valor del buffer estándar (4, 7 o 10).
 * @param errorMsg Búfer opcional para mensaje explicativo en caso de fallo.
 * @param errorMsgLen Longitud máxima del búfer errorMsg.
 * @param estabilidad Salida opcional con la dispersión medida en mV durante el muestreo.
 * @return true si la calibración fue aceptada y guardada; false si falló por interlock, inestabilidad o incoherencia.
 */
bool ejecutarCalibracionPH(uint8_t tina, uint8_t punto, char* errorMsg = nullptr, size_t errorMsgLen = 0, float* estabilidad = nullptr);

/**
 * @brief Restablece la calibración de una tina a los valores teóricos predeterminados de fábrica y limpia la NVS.
 * @param tina Número de tina (1 o 2).
 * @return true si se restableció correctamente; false si el interlock está activo.
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

