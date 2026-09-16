#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de grabación de datos en tiempo real, gestión de CSVs y carpetas de ensayo.
"""

import os
import sys
import time
import csv
import threading
import subprocess
from datetime import datetime
import tkinter as tk
from tkinter import messagebox


class GrabacionMixin:

    def toggle_grabacion(self):
        if not self.grabando:
            self.iniciar_grabacion()
        else:
            self.detener_grabacion()


    def iniciar_grabacion(self):
        self.ip_grabacion = self.entry_ip.get().strip() if hasattr(self, 'entry_ip') else "192.168.4.1"
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        p_num = self.placa_activa["num"] if self.placa_activa else 1
        r_name = str(self.placa_activa["ronda"]).replace(" ", "_") if self.placa_activa else "Manual"

        # Crear carpeta dedicada estructurada por ensayo
        self.carpeta_ensayo_actual = os.path.join(self.carpeta_experimentos, f"Ensayo_P{p_num:02d}_{r_name}_{timestamp_str}")
        self.carpeta_graficas_actual = os.path.join(self.carpeta_ensayo_actual, "graficas")
        os.makedirs(self.carpeta_graficas_actual, exist_ok=True)

        self.archivo_csv = os.path.join(self.carpeta_ensayo_actual, "telemetria_completa.csv")
        self.archivo_csv_errores = os.path.join(self.carpeta_ensayo_actual, "metricas_control_errores.csv")
        self.archivo_csv_tiempos_muertos = os.path.join(self.carpeta_ensayo_actual, "registro_tiempos_muertos.csv")
        self.archivo_csv_eventos = os.path.join(self.carpeta_ensayo_actual, "registro_eventos_fallos.csv")
        self.ultimo_csv_generado = self.archivo_csv
        self.historia_eventos_fallos = []

        # Crear archivo resumen técnico de la receta
        resumen_txt_path = os.path.join(self.carpeta_ensayo_actual, "resumen_receta.txt")
        try:
            with open(resumen_txt_path, "w", encoding="utf-8") as f_res:
                p = self.placa_activa or {"num": 1, "ronda": "Ronda 1", "ph": 2, "temp_zin": 25, "tiem_zin_s": 120, "pulsado": 0}
                f_res.write("========================================================================\n")
                f_res.write(f"FICHA TÉCNICA DE RECETA ISA-88 — ENSAYO PLACA #{p.get('num', 1):02d}\n")
                f_res.write("========================================================================\n")
                f_res.write(f"Fecha y Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f_res.write(f"Ronda / Bloque: {p.get('ronda')}\n")
                f_res.write(f"pH de Referencia Inicial: {p.get('ph')}\n")
                f_res.write(f"Etapa 1 - Limpieza: 240s @ 85°C (0.00 A)\n")
                f_res.write(f"Etapa 2 - Decapado: {p.get('matizado_s', 120)}s @ 85°C (0.00 A)\n")
                f_res.write(f"Etapa 3 - Zincado: {p.get('tiem_zin_s', 120)}s @ {p.get('temp_zin', 25)}°C | 1.50 A ({'Pulsado 10Hz 20%' if p.get('pulsado')==1 else 'DC'})\n")
                f_res.write(f"Etapa 4 - Niquelado Watts: {p.get('tiem_niq_s', 600)}s (10 min) @ 30°C | 1.13 A DC (pH ref ~5.5)\n")
                f_res.write("========================================================================\n")
        except Exception:
            pass

        try:
            # 1. CSV Principal de Telemetría (Compatible v3.1 / v3.5 / RTOS 1.3 con shunts, PI y ETS)
            self.csv_file_handle = open(self.archivo_csv, mode="w", newline="", encoding="utf-8")
            self.csv_writer = csv.writer(self.csv_file_handle)

            headers_tel = [
                "Timestamp_ISO", "Tiempo_Relativo_s",
                "Placa_ID", "Ronda", "Etapa_Num", "Etapa_Nombre", "Etapa_Tiempo_s", "Etapa_Duracion_s",
                "Corriente_Target_A", "Modo_Corriente", "Temp_SP_Target_C",
                # Canal Térmico y TRIAC 1 (Limpieza - 450W)
                "T1_Limpieza_Temp_C", "T1_Limpieza_SP_C", "T1_Limpieza_Activo",
                "T1_TRIAC_Potencia_Pct", "T1_TRIAC_Alpha_Deg", "T1_TRIAC_Delay_us", "T1_TRIAC_Watts_W",
                # Canal Térmico y TRIAC 2 (Decapado - 450W)
                "T2_Decapado_Temp_C", "T2_Decapado_SP_C", "T2_Decapado_Activo",
                "T2_TRIAC_Potencia_Pct", "T2_TRIAC_Alpha_Deg", "T2_TRIAC_Delay_us", "T2_TRIAC_Watts_W",
                # Canal Térmico y TRIAC 3 (Celda Hull - 18W)
                "T3_CeldaHull_Temp_C", "T3_CeldaHull_SP_C", "T3_CeldaHull_Activo",
                "T3_TRIAC_Potencia_Pct", "T3_TRIAC_Alpha_Deg", "T3_TRIAC_Delay_us", "T3_TRIAC_Watts_W",
                # Canal Térmico y TRIAC 4 (Niquelado - 450W)
                "T4_Niquelado_Temp_C", "T4_Niquelado_SP_C", "T4_Niquelado_Activo",
                "T4_TRIAC_Potencia_Pct", "T4_TRIAC_Alpha_Deg", "T4_TRIAC_Delay_us", "T4_TRIAC_Watts_W",
                # Módulo pH Dual
                "pH_Tina1", "pH_Tina2", "pH_Modulo_Activo",
                "pH_Modo_Cal_T1", "pH_Modo_Cal_T2",
                "pH_Slope_Pct_T1", "pH_Slope_Pct_T2", "pH_Interlock_Activo",
                # Fuente de Corriente Galvánica Lazo Cerrado RTOS 1.3
                "Fuente_Activa", "Fuente_Modo_Pulsado",
                "Fuente_Corriente_Consigna_A", "Fuente_Corriente_Real_A",
                "Fuente_Corriente_Shunt1_A", "Fuente_Corriente_Shunt2_A",
                "Fuente_Voltaje_Shunt1_V", "Fuente_Voltaje_Shunt2_V",
                "Fuente_Factor_Gm", "Fuente_Compensacion_Activa", "Fuente_Rele_VDD",
                "Fuente_Amplitud_DAC", "Fuente_Frecuencia_Hz", "Fuente_DutyCycle_Pct",
                "Fuente_PI_Estado", "Fuente_Salud_Celda",
                # Ley de Faraday, Culombimetría y Balance Térmico
                "Carga_Acumulada_Coulombs", "Masa_Teorica_Faraday_mg", "Energia_Termica_Wh",
                # Condiciones Ambientales
                "Ambiente_Temp_C", "Ambiente_Humedad_Pct", "Ambiente_Presion_hPa"
            ]
            self.csv_writer.writerow(headers_tel)
            self.csv_file_handle.flush()

            # 2. CSV Especializado de Métricas de Error y Control
            self.csv_err_handle = open(self.archivo_csv_errores, mode="w", newline="", encoding="utf-8")
            self.csv_err_writer = csv.writer(self.csv_err_handle)
            headers_err = [
                "Timestamp_ISO", "Tiempo_Relativo_s",
                "Etapa_Num", "Etapa_Nombre",
                "Error_T1_C", "Error_T2_C", "Error_T3_C", "Error_T4_C", "Error_Corriente_A",
                "IAE_T1", "IAE_T2", "IAE_T3", "IAE_T4", "IAE_Corriente",
                "Esfuerzo_u1_Pct", "Esfuerzo_u2_Pct", "Esfuerzo_u3_Pct", "Esfuerzo_u4_Pct"
            ]
            self.csv_err_writer.writerow(headers_err)
            self.csv_err_handle.flush()

            # 3. CSV Especializado de Registro de Tiempos Muertos entre Fases ISA-88
            self.csv_tm_handle = open(self.archivo_csv_tiempos_muertos, mode="w", newline="", encoding="utf-8")
            self.csv_tm_writer = csv.writer(self.csv_tm_handle)
            headers_tm = [
                "Transicion_ID", "Etapa_Origen_Num", "Etapa_Origen_Nombre",
                "Etapa_Destino_Num", "Etapa_Destino_Nombre",
                "Timestamp_Inicio", "Timestamp_Fin", "Tiempo_Muerto_s",
                "Temp_Ambiente_C", "Humedad_Pct", "Presion_hPa", "Evaporacion_Estimada_g_h"
            ]
            self.csv_tm_writer.writerow(headers_tm)
            self.csv_tm_handle.flush()

            # 4. CSV Especializado de Registro de Eventos, Anomalías y Accidentes de Sensores
            self.csv_eventos_handle = open(self.archivo_csv_eventos, mode="w", newline="", encoding="utf-8")
            self.csv_eventos_writer = csv.writer(self.csv_eventos_handle)
            headers_ev = [
                "Timestamp_ISO", "Tiempo_Relativo_s", "Etapa_Nombre",
                "Tipo_Evento", "Subsistema_Sensor", "Severidad",
                "Valor_Detectado", "Descripcion_Tecnica"
            ]
            self.csv_eventos_writer.writerow(headers_ev)
            self.csv_eventos_handle.flush()

        except Exception as e:
            messagebox.showerror("Error de Archivo", f"No se pudieron crear los archivos CSV del ensayo:\n{e}")
            return

        # Inicializar estados de detección de anomalías y accidentes de sensores
        self._prev_temps = [None, None, None, None]
        self._falla_sonda_activa = [False, False, False, False]
        self._salto_termico_activo = [False, False, False, False]
        self._sobretemp_activa = [False, False, False, False]
        self._falla_ph_activa = [False, False]
        self._prev_phs = [None, None]
        self._desbalance_shunt_activo = False
        self._salud_celda_activa = False
        self._enlace_wifi_ok = True
        self._accidente_simulado_pendiente = None

        self.grabando = True
        self.tiempo_inicio = time.time()
        self.muestras_count = 0

        # Reiniciar acumuladores IAE, Culombimetría y Energía Térmica
        self.iae_t1 = 0.0
        self.iae_t2 = 0.0
        self.iae_t3 = 0.0
        self.iae_t4 = 0.0
        self.iae_curr = 0.0
        self.coulombs_total = 0.0
        self.coulombs_etapa = 0.0
        self.coulombs_zn = 0.0
        self.coulombs_ni = 0.0
        self.energia_termica_wh = 0.0

        # Gestión de transiciones y tiempos muertos
        self.ultima_etapa_idx = getattr(self, 'etapa_activa_idx', 0)
        self.transicion_id_count = 0
        self.tiempo_fin_etapa_previa = time.time()
        self.historia_tiempos_muertos = []

        # Limpiar buffers
        self.buf_t.clear()
        self.buf_t1.clear()
        self.buf_t1_sp.clear()
        self.buf_t2.clear()
        self.buf_t2_sp.clear()
        self.buf_t3.clear()
        self.buf_t3_sp.clear()
        self.buf_t4.clear()
        self.buf_t4_sp.clear()
        self.buf_u1.clear()
        self.buf_u2.clear()
        self.buf_u3.clear()
        self.buf_u4.clear()
        self.buf_curr.clear()
        self.buf_curr_avg.clear()
        self.buf_ph1.clear()
        self.buf_ph2.clear()
        self.buf_ph_on.clear()
        self.buf_amb_t = []
        self.buf_amb_h = []
        self.buf_amb_p = []
        self.buf_ets_wave = [0.0] * 16

        self.btn_rec.config(text="⏹ DETENER GRABACIÓN", bg="#dc2626", activebackground="#ef4444")
        self.lbl_csv_info.config(text=f"💾 Guardando en: experimentos/{os.path.basename(self.carpeta_ensayo_actual)}/", fg="#34d399")
        if hasattr(self, 'lbl_incidentes'):
            self.lbl_incidentes.config(text="⚠️ Incidentes: 0", fg="#22c55e")

        self.hilo_muestreo = threading.Thread(target=self._bucle_adquisicion, daemon=True)
        self.hilo_muestreo.start()


    def registrar_evento(self, tipo_evento, sensor, severidad, valor_detectado, descripcion, t_rel=None, nom_etapa=None):
        """Registra un evento anómalo o de recuperación en el CSV de fallos y memoria."""
        if not self.grabando and not getattr(self, 'csv_eventos_handle', None):
            return

        t_iso = datetime.now().isoformat(timespec="seconds")
        if t_rel is None:
            t_rel = round(time.time() - self.tiempo_inicio, 1) if self.tiempo_inicio else 0.0

        if nom_etapa is None:
            if hasattr(self, '_obtener_datos_etapa_actual'):
                nom_etapa, _, _, _, _ = self._obtener_datos_etapa_actual()
            else:
                nom_etapa = "Proceso General"

        fila = [
            t_iso, t_rel, nom_etapa,
            tipo_evento, sensor, severidad,
            str(valor_detectado), descripcion
        ]

        if getattr(self, 'csv_eventos_handle', None) and not self.csv_eventos_handle.closed:
            try:
                self.csv_eventos_writer.writerow(fila)
                self.csv_eventos_handle.flush()
            except Exception:
                pass

        evento_dict = {
            "iso": t_iso,
            "t_rel": t_rel,
            "etapa": nom_etapa,
            "tipo": tipo_evento,
            "sensor": sensor,
            "severidad": severidad,
            "valor": str(valor_detectado),
            "desc": descripcion
        }
        if hasattr(self, 'historia_eventos_fallos'):
            self.historia_eventos_fallos.append(evento_dict)

        # Actualizar indicador numérico de incidentes en el SCADA
        if hasattr(self, 'lbl_incidentes'):
            n_anom = sum(1 for ev in self.historia_eventos_fallos if ev.get("severidad") in ("CRITICO", "ADVERTENCIA"))
            color = "#ef4444" if n_anom > 0 else "#22c55e"
            try:
                self.root.after(0, lambda: self.lbl_incidentes.config(
                    text=f"⚠️ Incidentes: {n_anom}",
                    fg=color
                ))
            except Exception:
                pass

        # Notificar a la ventana de diagnóstico si está abierta en pantalla
        if getattr(self, 'win_diag', None) and hasattr(self.win_diag, 'agregar_evento_gui'):
            try:
                self.root.after(0, lambda: self.win_diag.agregar_evento_gui(evento_dict))
            except Exception:
                pass


    def detener_grabacion(self):
        self.grabando = False
        if getattr(self, 'csv_file_handle', None):
            try:
                self.csv_file_handle.close()
            except Exception:
                pass
            self.csv_file_handle = None

        if getattr(self, 'csv_err_handle', None):
            try:
                self.csv_err_handle.close()
            except Exception:
                pass
            self.csv_err_handle = None

        if getattr(self, 'csv_tm_handle', None):
            try:
                self.csv_tm_handle.close()
            except Exception:
                pass
            self.csv_tm_handle = None

        if getattr(self, 'csv_eventos_handle', None):
            try:
                self.csv_eventos_handle.close()
            except Exception:
                pass
            self.csv_eventos_handle = None

        # Consolidar Auditoría Técnica de Incidentes en resumen_receta.txt
        resumen_txt_path = os.path.join(self.carpeta_ensayo_actual, "resumen_receta.txt") if self.carpeta_ensayo_actual else None
        if resumen_txt_path and os.path.exists(resumen_txt_path):
            try:
                with open(resumen_txt_path, "a", encoding="utf-8") as f_res:
                    f_res.write("\n========================================================================\n")
                    f_res.write("AUDITORÍA DE INCIDENCIAS Y ACCIDENTES DE SENSORES EN PROCESO\n")
                    f_res.write("========================================================================\n")
                    eventos = getattr(self, 'historia_eventos_fallos', [])
                    if not eventos:
                        f_res.write("Estado Global: ✅ 100% NOMINAL — 0 incidencias registradas durante el ensayo.\n")
                        f_res.write("No se detectaron saltos térmicos EMI, desconexiones de sondas MAX6675,\n")
                        f_res.write("desbalances en etapas shunt VCSS ni pérdidas de enlace con ESP32.\n")
                    else:
                        n_tot = len(eventos)
                        n_crit = sum(1 for e in eventos if e.get("severidad") == "CRITICO")
                        n_adv = sum(1 for e in eventos if e.get("severidad") == "ADVERTENCIA")
                        f_res.write(f"Total de Registros: {n_tot} (Críticos: {n_crit} | Advertencias: {n_adv} | Recuperaciones: {n_tot - n_crit - n_adv})\n")
                        f_res.write(f"{'Tiempo':<10} | {'Etapa':<22} | {'Severidad':<12} | {'Sensor':<22} | {'Tipo Evento':<24} | {'Detalle'}\n")
                        f_res.write("-" * 125 + "\n")
                        for ev in eventos:
                            t_fmt = f"{ev.get('t_rel', 0.0):.1f} s"
                            f_res.write(f"{t_fmt:<10} | {ev.get('etapa', '')[:22]:<22} | {ev.get('severidad', ''):<12} | {ev.get('sensor', '')[:22]:<22} | {ev.get('tipo', '')[:24]:<24} | {ev.get('desc', '')}\n")
                    f_res.write("========================================================================\n")
            except Exception:
                pass

        self.btn_rec.config(text="▶ INICIAR GRABACIÓN", bg="#059669", activebackground="#10b981")
        self.lbl_csv_info.config(text=f"✅ Ensayo cerrado en: {os.path.basename(self.carpeta_ensayo_actual)}/ ({self.muestras_count} muestras)", fg="#fbbf24")


    def abrir_carpeta_datos(self):
        destino = self.carpeta_ensayo_actual if (self.carpeta_ensayo_actual and os.path.exists(self.carpeta_ensayo_actual)) else self.carpeta_experimentos
        if sys.platform == "win32":
            os.startfile(destino)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", destino])
        else:
            subprocess.Popen(["xdg-open", destino])

