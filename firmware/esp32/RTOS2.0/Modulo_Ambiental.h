#ifndef MODULO_AMBIENTAL_H
#define MODULO_AMBIENTAL_H

/**
 * =================================================================================
 * MÓDULO METEOROLÓGICO Y AMBIENTAL (Modulo_Ambiental.h) — Versión RTOS 1.0
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * ESPECIFICACIONES DE INSTRUMENTACIÓN AMBIENTAL:
 * Registra las condiciones termodinámicas del laboratorio químico para registrar
 * variables de entorno que afectan la evaporación del electrolito y la presión de celda:
 * 1. Sensor AHT20 / AHT10 (I2C en 0x38 o 0x39):
 *    - Temperatura: -40 °C a +85 °C (+-0.3 °C).
 *    - Humedad Relativa: 0 % a 100 % (+-2 %).
 * 2. Sensor BMP280 / BME280 (I2C en 0x76 o 0x77):
 *    - Presión Barométrica Absoluta: 300 a 1100 hPa (+-1 hPa).
 *    - Temperatura de respaldo si el AHT20 no responde.
 * 3. Operación en Modo Degradado:
 *    Si alguno de los dos sensores no responde durante el escaneo I2C, el sistema
 *    continúa funcionando sin bloquearse, notificando la advertencia visual en la baliza LED.
 * =================================================================================
 */

#include "config.h"
#include "RTOS_Core.h"

/** @brief Indica si el sensor de humedad/temperatura AHT20 fue reconocido en el bus */
extern bool ahtInicializado;

/** @brief Indica si el sensor barométrico BMP280 fue reconocido en el bus */
extern bool bmpInicializado;

/**
 * @brief Ejecuta el escaneo I2C de diagnóstico de 0x01 a 0x7F e inicializa los sensores meteorológicos.
 * @return true si al menos un sensor ambiental quedó en línea; false si ninguno fue detectado.
 */
bool inicializarModuloAmbiental();

/**
 * @brief Adquiere las magnitudes de temperatura, humedad y presión atmosférica bajo cerrojo I2C.
 * Invocado cada 5000 ms (0.2 Hz) por Task_Sensado.
 */
void procesarLecturaAmbiental();

#endif // MODULO_AMBIENTAL_H

