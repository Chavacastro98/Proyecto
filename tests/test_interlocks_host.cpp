/**
 * =================================================================================
 * PRUEBAS DE HOST C++ NATIVAS: INTERLOCKS DE SEGURIDAD (test_interlocks_host.cpp)
 * =================================================================================
 * Ejecuta las pruebas de seguridad directamente contra el código C++ real
 * sin dependencias de Arduino (Unity / Standalone Assertion Runner).
 * =================================================================================
 */

#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include "../firmware/comun/interlocks_core.h"

static int g_tests_run = 0;
static int g_tests_passed = 0;

#define TEST_ASSERT(cond, msg) do { \
    g_tests_run++; \
    if (!(cond)) { \
        fprintf(stderr, "FAIL: %s (line %d)\n", msg, __LINE__); \
        exit(1); \
    } else { \
        g_tests_passed++; \
    } \
} while(0)

void test_encendido_seguro() {
    // 1. Apagado siempre permitido
    ValidacionInterlock_t v1 = core_validar_encendido_fuente(false, true, true, false);
    TEST_ASSERT(v1.autorizado == true, "Apagado debe permitirse siempre");

    // 2. Bloqueado si Fail-Safe
    ValidacionInterlock_t v2 = core_validar_encendido_fuente(true, true, false, true);
    TEST_ASSERT(v2.autorizado == false, "Encendido bloqueado por Fail-Safe");

    // 3. Bloqueado si pH activo
    ValidacionInterlock_t v3 = core_validar_encendido_fuente(true, false, true, true);
    TEST_ASSERT(v3.autorizado == false, "Encendido bloqueado por pH activo");

    // 4. Bloqueado si DAC no inicializado (S5)
    ValidacionInterlock_t v4 = core_validar_encendido_fuente(true, false, false, false);
    TEST_ASSERT(v4.autorizado == false, "Encendido bloqueado por DAC no inicializado");

    // 5. Autorizado si todo OK
    ValidacionInterlock_t v5 = core_validar_encendido_fuente(true, false, false, true);
    TEST_ASSERT(v5.autorizado == true, "Encendido autorizado cuando condiciones son seguras");
}

void test_recorte_corriente_y_conversion() {
    // S2: Recorte a 2030 LSB (3.50 A)
    int dac_clamped = core_recortar_dac_setpoint(4095, CORE_VCSS_DAC_MAX_PERMITIDO);
    TEST_ASSERT(dac_clamped == 2030, "DAC 4095 debe recortarse a 2030 LSB");

    int dac_neg = core_recortar_dac_setpoint(-50, CORE_VCSS_DAC_MAX_PERMITIDO);
    TEST_ASSERT(dac_neg == 0, "DAC negativo debe recortarse a 0");

    float amps = core_calcular_amperios_desde_dac(2030, CORE_VCSS_GM_NOMINAL, CORE_VCSS_VREF_DAC);
    TEST_ASSERT(fabsf(amps - 3.50f) < 0.02f, "Amperios convertidos deben ser ~3.50 A");
}

void test_evaluacion_sobretemperatura() {
    // S1: T >= SP + 3.0 por 3000 ms
    float sp = 60.0f;
    float temp_alta = 63.5f;

    bool disparo_rapido = core_evaluar_sobretemperatura(temp_alta, sp, CORE_TEMP_OVERHEAT_DELTA_C, 1000, 2500, CORE_TEMP_OVERHEAT_HOLD_MS);
    TEST_ASSERT(disparo_rapido == false, "No debe disparar si transcurren solo 1500 ms");

    bool disparo_sostenido = core_evaluar_sobretemperatura(temp_alta, sp, CORE_TEMP_OVERHEAT_DELTA_C, 1000, 4100, CORE_TEMP_OVERHEAT_HOLD_MS);
    TEST_ASSERT(disparo_sostenido == true, "Debe disparar Latch al sostenerse por 3100 ms");
}

void test_evaluacion_sobrecorriente_y_celda_abierta() {
    // S3: Sobrecorriente > 3.50 A por 200 ms
    bool oc_transitorio = core_evaluar_sobrecorriente(3.80f, CORE_VCSS_IMAX_PERMITIDA, 1000, 1100, CORE_VCSS_OVERCURRENT_HOLD_MS);
    TEST_ASSERT(oc_transitorio == false, "Sobrecorriente de 100 ms no debe disparar latch");

    bool oc_sostenida = core_evaluar_sobrecorriente(3.80f, CORE_VCSS_IMAX_PERMITIDA, 1000, 1250, CORE_VCSS_OVERCURRENT_HOLD_MS);
    TEST_ASSERT(oc_sostenida == true, "Sobrecorriente sostenida por 250 ms debe disparar latch");

    // S3: Celda abierta < 0.05 A con consigna > 0.30 A por 1000 ms
    bool open_transitoria = core_evaluar_celda_abierta(0.00f, 1.50f, 1000, 1500, CORE_VCSS_OPEN_CIRCUIT_HOLD_MS);
    TEST_ASSERT(open_transitoria == false, "Celda abierta por 500 ms no debe disparar");

    bool open_sostenida = core_evaluar_celda_abierta(0.00f, 1.50f, 1000, 2100, CORE_VCSS_OPEN_CIRCUIT_HOLD_MS);
    TEST_ASSERT(open_sostenida == true, "Celda abierta por 1100 ms debe disparar latch");
}

void test_crc8() {
    // S7: Validación de cálculo de CRC8
    const uint8_t test_data[] = {50, 50, 0, 0, 1};
    uint8_t crc1 = core_calcular_crc8(test_data, sizeof(test_data));
    uint8_t crc2 = core_calcular_crc8(test_data, sizeof(test_data));
    TEST_ASSERT(crc1 == crc2, "CRC8 debe ser determinista");
    TEST_ASSERT(crc1 != 0, "CRC8 debe calcular valor no nulo para trama de prueba");
}

int main() {
    printf("=================================================================\n");
    printf("EJECUTANDO PRUEBAS UNITARIAS DE HOST C++: INTERLOCKS Y SEGURIDAD\n");
    printf("=================================================================\n");

    test_encendido_seguro();
    test_recorte_corriente_y_conversion();
    test_evaluacion_sobretemperatura();
    test_evaluacion_sobrecorriente_y_celda_abierta();
    test_crc8();

    printf("[OK] Todas las pruebas pasaron: %d/%d aserciones verificadas.\n", g_tests_passed, g_tests_run);
    return 0;
}
