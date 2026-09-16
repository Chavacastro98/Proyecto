#include "JELDimmer2.h"

/**
 * =================================================================================
 * IMPLEMENTACIÓN DE LA LIBRERÍA JELDimmer2 (JELDimmer2.cpp)
 * =================================================================================
 * Implementación básica del control ON/OFF para un módulo dimmer AC de 4 canales.
 * La función setPower() está declarada pero no implementada porque en nano2.ino
 * se usa la lógica de tiempo proporcional directamente con APC_ON/APC_OFF.
 * =================================================================================
 */

JELDimmer2::JELDimmer2() {}

/**
 * Configura los 4 pines de disparo como salidas (inicialmente apagados)
 * y el pin de cruce por cero como entrada con pull-up interno.
 */
void JELDimmer2::begin(int pin1, int pin2, int pin3, int pin4, int zcPin) {
    int pins[4] = {pin1, pin2, pin3, pin4};
    for (int i = 0; i < 4; i++) {
        pinMode(pins[i], OUTPUT);
        digitalWrite(pins[i], LOW);
    }
    pinMode(zcPin, INPUT_PULLUP);
}

/**
 * Función reservada para control de potencia variable por canal.
 * No está implementada en esta versión de la librería.
 * En su lugar, nano2.ino controla la potencia usando APC_ON/APC_OFF
 * con lógica de tiempo proporcional.
 */
void JELDimmer2::setPower(int channel, int percent) {
    // No implementada — ver nano2.ino para la lógica de tiempo proporcional
}

/** Enciende un canal poniendo su pin en HIGH. */
void JELDimmer2::APC_ON(int pin) {
    digitalWrite(pin, HIGH);
}

/** Apaga un canal poniendo su pin en LOW. */
void JELDimmer2::APC_OFF(int pin) {
    digitalWrite(pin, LOW);
}
