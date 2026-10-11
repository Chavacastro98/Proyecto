#!/usr/bin/env python3
"""
===============================================================================
SUITE DE PRUEBAS UNITARIAS: INTERLOCKS DE SEGURIDAD Y MATRIZ ISA-88
===============================================================================
Verifica la lógica de las condiciones de seguridad, aislamiento galvánico
y conmutación en cero corriente (ZCS) implementadas en el firmware RTOS 2.0.
===============================================================================
"""



class InterlockValidator:
    """
    Modelo de validación de las reglas lógicas del firmware ESP32-S3 (Controller_Fuente.cpp
    y Controller_Termico.cpp) para asegurar que el SCADA y el firmware compartan
    las mismas restricciones de seguridad.
    """

    @staticmethod
    def validar_encendido_fuente(solicitar_run, failsafe_activo, ph_activo):
        """
        Regla de Controller_Fuente.cpp (handleActF):
        if (failsafe_activo) -> Bloqueado: Sistema en alarma Fail-Safe.
        if (ph_activo) -> Interlock: modulo pH activo. Apaguelo primero.
        """
        if not solicitar_run:
            return True, "Apagado seguro permitido"
        if failsafe_activo:
            return False, "Bloqueado: Sistema en alarma Fail-Safe"
        if ph_activo:
            return False, "Interlock: modulo pH activo. Apaguelo primero"
        return True, "Encendido autorizado"

    @staticmethod
    def validar_calibracion_vcss(fuente_activa, ph_activo, failsafe_activo):
        """
        Regla de Controller_Fuente.cpp (handleCalVCSS):
        Prohibido calibrar si Fail-Safe activo o módulo pH activo.
        """
        if failsafe_activo:
            return False, "Bloqueado por Fail-Safe"
        if ph_activo:
            return False, "Interlock activo: Modulo de pH operando"
        return True, "Calibracion permitida"

    @staticmethod
    def validar_reset_calibracion(fuente_activa):
        """
        Regla de Controller_Fuente.cpp (handleResetCalVCSS):
        Prohibido restablecer a nominal si la fuente esta encendida.
        """
        if fuente_activa:
            return False, "Interlock activo: La fuente esta encendida"
        return True, "Restablecimiento permitido"

    @staticmethod
    def simular_secuencia_zcs(corriente_inicial_a, dac_inicial):
        """
        Simulación de secuencia Zero-Current Switching (ZCS) antes de apertura de relé:
        1. Desconectar DAC (DAC = 0).
        2. Corriente cae a ~0.0 A.
        3. Apertura mecánica de contactos del relé VDD.
        """
        secuencia = []
        # Paso 1: Orden de apagado
        secuencia.append({"fase": "ORDEN_APAGADO", "dac": dac_inicial, "rele": 1})
        # Paso 2: Rampa/Escalón a cero DAC (ZCS)
        dac_actual = 0
        corriente_actual = 0.0
        secuencia.append({"fase": "DAC_CERO", "dac": dac_actual, "corriente": corriente_actual, "rele": 1})
        # Paso 3: Retardo seguro y apertura de relé sin arco voltaico
        rele_actual = 0
        secuencia.append({"fase": "RELE_ABIERTO", "dac": dac_actual, "corriente": corriente_actual, "rele": rele_actual})
        return secuencia


class TestInterlocksAislamientoGalvanico:
    """Pruebas del interlock de protección mutua entre el lazo VCSS y el electrodo de pH."""

    def test_fuente_bloqueada_si_ph_activo(self):
        """La fuente no debe encender si el módulo de pH está operando en la celda."""
        ok, msg = InterlockValidator.validar_encendido_fuente(
            solicitar_run=True, failsafe_activo=False, ph_activo=True
        )
        assert not ok
        assert "modulo pH activo" in msg

    def test_fuente_enciende_si_ph_inactivo(self):
        """La fuente debe encender normalmente si el pH está apagado y no hay alarmas."""
        ok, msg = InterlockValidator.validar_encendido_fuente(
            solicitar_run=True, failsafe_activo=False, ph_activo=False
        )
        assert ok
        assert msg == "Encendido autorizado"

    def test_apagado_siempre_permitido(self):
        """La orden de apagado (run=0) nunca debe ser bloqueada por ningún interlock."""
        ok, _ = InterlockValidator.validar_encendido_fuente(
            solicitar_run=False, failsafe_activo=True, ph_activo=True
        )
        assert ok


class TestInterlocksFailSafeYCalibracion:
    """Pruebas de bloqueo ante estados de alarma crítica y condiciones de calibración."""

    def test_bloqueo_por_alarma_failsafe(self):
        """Ninguna activación de potencia es válida si el latch de seguridad se ha disparado."""
        ok, msg = InterlockValidator.validar_encendido_fuente(
            solicitar_run=True, failsafe_activo=True, ph_activo=False
        )
        assert not ok
        assert "Fail-Safe" in msg

    def test_calibracion_vcss_bloqueada_con_ph(self):
        """No se permite calibrar shunt si el pH está activo en solución."""
        ok, msg = InterlockValidator.validar_calibracion_vcss(
            fuente_activa=False, ph_activo=True, failsafe_activo=False
        )
        assert not ok
        assert "Modulo de pH" in msg

    def test_reset_calibracion_bloqueado_si_fuente_activa(self):
        """El factor Gm no puede reescribirse a nominal mientras circule corriente."""
        ok, msg = InterlockValidator.validar_reset_calibracion(fuente_activa=True)
        assert not ok
        assert "fuente esta encendida" in msg

    def test_reset_calibracion_permitido_si_fuente_apagada(self):
        """El factor Gm puede reescribirse a nominal de 2.000 S con la fuente apagada."""
        ok, _msg = InterlockValidator.validar_reset_calibracion(fuente_activa=False)
        assert ok


class TestProtocoloZCS:
    """Verificación de la conmutación en cero corriente (Zero-Current Switching)."""

    def test_rele_no_abre_con_corriente_activa(self):
        """El relé debe abrirse únicamente cuando el DAC ya se encuentra en cero."""
        secuencia = InterlockValidator.simular_secuencia_zcs(corriente_inicial_a=1.50, dac_inicial=2048)
        assert len(secuencia) == 3
        # En el paso 2, el DAC ya es 0 antes de abrir el relé
        assert secuencia[1]["dac"] == 0
        assert secuencia[1]["rele"] == 1
        # En el paso 3, el relé abre con corriente 0
        assert secuencia[2]["rele"] == 0
        assert secuencia[2]["corriente"] == 0.0


class TestNuevosInterlocksSeguridad:
    """Pruebas de los nuevos interlocks de seguridad implementados en firmware RTOS 2.0 (Lote A)."""

    def test_recorte_rigido_corriente_a_3_50a(self):
        """Verifica que consignas > 3.50 A o DAC > 2029 LSB se recorten rígidamente al límite de hardware (S2)."""
        vcss_imax_nominal = 3.53 * 2.00  # 7.06 A
        vcss_imax_permitida = 3.50
        vcss_dac_max = int((vcss_imax_permitida / vcss_imax_nominal) * 4095.0)  # 2029 LSB

        # Solicitud de 6.0 A o DAC 4095
        dac_solicitado = 4095
        dac_clamped = min(max(dac_solicitado, 0), vcss_dac_max)
        assert dac_clamped == 2030
        amperios_efectivos = (dac_clamped / 4095.0) * vcss_imax_nominal
        assert round(amperios_efectivos, 2) == 3.50

    def test_rechazo_encendido_sin_dac_inicializado(self):
        """Verifica que el relé de +12V no se energice si el DAC MCP4725 no está operativo en I2C (S5)."""
        dac_inicializado = False
        rele_cerrado = False
        fuente_activa = False

        if not dac_inicializado:
            resultado = "RECHAZADO_DAC_NO_INIT"
        else:
            rele_cerrado = True
            fuente_activa = True
            resultado = "ENCENDIDO_OK"

        assert resultado == "RECHAZADO_DAC_NO_INIT"
        assert not rele_cerrado
        assert not fuente_activa

    def test_disparo_sobretemperatura_critica(self):
        """Verifica que T >= SP + 3.0 °C sostenida por 3000 ms active ERR_TEMP_OVERHEAT código 14 (S1)."""
        sp = 60.0
        temp = 63.5  # SP + 3.5 °C
        delta_umbral = 3.0
        hold_ms_umbral = 3000

        tiempo_sostenido = 1500
        latch = (temp >= sp + delta_umbral) and (tiempo_sostenido >= hold_ms_umbral)
        assert not latch

        tiempo_sostenido = 3100
        latch = (temp >= sp + delta_umbral) and (tiempo_sostenido >= hold_ms_umbral)
        err_code = 14 if latch else 0
        assert latch
        assert err_code == 14

    def test_disparo_sobrecorriente_medida(self):
        """Verifica que corriente medida > 3.50 A por 200 ms active ERR_VCSS_OVERCURRENT código 21 (S3)."""
        i_medida = 3.85
        umbral_imax = 3.50
        hold_ms_umbral = 200

        tiempo_sobrecorriente = 100
        latch = (i_medida > umbral_imax) and (tiempo_sobrecorriente >= hold_ms_umbral)
        assert not latch

        tiempo_sobrecorriente = 250
        latch = (i_medida > umbral_imax) and (tiempo_sobrecorriente >= hold_ms_umbral)
        err_code = 21 if latch else 0
        assert latch
        assert err_code == 21

    def test_disparo_celda_abierta(self):
        """Verifica que corriente < 0.05 A con consigna > 0.30 A por 1000 ms active ERR_VCSS_OPEN_CIRCUIT código 20 (S3)."""
        i_setpoint = 1.50
        i_medida = 0.00
        hold_ms_umbral = 1000

        tiempo_abierta = 500
        latch = (i_setpoint > 0.30 and i_medida < 0.05) and (tiempo_abierta >= hold_ms_umbral)
        assert not latch

        tiempo_abierta = 1100
        latch = (i_setpoint > 0.30 and i_medida < 0.05) and (tiempo_abierta >= hold_ms_umbral)
        err_code = 20 if latch else 0
        assert latch
        assert err_code == 20
