#include "Modulo_Termico.h"
#include "config.h"

/**
 * =================================================================================
 * IMPLEMENTACIÓN DEL CONTROL TÉRMICO (Modulo_Termico.cpp) — Versión 4.0
 * =================================================================================
 */

portMUX_TYPE muxTermico = portMUX_INITIALIZER_UNLOCKED;

CanalTermico canales[] = {
    CanalTermico(0, COMMON_SCK, 5,  COMMON_SO, 62.65f, 0.0897f), // Canal 0: Limpieza (450W)
    CanalTermico(1, COMMON_SCK, 4,  COMMON_SO, 62.65f, 0.0897f), // Canal 1: Decapado (450W)
    CanalTermico(2, COMMON_SCK, 13, COMMON_SO, 16.71f, 0.0239f), // Canal 2: Celda Hull (18W)
    CanalTermico(3, COMMON_SCK, 14, COMMON_SO, 62.51f, 0.0895f)  // Canal 3: Niquelado (450W)
};

void inicializarModuloTermico() {
    lastPI = millis();
    lastRamp = millis();

    for (int i = 0; i < 4; i++) {
        pinMode(canales[i].pinCS, OUTPUT);
        digitalWrite(canales[i].pinCS, HIGH);
    }
}

int CanalTermico::calcularPI() {
    float input = (float)sensor.readCelsius();
    
    if (isnan(input) || input <= 0.0f || input >= 150.0f) {
        portENTER_CRITICAL(&muxTermico);
        activo = false;
        integral = 0.0f;
        temperatura = 0.0f;
        portEXIT_CRITICAL(&muxTermico);
        return 0;
    }

    portENTER_CRITICAL(&muxTermico);
    temperatura = input;
    float tempLocal = temperatura;
    float spLocal = setpoint;
    bool activoLocal = activo;
    portEXIT_CRITICAL(&muxTermico);

    if (!activoLocal) {
        portENTER_CRITICAL(&muxTermico);
        integral = 0.0f;
        portEXIT_CRITICAL(&muxTermico);
        return 0;
    }

    if (tempLocal >= (spLocal + 2.0f)) {
        return 0;
    }

    float error = spLocal - tempLocal;
    float P = Kp * error;

    portENTER_CRITICAL(&muxTermico);
    integral += error * 1.0f;
    if (Ki > 0.0f) {
        if (integral * Ki > 100.0f) integral = 100.0f / Ki;
        if (integral * Ki < 0.0f)   integral = 0.0f;
    }
    float I = Ki * integral;
    portEXIT_CRITICAL(&muxTermico);

    float salida = P + I;
    return (int)constrain(salida, 0.0f, 100.0f);
}

void procesarControlTermico() {
    unsigned long timestampActual = millis();

    if (timestampActual - lastRamp >= 200) {
        lastRamp = timestampActual;
        portENTER_CRITICAL(&muxTermico);
        for (int i = 0; i < 4; i++) {
            if (canales[i].activo && canales[i].limitePotencia < 100.0f) {
                canales[i].limitePotencia += 1.0f;
            }
        }
        portEXIT_CRITICAL(&muxTermico);
    }

    if (timestampActual - lastPI >= 1000) {
        lastPI = timestampActual;

        int potenciasCalculadas[4] = {0, 0, 0, 0};

        for (int i = 0; i < 4; i++) {
            int u_pi = canales[i].calcularPI();
            
            portENTER_CRITICAL(&muxTermico);
            float limLocal = canales[i].limitePotencia;
            int pot = (int)min((float)u_pi, limLocal);
            canales[i].potenciaActual = pot;
            portEXIT_CRITICAL(&muxTermico);

            potenciasCalculadas[i] = pot;
        }

        char cadenaUART[32];
        snprintf(cadenaUART, sizeof(cadenaUART), "%d,%d,%d,%d",
                 potenciasCalculadas[0], potenciasCalculadas[1],
                 potenciasCalculadas[2], potenciasCalculadas[3]);

        Serial2.println(cadenaUART);

        Serial.print("[TÉRMICO] Potencias enviadas al Nano: ");
        Serial.println(cadenaUART);
    }
}
