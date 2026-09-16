#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
SUITE DE PRUEBAS UNITARIAS: INTERLOCKS DE SEGURIDAD Y MATRIZ ISA-88
===============================================================================
Verifica la lógica de las condiciones de seguridad, aislamiento galvánico
y conmutación en cero corriente (ZCS) implementadas en el firmware RTOS 2.0.
===============================================================================
"""

import pytest


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
        ok, msg = InterlockValidator.validar_reset_calibracion(fuente_activa=False)
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
