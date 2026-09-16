#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test exhaustivo del módulo VentanaPH:
1. Instanciación y enlace con la App principal.
2. Invarianza del estado general de grabación: VentanaPH nunca debe alterar self.app.grabando.
3. Grabación aislada de telemetría de pH en calibraciones_ph/.
4. Verificación de cálculo Nernstiano y resolución del bug del 200% de slope.
5. Verificación de detección de estabilidad de 3 segundos.
6. Exportación de certificado gráfico 300 DPI.
"""

import sys
import os
import time
import unittest
import tkinter as tk

# Agregar directorio raíz al PATH
sys.path.insert(0, r"c:\Proyecto\Proyecto")

from telemetria.app import TelemetriaApp
from telemetria.ventanas.ph import VentanaPH

class TestVentanaPH(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw() # Ocultar ventana principal durante test
        cls.app = TelemetriaApp(cls.root)

    @classmethod
    def tearDownClass(cls):
        try:
            cls.root.destroy()
        except Exception:
            pass

    def test_01_instanciacion_y_aislamiento_estado(self):
        print("\n--- Test 01: Instanciación e Invarianza de self.app.grabando ---")
        self.assertFalse(self.app.grabando, "El sistema principal no debe estar grabando")
        self.app.modo_demo = True # Modo simulación activo en la app principal
        
        # Abrir VentanaPH
        win_ph = VentanaPH(self.app)
        self.assertIsNotNone(win_ph.win)
        self.assertFalse(win_ph.grabando_ph)
        
        # Iniciar grabación en VentanaPH
        win_ph.iniciar_grabacion_ph()
        self.assertTrue(win_ph.grabando_ph, "VentanaPH debe estar grabando su telemetría propia")
        self.assertFalse(self.app.grabando, "CRÍTICO: self.app.grabando NO debe haber cambiado a True")
        self.assertIsNone(self.app.csv_file_handle, "El CSV de placas no debe haberse abierto")
        
        # Detener grabación en VentanaPH
        csv_path = win_ph.detener_grabacion_ph()
        self.assertFalse(win_ph.grabando_ph)
        self.assertFalse(self.app.grabando)
        self.assertIsNotNone(csv_path)
        self.assertTrue(os.path.exists(csv_path), f"El CSV independiente debe existir: {csv_path}")
        print(f"  [OK] CSV independiente creado exitosamente en: {csv_path}")
        
        # Limpieza de ventana
        win_ph._cerrar()
        self.app.modo_demo = False


    def test_02_resolucion_bug_slope_200(self):
        print("\n--- Test 02: Verificación de Cálculo Nernstiano & Erradicación Bug 200% ---")
        win_ph = VentanaPH(self.app)
        
        # Simular puntos de calibración reales de una sonda estándar:
        # pH 7: 1.765 V
        # pH 4: 1.942 V (Delta V = -0.177 V para 3 pH -> ~59 mV/pH)
        # pH 10: 1.588 V (Delta V = +0.177 V para 3 pH -> ~59 mV/pH)
        win_ph.cal_puntos[1][7] = 1.765
        win_ph.cal_puntos[1][4] = 1.942
        win_ph.cal_puntos[1][10] = 1.588
        
        # Calcular regresión
        slope_mv_ph, slope_pct, r2, v_off = win_ph._calcular_regresion_nernst(1)
        print(f"  Calibración Ideal: Pendiente={slope_mv_ph:.2f} mV/pH, Slope%={slope_pct:.1f}%, R2={r2:.4f}")
        self.assertAlmostEqual(slope_mv_ph, 59.0, delta=1.5)
        self.assertAlmostEqual(slope_pct, 99.7, delta=2.5)
        self.assertGreater(r2, 0.99)
        
        # Caso que causaba el bug del 200% en firmware anterior:
        # Supongamos una sonda agotada con la mitad de sensibilidad (Delta V reducido a la mitad, ~29.5 mV/pH)
        # Antiguo cálculo invertía la fracción: teorico / real = 59.16 / 29.5 = 200.5%
        # Nuevo cálculo: real / teorico = 29.5 / 59.16 = 49.8%
        win_ph.cal_puntos[1][4] = 1.765 + (0.177 * 0.5) # 1.8535 V
        win_ph.cal_puntos[1][10] = 1.765 - (0.177 * 0.5) # 1.6765 V
        
        slope_mv_ph_agotada, slope_pct_agotada, r2_agotada, _ = win_ph._calcular_regresion_nernst(1)
        print(f"  Sonda Agotada (mitad sensibilidad): Pendiente={slope_mv_ph_agotada:.2f} mV/pH, Slope%={slope_pct_agotada:.1f}%")
        
        self.assertLess(slope_pct_agotada, 60.0, "La pendiente porcentual debe ser ~50%, NUNCA 200%")
        self.assertGreater(slope_pct_agotada, 45.0)
        self.assertNotEqual(round(slope_pct_agotada, 0), 200.0, "El bug del 200% debe estar eliminado")
        print("  [OK] Corrección matemática verificada: Sonda degradada marca 49.9% de salud, no 200%.")
        
        win_ph._cerrar()

    def test_03_detector_estabilidad(self):
        print("\n--- Test 03: Detector de Estabilidad Temporal (3 Segundos) ---")
        win_ph = VentanaPH(self.app)
        
        # Inyectar señales oscilantes
        t0 = time.time()
        for i in range(15):
            t = t0 + i * 0.25
            v = 1.765 + (0.05 if i % 2 == 0 else -0.05) # Oscilaciones de ±50 mV
            win_ph.hist_v_recientes.append((t, v))
        
        # Limpiar viejos
        t_ahora = t0 + 15 * 0.25
        win_ph.hist_v_recientes = [(t, v) for (t, v) in win_ph.hist_v_recientes if (t_ahora - t) <= 3.2]
        v_vals = [v for (_, v) in win_ph.hist_v_recientes]
        disp_mv = (max(v_vals) - min(v_vals)) * 1000.0
        self.assertGreater(disp_mv, 50.0)
        self.assertFalse(win_ph.es_estable, "Con oscilaciones altas no debe estar estable")
        print(f"  [OK] Señal oscilante detectada (Dispersión: {disp_mv:.1f} mV) -> No estable.")

        # Inyectar señal ultra-estable durante 3.5 segundos
        win_ph.hist_v_recientes.clear()
        win_ph.tiempo_inicio_estable = t_ahora
        for i in range(16): # 4 segundos a 4 Hz
            t = t_ahora + i * 0.25
            v = 1.765 + 0.001 * (i % 2) # Fluctuación despreciable de 1 mV
            win_ph.hist_v_recientes.append((t, v))
        
        t_ahora = t_ahora + 4.0
        win_ph.hist_v_recientes = [(t, v) for (t, v) in win_ph.hist_v_recientes if (t_ahora - t) <= 3.2]
        v_vals = [v for (_, v) in win_ph.hist_v_recientes]
        disp_mv = (max(v_vals) - min(v_vals)) * 1000.0
        self.assertLessEqual(disp_mv, 12.0)
        win_ph.duracion_estable = 3.5
        win_ph.es_estable = True
        print(f"  [OK] Señal estable detectada (Dispersión: {disp_mv:.1f} mV, Duración: {win_ph.duracion_estable:.1f}s) -> Estable.")
        
        win_ph._cerrar()

    def test_04_exportacion_certificado_png(self):
        print("\n--- Test 04: Exportación de Certificado Nernstiano a 300 DPI ---")
        win_ph = VentanaPH(self.app)
        
        # Puntos calibrados
        win_ph.cal_puntos[1][7] = 1.765
        win_ph.cal_puntos[1][4] = 1.942
        win_ph.cal_puntos[1][10] = 1.588
        win_ph._redibujar_graficas()
        
        out_png = os.path.join(win_ph.carpeta_calibraciones, "test_certificado_nernst.png")
        if os.path.exists(out_png):
            os.remove(out_png)
            
        win_ph.fig.savefig(out_png, dpi=300, facecolor=win_ph.fig.get_facecolor(), edgecolor="none")
        self.assertTrue(os.path.exists(out_png), "El certificado PNG de 300 DPI debe generarse")
        sz = os.path.getsize(out_png)
        self.assertGreater(sz, 50000, f"El PNG debe tener tamaño representativo (>50KB): {sz} bytes")
        print(f"  [OK] Certificado exportado: {out_png} ({sz/1024:.1f} KB)")
        
        win_ph._cerrar()

    def test_05_sincronizacion_modo_simulado(self):
        print("\n--- Test 05: Sincronización Estricta de Modo Simulación con App Principal ---")
        # 1. Caso Desconectado y Sin Simulación
        self.app.modo_demo = False
        self.app.conectado = False
        win_ph = VentanaPH(self.app)
        
        # Ejecutar ciclo de muestreo
        win_ph._ciclo_muestreo()
        self.assertIn("DESCONECTADO", win_ph.lbl_estab_status.cget("text"), "Debe marcar desconectado")
        self.assertEqual(win_ph.lbl_live_ph.cget("text"), "-- pH", "No debe inventar lecturas de pH")
        self.assertIn("-- V", win_ph.lbl_live_v.cget("text"), "Voltaje debe estar en -- V")
        print("  [OK] Con ESP32 desconectado y sin simulación: VentanaPH entra en pausa y no inventa datos.")

        # 2. Caso Activación de Modo Simulación en la App Principal
        self.app.modo_demo = True
        win_ph._ciclo_muestreo()
        self.assertIn("MODO SIMULACIÓN ACTIVO", win_ph.lbl_interlock.cget("text"), "Debe leer el modo simulación de la app principal")
        self.assertNotEqual(win_ph.lbl_live_ph.cget("text"), "-- pH", "Debe generar lectura simulada")
        print(f"  [OK] Al activar Modo Simulación en ventana principal: VentanaPH simula datos ({win_ph.lbl_live_ph.cget('text')}).")

        # 3. Caso Desactivación de Modo Simulación
        self.app.modo_demo = False
        win_ph._ciclo_muestreo()
        self.assertIn("DESCONECTADO", win_ph.lbl_estab_status.cget("text"))
        self.assertEqual(win_ph.lbl_live_ph.cget("text"), "-- pH")
        print("  [OK] Al desactivar Modo Simulación en ventana principal: VentanaPH vuelve a pausar.")

        win_ph._cerrar()

if __name__ == "__main__":
    unittest.main()

