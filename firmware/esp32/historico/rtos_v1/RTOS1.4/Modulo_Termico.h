#ifndef MODULO_TERMICO_H
#define MODULO_TERMICO_H

/**
 * =================================================================================
 * MÓDULO DE CONTROL TÉRMICO PI (Modulo_Termico.h) — Versión RTOS 1.0
 * =================================================================================
 * Plataforma: ESP32-S3 (Xtensa Dual-Core 32-bit LX7 @ 240 MHz)
 *
 * ESPECIFICACIONES DE LA PLANTA TÉRMICA:
 * El sistema gobierna de forma desacoplada la temperatura de 4 tinas de proceso:
 * - Canal 0: Tina de Limpieza Electrolítica (450W, Kp=62.65, Ki=0.0897)
 * - Canal 1: Tina de Decapado Químico (450W, Kp=62.65, Ki=0.0897)
 * - Canal 2: Tina de Celda Hull de Prueba (18W, Kp=16.71, Ki=0.0239)
 * - Canal 3: Tina de Niquelado Watts (450W, Kp=62.51, Ki=0.0895)
 *
 * INSTRUMENTACIÓN Y ACCIONAMIENTO:
 * - Sensores: Termopares Tipo K con compensación de unión fría MAX6675 (SPI @ 4.3 MHz).
 * - Actuadores: Calefactores de inmersión resistivos modulados por TRIACs con cruce
 *   por cero gobernados por Arduino Nano esclavo vía enlace UART2.
 * =================================================================================
 */

#include "config.h"
#include "RTOS_Core.h"
#include <max6675.h>

/**
 * @brief Estructura que encapsula el estado físico, parámetros de sintonía PI
 * y objeto sensor de cada reactor térmico independiente.
 */
struct CanalTermico {
    int id;                 /**< Identificador numérico del canal (0..3) */
    int pinCS;              /**< GPIO conectado a la línea Chip Select del MAX6675 */
    MAX6675 sensor;         /**< Instancia del controlador de interfaz SPI MAX6675 */
    float temperatura;      /**< Última lectura de temperatura validada (°C) */
    float setpoint;         /**< Temperatura objetivo fijada por el operador (°C) */
    bool activo;            /**< Estado de habilitación del lazo de control */
    float limitePotencia;   /**< Techo de potencia dinámica impuesto por la rampa suave (0..100%) */
    float integral;         /**< Acumulador del término integral con anti-windup */
    float Kp;               /**< Ganancia proporcional sintonizada */
    float Ki;               /**< Ganancia integral sintonizada */
    int potenciaActual;     /**< Potencia de salida calculada y transmitida (0..100%) */

    /**
     * @brief Constructor del canal térmico.
     */
    CanalTermico(int _id, int _sck, int _cs, int _so, float _kp, float _ki) 
        : id(_id), pinCS(_cs), sensor(_sck, _cs, _so), temperatura(0.0f), 
          setpoint(60.0f), activo(false), limitePotencia(0.0f), integral(0.0f), 
          Kp(_kp), Ki(_ki), potenciaActual(0) {}

    /**
     * @brief Evalúa la ley de control Proporcional-Integral con límites y protecciones.
     * @return Porcentaje de potencia a aplicar (0..100%).
     */
    int calcularPI();
};

/** @brief Arreglo global de los 4 canales térmicos de la planta */
extern CanalTermico canales[];

/**
 * @brief Configura los pines Chip Select (CS) del bus SPI para los sensores MAX6675.
 */
void inicializarModuloTermico();

/**
 * @brief Avanza la rampa de arranque suave (+1% cada 200 ms) para los canales activos.
 */
void ejecutarPasoTermico200ms();

/**
 * @brief Ejecuta el cálculo PI a 1 Hz, aplica el límite de rampa y transmite las potencias a UART2.
 */
void ejecutarPasoTermico1000ms();

#endif // MODULO_TERMICO_H

