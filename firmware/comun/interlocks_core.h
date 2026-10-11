#ifndef INTERLOCKS_CORE_H
#define INTERLOCKS_CORE_H

/**
 * =================================================================================
 * NÚCLEO DESACOPLADO DE INTERLOCKS Y SEGURIDAD INDUSTRIAL (interlocks_core.h)
 * =================================================================================
 * Biblioteca C++ pura (sin dependencias del SDK de Arduino) que encapsula las
 * reglas lógicas de seguridad, interlocks de procesos químicos (ISA-88) y cálculo
 * de límites metrológicos del sistema.
 *
 * Utilizable tanto en el firmware embebido (ESP32-S3 RTOS 2.0) como en suites de
 * pruebas unitarias en host (GoogleTest, Unity, CTypes o CFFI).
 * =================================================================================
 */

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <math.h>

#ifdef __cplusplus
extern "C" {
#endif

/** Constantes unificadas de seguridad */
#define CORE_VCSS_GM_NOMINAL         2.00f
#define CORE_VCSS_VREF_DAC           3.53f
#define CORE_VCSS_IMAX_NOMINAL       7.06f  // (3.53 V * 2.00 S)
#define CORE_VCSS_IMAX_PERMITIDA     3.50f  // Límite de hardware/derating
#define CORE_VCSS_DAC_MAX_PERMITIDO  2030   // (3.50 / 7.06) * 4095
#define CORE_TEMP_OVERHEAT_DELTA_C   3.0f   // Delta sobre setpoint
#define CORE_TEMP_OVERHEAT_HOLD_MS   3000   // Tiempo de persistencia (ms)
#define CORE_VCSS_OVERCURRENT_HOLD_MS 200   // Tiempo de persistencia sobrecorriente (ms)
#define CORE_VCSS_OPEN_CIRCUIT_HOLD_MS 1000 // Tiempo de persistencia celda abierta (ms)

/** Códigos de error unificados */
typedef enum {
    CORE_ERR_NONE              = 0,
    CORE_ERR_TC0_FAIL          = 10,
    CORE_ERR_TC1_FAIL          = 11,
    CORE_ERR_TC2_FAIL          = 12,
    CORE_ERR_TC3_FAIL          = 13,
    CORE_ERR_TEMP_OVERHEAT     = 14,
    CORE_ERR_VCSS_OPEN_CIRCUIT = 20,
    CORE_ERR_VCSS_OVERCURRENT  = 21,
    CORE_ERR_I2C_ADS_LOST      = 30,
    CORE_ERR_I2C_DAC_LOST      = 31,
    CORE_ERR_RTOS_HEARTBEAT    = 40,
    CORE_ERR_UART_NANO_TIMEOUT = 50
} CoreErrorCode_t;

/** Resultado de validación de encendido */
typedef struct {
    bool autorizado;
    const char *motivo;
} ValidacionInterlock_t;

/**
 * @brief Evalúa la regla de encendido de la fuente galvánica VCSS.
 * Regla: Prohibido encender si hay Fail-Safe latched, módulo pH activo o DAC no inicializado.
 */
static inline ValidacionInterlock_t core_validar_encendido_fuente(
    bool solicitar_run,
    bool failsafe_activo,
    bool ph_activo,
    bool dac_inicializado
) {
    ValidacionInterlock_t res;
    if (!solicitar_run) {
        res.autorizado = true;
        res.motivo = "Apagado seguro permitido";
        return res;
    }
    if (failsafe_activo) {
        res.autorizado = false;
        res.motivo = "Bloqueado: Sistema en alarma Fail-Safe";
        return res;
    }
    if (ph_activo) {
        res.autorizado = false;
        res.motivo = "Interlock: modulo pH activo. Apaguelo primero";
        return res;
    }
    if (!dac_inicializado) {
        res.autorizado = false;
        res.motivo = "Rechazado: DAC MCP4725 no inicializado";
        return res;
    }
    res.autorizado = true;
    res.motivo = "Encendido autorizado";
    return res;
}

/**
 * @brief Evalúa si se permite calibrar el sumidero VCSS.
 */
static inline ValidacionInterlock_t core_validar_calibracion_vcss(
    bool fuente_activa,
    bool ph_activo,
    bool failsafe_activo
) {
    ValidacionInterlock_t res;
    if (failsafe_activo) {
        res.autorizado = false;
        res.motivo = "Bloqueado por Fail-Safe";
        return res;
    }
    if (ph_activo) {
        res.autorizado = false;
        res.motivo = "Interlock activo: Modulo de pH operando";
        return res;
    }
    res.autorizado = true;
    res.motivo = "Calibracion permitida";
    return res;
}

/**
 * @brief Evalúa si se permite restablecer la ganancia nominal VCSS.
 */
static inline ValidacionInterlock_t core_validar_reset_calibracion(bool fuente_activa) {
    ValidacionInterlock_t res;
    if (fuente_activa) {
        res.autorizado = false;
        res.motivo = "Interlock activo: La fuente esta encendida";
        return res;
    }
    res.autorizado = true;
    res.motivo = "Restablecimiento permitido";
    return res;
}

/**
 * @brief Recorta rígidamente una consigna DAC al límite seguro de corriente.
 */
static inline int core_recortar_dac_setpoint(int valor_solicitado, int dac_max_permitido) {
    if (valor_solicitado < 0) return 0;
    if (valor_solicitado > dac_max_permitido) return dac_max_permitido;
    return valor_solicitado;
}

/**
 * @brief Convierte código DAC a corriente estimada teórica (A).
 */
static inline float core_calcular_amperios_desde_dac(int dac_val, float gm_nominal, float vref_dac) {
    float v = ((float)dac_val / 4095.0f) * vref_dac;
    return v * gm_nominal;
}

/**
 * @brief Evalúa condición de sobretemperatura sostenida.
 * @return true si debe dispararse el latch Fail-Safe (ERR_TEMP_OVERHEAT).
 */
static inline bool core_evaluar_sobretemperatura(
    float temp,
    float sp,
    float delta_umbral,
    uint32_t tiempo_inicio_ms,
    uint32_t ahora_ms,
    uint32_t hold_ms
) {
    if (temp >= (sp + delta_umbral)) {
        if (tiempo_inicio_ms > 0 && (ahora_ms - tiempo_inicio_ms >= hold_ms)) {
            return true;
        }
    }
    return false;
}

/**
 * @brief Evalúa condición de sobrecorriente medida sostenida.
 * @return true si debe dispararse el latch Fail-Safe (ERR_VCSS_OVERCURRENT).
 */
static inline bool core_evaluar_sobrecorriente(
    float i_medida,
    float i_max_permitida,
    uint32_t tiempo_inicio_ms,
    uint32_t ahora_ms,
    uint32_t hold_ms
) {
    if (i_medida > i_max_permitida) {
        if (tiempo_inicio_ms > 0 && (ahora_ms - tiempo_inicio_ms >= hold_ms)) {
            return true;
        }
    }
    return false;
}

/**
 * @brief Evalúa condición de celda electroquímica abierta sostenida.
 * @return true si debe dispararse el latch Fail-Safe (ERR_VCSS_OPEN_CIRCUIT).
 */
static inline bool core_evaluar_celda_abierta(
    float i_medida,
    float i_setpoint,
    uint32_t tiempo_inicio_ms,
    uint32_t ahora_ms,
    uint32_t hold_ms
) {
    if (i_setpoint > 0.30f && i_medida < 0.05f) {
        if (tiempo_inicio_ms > 0 && (ahora_ms - tiempo_inicio_ms >= hold_ms)) {
            return true;
        }
    }
    return false;
}

/**
 * @brief Calcula CRC-8 estándar (polinomio 0x07, init 0x00) para tramas serie seguras.
 */
static inline uint8_t core_calcular_crc8(const uint8_t *data, size_t len) {
    uint8_t crc = 0x00;
    for (size_t i = 0; i < len; i++) {
        crc ^= data[i];
        for (uint8_t b = 0; b < 8; b++) {
            if (crc & 0x80) {
                crc = (crc << 1) ^ 0x07;
            } else {
                crc <<= 1;
            }
        }
    }
    return crc;
}

#ifdef __cplusplus
}
#endif

#endif // INTERLOCKS_CORE_H
