#ifndef MODULO_TERMICO_H
#define MODULO_TERMICO_H

/**
 * =================================================================================
 * MÓDULO DE CONTROL TÉRMICO (Modulo_Termico.h) — Versión 4.0
 * =================================================================================
 * Este módulo se encarga de medir la temperatura de 4 tinas usando termopares
 * Tipo K con amplificadores MAX6675 (comunicación SPI), y de ejecutar un
 * algoritmo de control PI (Proporcional-Integral) para mantener cada tina
 * a la temperatura deseada por el operador.
 *
 * CARACTERÍSTICAS:
 * - 4 canales de control independientes, cada uno con sus propias ganancias PI.
 * - Protección anti-windup: la acción integral se limita para evitar sobretiros.
 * - Rampa de arranque suave: la potencia sube gradualmente al encender.
 * - Los porcentajes de potencia calculados se envían al Arduino Nano por serie.
 */

#include "config.h"
#include <max6675.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

extern portMUX_TYPE muxTermico;

struct CanalTermico {
    int id;                 // Número de canal (0 a 3)
    int pinCS;              // Pin de selección del sensor MAX6675 en el bus SPI
    MAX6675 sensor;         // Objeto para leer el termopar MAX6675
    float temperatura;      // Última temperatura medida en °C
    float setpoint;         // Temperatura objetivo configurada por el usuario en °C
    bool activo;            // true = canal encendido, false = canal apagado
    float limitePotencia;   // Límite actual de la rampa de arranque (0 a 100 %)
    float integral;         // Acumulador de la acción integral del control PI
    float Kp;               // Ganancia proporcional del control PI
    float Ki;               // Ganancia integral del control PI
    int potenciaActual;     // Porcentaje de potencia real aplicado al TRIAC (0 a 100 %)

    CanalTermico(int _id, int _sck, int _cs, int _so, float _kp, float _ki) 
        : id(_id), pinCS(_cs), sensor(_sck, _cs, _so), temperatura(0.0f), 
          setpoint(60.0f), activo(false), limitePotencia(0.0f), integral(0.0f), 
          Kp(_kp), Ki(_ki), potenciaActual(0) {}

    int calcularPI();
};

extern CanalTermico canales[];

/** Prepara los pines y temporizadores del módulo térmico. */
void inicializarModuloTermico();

/**
 * Función que se ejecuta en el bucle principal. Se encarga de:
 * - Incrementar la rampa de arranque cada 200 ms
 * - Calcular el control PI y enviar potencias al Nano cada 1000 ms
 */
void procesarControlTermico();

#endif // MODULO_TERMICO_H
