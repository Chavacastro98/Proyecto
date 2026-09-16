#ifndef JELDIMMER2_H
#define JELDIMMER2_H

#include <Arduino.h>

/**
 * =================================================================================
 * LIBRERÍA DE CONTROL DIMMER AC DE 4 CANALES (JELDimmer2.h)
 * =================================================================================
 * Controla un módulo dimmer de corriente alterna de 4 canales. Proporciona
 * funciones simples para encender y apagar cada canal (ON/OFF a ciclos completos).
 *
 * FUNCIONES DISPONIBLES:
 *   begin()    → Configura los pines de salida y el pin de cruce por cero
 *   APC_ON()   → Enciende un canal (pin HIGH)
 *   APC_OFF()  → Apaga un canal (pin LOW)
 *   setPower() → (No implementada, reservada para uso futuro)
 * =================================================================================
 */

class JELDimmer2 {
public:
    JELDimmer2();

    /** Inicializa los 4 pines de disparo como salidas y el pin de cruce por cero como entrada. */
    void begin(int pin1, int pin2, int pin3, int pin4, int zcPin);

    /**
     * Función reservada para implementar control de potencia variable.
     * Actualmente NO está implementada — se usan APC_ON/APC_OFF directamente.
     */
    void setPower(int channel, int percent);

    /** Enciende un canal poniendo su pin de disparo en HIGH. */
    void APC_ON(int pin);

    /** Apaga un canal poniendo su pin de disparo en LOW. */
    void APC_OFF(int pin);
};

#endif // JELDIMMER2_H
