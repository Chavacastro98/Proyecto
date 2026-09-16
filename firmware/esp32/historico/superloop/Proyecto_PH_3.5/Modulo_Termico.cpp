#include "Modulo_Termico.h"
#include "config.h"

/**
 * =================================================================================
 * IMPLEMENTACIÓN DEL CONTROL TÉRMICO (Modulo_Termico.cpp)
 * =================================================================================
 * Aquí se implementa el algoritmo de control PI que mantiene la temperatura de
 * cada tina en el valor deseado, y la comunicación serie con el Arduino Nano
 * para transmitir los porcentajes de potencia calculados.
 *
 * El mutex (muxTermico) se usa siempre que se leen o escriben las variables
 * del canal porque el servidor web puede modificarlas al mismo tiempo que
 * este módulo las está usando para sus cálculos.
 * =================================================================================
 */

// Candado de protección para las variables compartidas del control térmico
portMUX_TYPE muxTermico = portMUX_INITIALIZER_UNLOCKED;

// Definición de los 4 canales de calentamiento con sus pines y ganancias PI.
// Las ganancias (Kp, Ki) están calibradas según la inercia térmica de cada tina.
CanalTermico canales[] = {
    CanalTermico(0, COMMON_SCK, 5,  COMMON_SO, 62.65f, 0.0897f), // Canal 0: Limpieza (450W)
    CanalTermico(1, COMMON_SCK, 4,  COMMON_SO, 62.65f, 0.0897f), // Canal 1: Decapado (450W)
    CanalTermico(2, COMMON_SCK, 13, COMMON_SO, 16.71f, 0.0239f), // Canal 2: Celda Hull (18W)
    CanalTermico(3, COMMON_SCK, 14, COMMON_SO, 62.51f, 0.0895f)  // Canal 3: Niquelado (450W)
};

/**
 * Configura los pines de selección SPI de los 4 sensores MAX6675.
 * Se ponen en HIGH (deshabilitados) para evitar conflictos en el bus SPI.
 */
void inicializarModuloTermico() {
    lastPI = millis();
    lastRamp = millis();

    for (int i = 0; i < 4; i++) {
        pinMode(canales[i].pinCS, OUTPUT);
        digitalWrite(canales[i].pinCS, HIGH);
    }
}

/**
 * Algoritmo de control PI con protecciones de seguridad.
 * 
 * FUNCIONAMIENTO:
 * 1. Lee la temperatura del sensor MAX6675
 * 2. Si la lectura es inválida, apaga el canal por seguridad
 * 3. Calcula el error: diferencia entre setpoint y temperatura actual
 * 4. Aplica la fórmula PI: salida = Kp*error + Ki*integral
 * 5. Limita la salida entre 0% y 100%
 *
 * @return Porcentaje de potencia (0 a 100 %)
 */
int CanalTermico::calcularPI() {
    // 1. Leer la temperatura del sensor
    float input = (float)sensor.readCelsius();
    
    // PROTECCIÓN: Si el sensor da una lectura imposible (desconectado, dañado, etc.),
    // apagar el canal inmediatamente para evitar sobrecalentamiento
    if (isnan(input) || input <= 0.0f || input >= 150.0f) {
        portENTER_CRITICAL(&muxTermico);
        activo = false;
        integral = 0.0f;
        temperatura = 0.0f;
        portEXIT_CRITICAL(&muxTermico);
        return 0; // 0% de potencia = resistencia apagada
    }

    // 2. Guardar la temperatura leída y obtener copias locales para los cálculos
    portENTER_CRITICAL(&muxTermico);
    temperatura = input;
    float tempLocal = temperatura;
    float spLocal = setpoint;
    bool activoLocal = activo;
    portEXIT_CRITICAL(&muxTermico);

    // Si el canal está apagado desde la interfaz web, no calentar
    if (!activoLocal) {
        portENTER_CRITICAL(&muxTermico);
        integral = 0.0f;
        portEXIT_CRITICAL(&muxTermico);
        return 0;
    }

    // PROTECCIÓN: Si la temperatura superó el setpoint por más de 2°C,
    // cortar la potencia completamente (el sistema solo calienta, no enfría)
    if (tempLocal >= (spLocal + 2.0f)) {
        return 0;
    }

    // 3. Calcular el error de temperatura
    float error = spLocal - tempLocal;

    // 4. Acción Proporcional: responde proporcionalmente al error actual
    float P = Kp * error;

    // 5. Acción Integral: acumula el error a lo largo del tiempo para
    //    eliminar diferencias pequeñas pero persistentes (error en estado estable).
    //    Se limita (anti-windup) para que no se acumule demasiado.
    portENTER_CRITICAL(&muxTermico);
    integral += error * 1.0f; // Período de muestreo = 1 segundo
    if (Ki > 0.0f) {
        // No dejar que la integral sola supere el 100% de la salida
        if (integral * Ki > 100.0f) integral = 100.0f / Ki;
        // No acumular valores negativos (el sistema solo calienta, nunca enfría)
        if (integral * Ki < 0.0f)   integral = 0.0f;
    }
    float I = Ki * integral;
    portEXIT_CRITICAL(&muxTermico);

    // 6. Salida total = P + I, limitada entre 0% y 100%
    float salida = P + I;
    return (int)constrain(salida, 0.0f, 100.0f);
}

/**
 * Función ejecutada en el bucle principal. Maneja dos tareas temporizadas:
 * 1. Rampa de arranque suave (cada 200 ms): sube el límite de potencia 1% por ciclo
 * 2. Cálculo PI y envío al Arduino Nano (cada 1000 ms)
 */
void procesarControlTermico() {
    unsigned long timestampActual = millis();

    // --- RAMPA DE ARRANQUE SUAVE (cada 200 ms) ---
    // Al encender, la potencia máxima permitida sube gradualmente de 0% a 100%
    // para evitar picos de corriente en los TRIACs al arrancar las resistencias.
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

    // --- CÁLCULO PI Y ENVÍO DE POTENCIAS (cada 1000 ms) ---
    if (timestampActual - lastPI >= 1000) {
        lastPI = timestampActual;

        int potenciasCalculadas[4] = {0, 0, 0, 0};

        // Calcular la potencia de cada canal y limitarla por la rampa de arranque
        for (int i = 0; i < 4; i++) {
            int u_pi = canales[i].calcularPI();
            
            portENTER_CRITICAL(&muxTermico);
            float limLocal = canales[i].limitePotencia;
            int pot = (int)min((float)u_pi, limLocal);
            canales[i].potenciaActual = pot;
            portEXIT_CRITICAL(&muxTermico);

            potenciasCalculadas[i] = pot;
        }

        // Enviar los 4 porcentajes al Arduino Nano por comunicación serie
        // Formato: "pot0,pot1,pot2,pot3" (ejemplo: "50,0,100,25")
        char cadenaUART[32];
        snprintf(cadenaUART, sizeof(cadenaUART), "%d,%d,%d,%d",
                 potenciasCalculadas[0], potenciasCalculadas[1],
                 potenciasCalculadas[2], potenciasCalculadas[3]);

        Serial2.println(cadenaUART);

        // Mostrar en la consola USB para depuración
        Serial.print("[TÉRMICO] Potencias enviadas al Nano: ");
        Serial.println(cadenaUART);
    }
}