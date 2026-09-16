#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de verificación del interlock de seguridad del relé y temporizador en gestor_ensayos.
"""
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Incluir carpeta telemetria2.0 en path
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(base_dir, "software", "telemetria2.0"))

from gestor_ensayos import GestorEnsayosMixin


class MockApp(GestorEnsayosMixin):
    def __init__(self):
        self.root = MagicMock()
        self.excel_path = ""
        self.lista_placas = []
        self.placa_activa = {
            "num": 1,
            "ronda": "Ronda 1",
            "limpieza_s": 240,
            "matizado_s": 120,
            "ph": 2,
            "temp_zin": 25,
            "tiem_zin_s": 120,
            "pulsado": 0,
            "tiem_niq_s": 600,
            "tag_filtro": "pH 2 — 25°C"
        }
        self.etapa_activa_idx = 0
        self.etapa_corriendo = False
        self.etapa_duracion_total = 240
        self.etapa_segundos_restantes = 240
        self.etapa_segundos_transcurridos = 0
        self.t_inicio_etapa_real = None
        self.t_acumulado_etapa = 0.0
        self.modo_demo = False
        self.grabando = True

        # Widgets simulados
        self.lbl_etapa_titulo = MagicMock()
        self.lbl_timer_big = MagicMock()
        self.btn_stage_toggle = MagicMock()
        self.lbl_aviso_etapa = MagicMock()
        self.btn_stage_prev = MagicMock()
        self.lbl_hw_sync_status = MagicMock()
        self.lbl_e1 = MagicMock()
        self.lbl_e2 = MagicMock()
        self.lbl_e3 = MagicMock()
        self.lbl_e4 = MagicMock()
        self.var_auto_sync_hw = MagicMock()
        self.var_auto_sync_hw.get.return_value = True
        self.buf_t = [0.0]
        self.marcadores_etapas = []

        # Registro de comandos HTTP simulados
        self.comandos_enviados = []

    def enviar_setpoints_esp32(self, feedback_usuario=False):
        # Versión adaptada para capturar el valor de run enviado
        nombre, dur, sp_t, curr_sp, modo_corr = self._obtener_datos_etapa_actual()
        debe_energizar = bool(getattr(self, 'etapa_corriendo', False) and self.etapa_activa_idx in (2, 3))
        run_val = 1 if debe_energizar else 0
        self.comandos_enviados.append({
            "accion": "setpoints",
            "etapa_idx": self.etapa_activa_idx,
            "nombre": nombre,
            "etapa_corriendo": self.etapa_corriendo,
            "run_val": run_val,
            "curr_sp": curr_sp
        })

    def apagar_fuente_esp32(self, feedback_usuario=False):
        self.comandos_enviados.append({
            "accion": "apagar_fuente",
            "etapa_idx": self.etapa_activa_idx,
            "run_val": 0
        })

    def iniciar_grabacion(self):
        pass


class TestInterlockSeguridad(unittest.TestCase):

    def setUp(self):
        self.app = MockApp()

    def test_interlock_al_dar_siguiente(self):
        """Verifica que al avanzar entre etapas NUNCA se suministre corriente antes de iniciar."""
        # 1. En Etapa 1 (Limpieza)
        self.assertEqual(self.app.etapa_activa_idx, 0)
        self.assertFalse(self.app.etapa_corriendo)

        # 2. Avanzar de Etapa 1 a Etapa 2 (Decapado)
        self.app.avanzar_siguiente_etapa()
        self.assertEqual(self.app.etapa_activa_idx, 1)
        self.assertFalse(self.app.etapa_corriendo)
        # El último setpoint enviado debe tener run_val == 0
        ultimo_sp = [c for c in self.app.comandos_enviados if c["accion"] == "setpoints"][-1]
        self.assertEqual(ultimo_sp["run_val"], 0, "En etapa 2 no debe haber corriente")

        # 3. Avanzar de Etapa 2 a Etapa 3 (Zincado) -> CASO CRÍTICO REPORTADO POR EL USUARIO
        self.app.avanzar_siguiente_etapa()
        self.assertEqual(self.app.etapa_activa_idx, 2)
        self.assertFalse(self.app.etapa_corriendo, "La etapa 3 NO debe estar corriendo al dar Siguiente")
        
        # Debe haberse llamado apagar_fuente_esp32 antes de entrar a etapa 3
        apagados = [c for c in self.app.comandos_enviados if c["accion"] == "apagar_fuente"]
        self.assertTrue(len(apagados) > 0, "Debe asegurarse corte previo de fuente")

        ultimo_sp = [c for c in self.app.comandos_enviados if c["accion"] == "setpoints"][-1]
        self.assertEqual(ultimo_sp["run_val"], 0, "PELIGRO: El relé se cerró automáticamente al dar Siguiente entre etapa 2 y 3")

        # 4. Operador pulsa explícitamente '▶ Iniciar Etapa' en Zincado
        self.app.toggle_etapa()
        self.assertTrue(self.app.etapa_corriendo, "La etapa debe estar corriendo tras presionar Iniciar")
        ultimo_sp = [c for c in self.app.comandos_enviados if c["accion"] == "setpoints"][-1]
        self.assertEqual(ultimo_sp["run_val"], 1, "La corriente DEBE activarse al pulsar Iniciar Etapa")

        # 5. Operador pulsa '⏸ Pausar'
        self.app.toggle_etapa()
        self.assertFalse(self.app.etapa_corriendo)
        ultimo_cmd = self.app.comandos_enviados[-1]
        self.assertEqual(ultimo_cmd["accion"], "apagar_fuente")
        self.assertEqual(ultimo_cmd["run_val"], 0, "La corriente DEBE cortarse inmediatamente al pausar")

        # 6. Avanzar de Etapa 3 a Etapa 4 (Niquelado) -> SEGUNDO CASO REPORTADO POR EL USUARIO
        self.app.avanzar_siguiente_etapa()
        self.assertEqual(self.app.etapa_activa_idx, 3)
        self.assertFalse(self.app.etapa_corriendo, "La etapa 4 NO debe estar corriendo al dar Siguiente")
        ultimo_sp = [c for c in self.app.comandos_enviados if c["accion"] == "setpoints"][-1]
        self.assertEqual(ultimo_sp["run_val"], 0, "PELIGRO: El relé se cerró automáticamente al dar Siguiente entre etapa 3 y 4")

        # 7. Operador pulsa '▶ Iniciar Etapa' en Niquelado
        self.app.toggle_etapa()
        self.assertTrue(self.app.etapa_corriendo)
        ultimo_sp = [c for c in self.app.comandos_enviados if c["accion"] == "setpoints"][-1]
        self.assertEqual(ultimo_sp["run_val"], 1, "La corriente de 1.13A DEBE activarse al pulsar Iniciar")
        self.assertEqual(ultimo_sp["curr_sp"], 1.13)


if __name__ == "__main__":
    unittest.main()
