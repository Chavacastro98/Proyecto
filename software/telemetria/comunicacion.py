#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de comunicación HTTP con ESP32, ping, bucle de adquisición y modo demo.
"""

import math
import time
import random
import threading
from datetime import datetime
import requests
import tkinter as tk
from tkinter import messagebox

from telemetria.utilidades.calculos import calcular_disparo_triac


class ComunicacionMixin:

    def _on_toggle_demo(self):
        self.modo_demo = self.var_demo.get()
        if self.modo_demo:
            self.lbl_status.config(text="🎮 MODO DEMO", fg="#fbbf24")
            self.lbl_csv_info.config(text="Modo Simulación activo: Generando datos sintéticos realistas en telemetria/experimentos/.", fg="#fbbf24")
        else:
            self.demo_forzar_corriente = False
            self.btn_demo_curr.config(bg="#1e293b", fg="#94a3b8")
            self._probar_conexion_silenciosa()


    def _toggle_forzar_corriente_demo(self):
        if not self.modo_demo:
            self.var_demo.set(True)
            self._on_toggle_demo()
        self.demo_forzar_corriente = not self.demo_forzar_corriente
        if self.demo_forzar_corriente:
            self.btn_demo_curr.config(bg="#22c55e", fg="#0f172a", text="⚡ Corriente ON (1.5A)")
        else:
            self.btn_demo_curr.config(bg="#1e293b", fg="#94a3b8", text="⚡ Forzar Corriente")


    def _probar_conexion_silenciosa(self):
        if self.modo_demo:
            return
        ip = self.entry_ip.get().strip() if hasattr(self, 'entry_ip') else "192.168.4.1"
        def _ping():
            try:
                r = requests.get(f"http://{ip}/data_env", timeout=1.5)
                if r.status_code == 200:
                    self.conectado = True
                    try:
                        self.root.after(0, lambda: self.lbl_status.config(text="🟢 EN LÍNEA", fg="#34d399"))
                    except Exception:
                        pass
                    return
            except Exception:
                pass
            self.conectado = False
            try:
                self.root.after(0, lambda: self.lbl_status.config(text="🔴 DESCONECTADO", fg="#ef4444"))
            except Exception:
                pass

        threading.Thread(target=_ping, daemon=True).start()


    def probar_conexion_manual(self):
        if self.modo_demo:
            messagebox.showinfo("Modo Demo", "El Modo Simulación está activo. Desmárcalo para conectar con hardware real.")
            return
        ip = self.entry_ip.get().strip()
        try:
            r = requests.get(f"http://{ip}/data_env", timeout=2.0)
            if r.status_code == 200:
                self.conectado = True
                self.lbl_status.config(text="🟢 EN LÍNEA", fg="#34d399")
                messagebox.showinfo("Conexión Exitosa", f"Conectado correctamente al ESP32 ({ip}).")
                return
        except Exception:
            self.conectado = False
            self.lbl_status.config(text="🔴 DESCONECTADO", fg="#ef4444")
            messagebox.showwarning(
                "Sin Conexión",
                f"No se pudo conectar a http://{ip}\n\n1. Verifica Wi-Fi 'Uli' (Pass: 12345678).\n2. Si deseas probar sin hardware, activa '🎮 Modo Demo'."
            )


    def simular_accidente_sensor(self, tipo_accidente):
        """Inyecta un accidente o perturbación simulada para probar el sistema de auditoría."""
        self._accidente_simulado_pendiente = tipo_accidente
        self._accidente_duracion = 4 if tipo_accidente != "salto_t2" else 1
        if hasattr(self, 'lbl_status'):
            self.lbl_status.config(text=f"⚠️ TEST: {tipo_accidente.upper()}", fg="#ef4444")


    def _generar_datos_simulados(self, t_rel):
        sp1, sp2 = 85.0, 85.0
        p = self.placa_activa or {"temp_zin": 25, "ph": 2, "pulsado": 0}
        sp3 = float(p.get("temp_zin", 25))
        sp4 = 30.0

        tau = 80.0
        factor = 1.0 - math.exp(-t_rel / tau)
        t1 = 24.0 + (sp1 - 24.0) * factor + random.uniform(-0.15, 0.15)
        t2 = 24.0 + (sp2 - 24.0) * factor + random.uniform(-0.15, 0.15)
        t3 = 24.0 + (sp3 - 24.0) * factor + random.uniform(-0.15, 0.15)
        t4 = 24.0 + (sp4 - 24.0) * factor + random.uniform(-0.15, 0.15)

        # Inyección de accidentes simulados para validación técnica
        acc = getattr(self, '_accidente_simulado_pendiente', None)
        if acc == "salto_t2":
            # Salto térmico abrupto por ruido EMI o falso contacto (+16.5°C instantáneos)
            t2 += 16.5
            self._accidente_simulado_pendiente = None
        elif acc == "desconexion_t1":
            # Termopar MAX6675 abierto / desconectado (lectura en 0.0°C)
            t1 = 0.0
            dur = getattr(self, '_accidente_duracion', 4) - 1
            if dur <= 0:
                self._accidente_simulado_pendiente = None
                self._accidente_duracion = 4
            else:
                self._accidente_duracion = dur
        elif acc == "sobretemp_t4":
            # Sobrecalentamiento crítico de seguridad (>68°C en Níquel)
            t4 = 72.8
            dur = getattr(self, '_accidente_duracion', 4) - 1
            if dur <= 0:
                self._accidente_simulado_pendiente = None
                self._accidente_duracion = 4
            else:
                self._accidente_duracion = dur

        # Simular potencia TRIAC %
        u1_sim = int(max(0, min(100, (sp1 - t1) * 15.0 + 20.0)))
        u2_sim = int(max(0, min(100, (sp2 - t2) * 15.0 + 20.0)))
        u3_sim = int(max(0, min(100, (sp3 - t3) * 15.0 + 20.0)))
        u4_sim = int(max(0, min(100, (sp4 - t4) * 15.0 + 20.0)))

        d_t = [
            {"t": round(t1, 1), "sp": sp1, "p": u1_sim, "run": 1},
            {"t": round(t2, 1), "sp": sp2, "p": u2_sim, "run": 1},
            {"t": round(t3, 1), "sp": sp3, "p": u3_sim, "run": 1},
            {"t": round(t4, 1), "sp": sp4, "p": u4_sim, "run": 1}
        ]

        ph_target = float(p.get("ph", 2))
        ph1_val = round(ph_target + random.uniform(-0.04, 0.04), 2)
        if acc == "ph_anomalo":
            ph1_val = 14.75  # Fuera de rango electroquímico
            dur = getattr(self, '_accidente_duracion', 4) - 1
            if dur <= 0:
                self._accidente_simulado_pendiente = None
                self._accidente_duracion = 4
            else:
                self._accidente_duracion = dur

        d_ph = {
            "p1": ph1_val,
            "p2": round(4.20 + random.uniform(-0.03, 0.03), 2),
            "on": 1,
            "m1": 2,
            "m2": 2,
            "sl1": 98.4,
            "sl2": 97.8,
            "il": 0
        }

        if (self.etapa_corriendo and self.etapa_activa_idx in (2, 3)) or self.demo_forzar_corriente:
            curr_target = 1.50 if (self.etapa_activa_idx == 2 or self.demo_forzar_corriente) else 1.13
            modo_pul = p.get("pulsado", 0) if self.etapa_activa_idx == 2 else 0
            i_real_sim = round(curr_target + random.uniform(-0.02, 0.02), 3)
            i1_sim = round(i_real_sim * 0.502, 3)
            i2_sim = round(i_real_sim * 0.498, 3)
            salud_sim = 0

            if acc == "desbalance_vcss":
                i1_sim = round(i_real_sim * 0.85, 3)
                i2_sim = round(i_real_sim * 0.15, 3)
                dur = getattr(self, '_accidente_duracion', 4) - 1
                if dur <= 0:
                    self._accidente_simulado_pendiente = None
                    self._accidente_duracion = 4
                else:
                    self._accidente_duracion = dur
            elif acc == "saturacion_celda":
                salud_sim = 1
                dur = getattr(self, '_accidente_duracion', 4) - 1
                if dur <= 0:
                    self._accidente_simulado_pendiente = None
                    self._accidente_duracion = 4
                else:
                    self._accidente_duracion = dur

            # Simular onda ETS de 16 puntos
            wave_sim = []
            num_h = int(round(16 * (0.20 if modo_pul == 1 else 1.0)))
            for pt in range(16):
                if pt < num_h:
                    wave_sim.append(round(i_real_sim * (0.98 + 0.04 * math.sin(pt)), 3))
                else:
                    wave_sim.append(0.01)

            d_f = {
                "act": 1,
                "modo": modo_pul,
                "amps": curr_target,
                "i_real": i_real_sim,
                "i1": i1_sim,
                "i2": i2_sim,
                "vs1": round(i1_sim * 0.15, 3),
                "vs2": round(i2_sim * 0.15, 3),
                "gm": 1.005,
                "comp": 1,
                "rele": 1,
                "amp": int(curr_target * 500),
                "sp": int(curr_target * 500),
                "freq": 10 if modo_pul == 1 else 0,
                "duty": 20 if modo_pul == 1 else 0,
                "pi_st": 0 if modo_pul == 1 else 3,
                "salud": salud_sim,
                "wave": wave_sim
            }
        else:
            d_f = {
                "act": 0,
                "modo": 0,
                "amps": 0.0,
                "i_real": 0.0,
                "i1": 0.0,
                "i2": 0.0,
                "vs1": 0.0,
                "vs2": 0.0,
                "gm": 1.000,
                "comp": 0,
                "rele": 0,
                "amp": 0,
                "sp": 0,
                "freq": 0,
                "duty": 0,
                "pi_st": 0,
                "salud": 0,
                "wave": [0.0] * 16
            }

        if acc == "caida_wifi":
            self.conectado = False
            dur = getattr(self, '_accidente_duracion', 3) - 1
            if dur <= 0:
                self._accidente_simulado_pendiente = None
                self._accidente_duracion = 3
                self.conectado = True
            else:
                self._accidente_duracion = dur

        d_env = {
            "t": round(23.5 + random.uniform(-0.2, 0.2), 1),
            "h": round(58.0 + random.uniform(-0.5, 0.5), 1),
            "p": 1013.2
        }
        return d_t, d_ph, d_f, d_env


    def _bucle_adquisicion(self):
        session = requests.Session()
        session.headers.update({"User-Agent": "TelemetriaGUI/3.5"})
        ip = getattr(self, 'ip_grabacion', '192.168.4.1')
        base_url = f"http://{ip}"

        # Caché para resiliencia ante jitter Wi-Fi
        ultimo_d_t = [
            {"t": 24.0, "sp": 0.0, "p": 0, "run": 0},
            {"t": 24.0, "sp": 0.0, "p": 0, "run": 0},
            {"t": 24.0, "sp": 0.0, "p": 0, "run": 0},
            {"t": 24.0, "sp": 0.0, "p": 0, "run": 0}
        ]
        ultimo_d_ph = {"p1": 7.0, "p2": 7.0, "on": 0, "m1": 0, "m2": 0, "sl1": 100.0, "sl2": 100.0, "il": 0}
        ultimo_d_f = {"act": 0, "modo": 0, "amps": 0.0, "i_real": 0.0, "i1": 0.0, "i2": 0.0, "vs1": 0.0, "vs2": 0.0, "gm": 1.0, "comp": 0, "rele": 0, "amp": 0, "freq": 0, "duty": 0}
        ultimo_d_env = {"t": "24.0", "h": "50", "p": "1013.2"}

        # Inicialización de estados de detección de fallos si no existen
        if not hasattr(self, '_prev_temps') or self._prev_temps is None:
            self._prev_temps = [None, None, None, None]
        if not hasattr(self, '_falla_sonda_activa'):
            self._falla_sonda_activa = [False, False, False, False]
        if not hasattr(self, '_salto_termico_activo'):
            self._salto_termico_activo = [False, False, False, False]
        if not hasattr(self, '_sobretemp_activa'):
            self._sobretemp_activa = [False, False, False, False]
        if not hasattr(self, '_falla_ph_activa'):
            self._falla_ph_activa = [False, False]
        if not hasattr(self, '_prev_phs'):
            self._prev_phs = [None, None]
        if not hasattr(self, '_desbalance_shunt_activo'):
            self._desbalance_shunt_activo = False
        if not hasattr(self, '_salud_celda_activa'):
            self._salud_celda_activa = False
        if not hasattr(self, '_enlace_wifi_ok'):
            self._enlace_wifi_ok = True

        t_prev_ciclo = None

        while self.grabando:
            t_ciclo_inicio = time.time()
            if t_prev_ciclo is not None:
                dt = max(0.1, min(3.0, t_ciclo_inicio - t_prev_ciclo))
            else:
                dt = 1.0
            t_prev_ciclo = t_ciclo_inicio

            t_rel = round(t_ciclo_inicio - self.tiempo_inicio, 1)
            t_iso = datetime.now().isoformat(timespec="seconds")

            d_t, d_ph, d_f, d_env = None, None, None, None

            if self.modo_demo:
                d_t, d_ph, d_f, d_env = self._generar_datos_simulados(t_rel)
                self.conectado = True
                ultimo_d_t, ultimo_d_ph, ultimo_d_f, ultimo_d_env = d_t, d_ph, d_f, d_env
            else:
                any_success = False
                # 1. RUTA RÁPIDA OPTIMIZADA: Endpoint unificado /data_all (RTOS 1.0)
                try:
                    r_all = session.get(f"{base_url}/data_all", timeout=0.8)
                    if r_all.status_code == 200:
                        d_all = r_all.json()
                        d_t = d_all.get("t")
                        d_ph = d_all.get("ph")
                        d_f = d_all.get("f")
                        d_env = d_all.get("env")
                        ultimo_d_t, ultimo_d_ph, ultimo_d_f, ultimo_d_env = d_t, d_ph, d_f, d_env
                        any_success = True
                except Exception:
                    pass

                # 2. FALLBACK RETROCOMPATIBLE (Si el firmware no soporta /data_all)
                if not any_success:
                    try:
                        r_t = session.get(f"{base_url}/data_t", timeout=0.8)
                        if r_t.status_code == 200:
                            d_t = r_t.json()
                            ultimo_d_t = d_t
                            any_success = True
                    except Exception:
                        d_t = ultimo_d_t

                    try:
                        r_ph = session.get(f"{base_url}/get_ph_dual", timeout=0.8)
                        if r_ph.status_code == 200:
                            d_ph = r_ph.json()
                            ultimo_d_ph = d_ph
                            any_success = True
                    except Exception:
                        d_ph = ultimo_d_ph

                    try:
                        r_f = session.get(f"{base_url}/data_f", timeout=0.8)
                        if r_f.status_code == 200:
                            d_f = r_f.json()
                            ultimo_d_f = d_f
                            any_success = True
                    except Exception:
                        d_f = ultimo_d_f

                    try:
                        r_env = session.get(f"{base_url}/data_env", timeout=0.8)
                        if r_env.status_code == 200:
                            d_env = r_env.json()
                            ultimo_d_env = d_env
                            any_success = True
                    except Exception:
                        d_env = ultimo_d_env

                self.conectado = any_success
                d_t = d_t or ultimo_d_t
                d_ph = d_ph or ultimo_d_ph
                d_f = d_f or ultimo_d_f
                d_env = d_env or ultimo_d_env

                self.ultimo_d_t = d_t
                self.ultimo_d_ph = d_ph
                self.ultimo_d_f = d_f
                self.ultimo_d_env = d_env

            if d_t and d_ph and d_f and d_env:
                nom_etapa, dur_etapa, sp_target, curr_target, modo_corr = self._obtener_datos_etapa_actual()
                placa_id = self.placa_activa["num"] if self.placa_activa else ""
                ronda_id = self.placa_activa["ronda"] if self.placa_activa else ""

                # Auditoría y detección de anomalías / accidentes de sensores en tiempo real
                self._detectar_incidencias_sensores(t_rel, d_t, d_ph, d_f, d_env, nom_etapa)

                # Extracción robusta de campos v3.1 / v3.5 / RTOS 1.3
                i_consigna = float(d_f.get("amps", 0.0))
                i_medida_real = float(d_f.get("i_real", i_consigna))
                i_shunt1 = float(d_f.get("i1", i_medida_real * 0.5))
                i_shunt2 = float(d_f.get("i2", i_medida_real * 0.5))
                v_shunt1 = float(d_f.get("vs1", 0.0))
                v_shunt2 = float(d_f.get("vs2", 0.0))
                factor_gm = float(d_f.get("gm", 1.0))
                comp_activa = int(d_f.get("comp", 0))
                rele_vdd = int(d_f.get("rele", 0))
                pi_st = int(d_f.get("pi_st", 0))
                salud_celda = int(d_f.get("salud", 0))
                wave_data = d_f.get("wave", [])
                if wave_data and len(wave_data) == 16:
                    self.buf_ets_wave = [float(x) for x in wave_data]

                # Histórico ambiental
                try:
                    amb_t_f = float(d_env.get("t", 24.0))
                    amb_h_f = float(d_env.get("h", 50.0))
                    amb_p_f = float(d_env.get("p", 1013.2))
                    if hasattr(self, 'buf_amb_t'):
                        self.buf_amb_t.append(amb_t_f)
                        self.buf_amb_h.append(amb_h_f)
                        self.buf_amb_p.append(amb_p_f)
                except Exception:
                    amb_t_f, amb_h_f, amb_p_f = 24.0, 50.0, 1013.2

                # Detección de transición de fase ISA-88 y registro de tiempos muertos
                cur_etapa = self.etapa_activa_idx
                if cur_etapa != getattr(self, 'ultima_etapa_idx', cur_etapa):
                    t_fin_trans = time.time()
                    t_muerto = max(0.0, round(t_fin_trans - getattr(self, 'tiempo_fin_etapa_previa', t_fin_trans), 2))
                    self.transicion_id_count = getattr(self, 'transicion_id_count', 0) + 1

                    nom_etapas = ["Limpieza Química", "Decapado Ácido", "Zincado Celda Hull", "Niquelado Químico Watts"]
                    orig_nom = nom_etapas[self.ultima_etapa_idx] if 0 <= self.ultima_etapa_idx < len(nom_etapas) else f"Etapa {self.ultima_etapa_idx+1}"
                    dest_nom = nom_etapas[cur_etapa] if 0 <= cur_etapa < len(nom_etapas) else f"Etapa {cur_etapa+1}"
                    evap_est = round(max(0.0, (100.0 - amb_h_f) * 0.12 * (amb_t_f / 25.0)), 2)

                    fila_tm = [
                        self.transicion_id_count,
                        self.ultima_etapa_idx + 1, orig_nom,
                        cur_etapa + 1, dest_nom,
                        datetime.fromtimestamp(getattr(self, 'tiempo_fin_etapa_previa', t_fin_trans)).isoformat(timespec="seconds"),
                        datetime.fromtimestamp(t_fin_trans).isoformat(timespec="seconds"),
                        t_muerto,
                        amb_t_f, amb_h_f, amb_p_f, evap_est
                    ]
                    if getattr(self, 'csv_tm_handle', None) and not self.csv_tm_handle.closed:
                        try:
                            self.csv_tm_writer.writerow(fila_tm)
                            self.csv_tm_handle.flush()
                        except Exception:
                            pass
                    if hasattr(self, 'historia_tiempos_muertos'):
                        self.historia_tiempos_muertos.append(fila_tm)
                    self.ultima_etapa_idx = cur_etapa
                    self.tiempo_fin_etapa_previa = t_fin_trans

                # Calcular Errores e IAE
                e1 = float(d_t[0]["sp"]) - float(d_t[0]["t"])
                e2 = float(d_t[1]["sp"]) - float(d_t[1]["t"])
                e3 = float(d_t[2]["sp"]) - float(d_t[2]["t"])
                e4 = float(d_t[3]["sp"]) - float(d_t[3]["t"])
                e_i = curr_target - i_medida_real

                self.iae_t1 += abs(e1) * dt
                self.iae_t2 += abs(e2) * dt
                self.iae_t3 += abs(e3) * dt
                self.iae_t4 += abs(e4) * dt
                self.iae_curr += abs(e_i) * dt

                # Obtener potencia de disparo del ESP32 (o estimarla)
                u1 = float(d_t[0].get("p", min(100.0, max(0.0, e1 * 15.0 + 25.0)) if d_t[0]["run"] == 1 else 0.0))
                u2 = float(d_t[1].get("p", min(100.0, max(0.0, e2 * 15.0 + 25.0)) if d_t[1]["run"] == 1 else 0.0))
                u3 = float(d_t[2].get("p", min(100.0, max(0.0, e3 * 15.0 + 25.0)) if d_t[2]["run"] == 1 else 0.0))
                u4 = float(d_t[3].get("p", min(100.0, max(0.0, e4 * 15.0 + 25.0)) if d_t[3]["run"] == 1 else 0.0))

                self.ultimo_u1 = u1
                self.ultimo_u2 = u2
                self.ultimo_u3 = u3
                self.ultimo_u4 = u4
                self.ultimo_amps = i_medida_real

                # Calcular variables de conmutación de fase y potencia de los TRIACs
                p1_pct, a1_deg, d1_us, w1 = calcular_disparo_triac(u1, 450.0)
                p2_pct, a2_deg, d2_us, w2 = calcular_disparo_triac(u2, 450.0)
                p3_pct, a3_deg, d3_us, w3 = calcular_disparo_triac(u3, 18.0)
                p4_pct, a4_deg, d4_us, w4 = calcular_disparo_triac(u4, 450.0)

                # Acumulación de energía eléctrica/térmica (Wh) con dt real
                self.energia_termica_wh = getattr(self, 'energia_termica_wh', 0.0) + (((w1 + w2 + w3 + w4) * dt) / 3600.0)

                # Integración Culombimétrica Faradaica Q = ∫ I dt con dt real
                if i_medida_real > 0.005:
                    self.coulombs_total += i_medida_real * dt
                    self.coulombs_etapa += i_medida_real * dt
                    if self.etapa_activa_idx == 2:
                        self.coulombs_zn = getattr(self, 'coulombs_zn', 0.0) + (i_medida_real * dt)
                    elif self.etapa_activa_idx == 3:
                        self.coulombs_ni = getattr(self, 'coulombs_ni', 0.0) + (i_medida_real * dt)

                m_teo_zn = getattr(self, 'coulombs_zn', 0.0) * 0.33880
                m_teo_ni = getattr(self, 'coulombs_ni', 0.0) * 0.30414
                m_teo_instantanea = m_teo_zn + m_teo_ni

                # Fila de Telemetría Completa RTOS 1.3
                fila_tel = [
                    t_iso, t_rel,
                    placa_id, ronda_id, self.etapa_activa_idx + 1, nom_etapa,
                    self.etapa_segundos_transcurridos, dur_etapa,
                    curr_target, modo_corr, sp_target,
                    # T1 y TRIAC 1
                    d_t[0]["t"], d_t[0]["sp"], d_t[0]["run"],
                    p1_pct, a1_deg, d1_us, w1,
                    # T2 y TRIAC 2
                    d_t[1]["t"], d_t[1]["sp"], d_t[1]["run"],
                    p2_pct, a2_deg, d2_us, w2,
                    # T3 y TRIAC 3
                    d_t[2]["t"], d_t[2]["sp"], d_t[2]["run"],
                    p3_pct, a3_deg, d3_us, w3,
                    # T4 y TRIAC 4
                    d_t[3]["t"], d_t[3]["sp"], d_t[3]["run"],
                    p4_pct, a4_deg, d4_us, w4,
                    # pH
                    d_ph["p1"], d_ph["p2"], d_ph["on"],
                    d_ph["m1"], d_ph["m2"],
                    d_ph["sl1"], d_ph["sl2"], d_ph["il"],
                    # Fuente
                    d_f["act"], d_f["modo"],
                    i_consigna, i_medida_real,
                    i_shunt1, i_shunt2,
                    v_shunt1, v_shunt2,
                    factor_gm, comp_activa, rele_vdd,
                    d_f.get("amp", 0), d_f.get("freq", 0), d_f.get("duty", 0),
                    pi_st, salud_celda,
                    # Ley de Faraday y Culombimetría
                    round(self.coulombs_total, 2), round(m_teo_instantanea, 2), round(self.energia_termica_wh, 3),
                    # Ambiente
                    d_env.get("t", "--"), d_env.get("h", "--"), d_env.get("p", "--")
                ]

                # Fila de Métricas de Error
                fila_err = [
                    t_iso, t_rel,
                    self.etapa_activa_idx + 1, nom_etapa,
                    round(e1, 2), round(e2, 2), round(e3, 2), round(e4, 2), round(e_i, 3),
                    round(self.iae_t1, 1), round(self.iae_t2, 1), round(self.iae_t3, 1), round(self.iae_t4, 1), round(self.iae_curr, 2),
                    round(self.ultimo_u1, 1), round(self.ultimo_u2, 1), round(self.ultimo_u3, 1), round(self.ultimo_u4, 1)
                ]

                # Escribir a CSVs
                if self.csv_file_handle and not self.csv_file_handle.closed:
                    try:
                        self.csv_writer.writerow(fila_tel)
                        self.csv_file_handle.flush()
                        self.muestras_count += 1
                    except Exception:
                        pass

                if self.csv_err_handle and not self.csv_err_handle.closed:
                    try:
                        self.csv_err_writer.writerow(fila_err)
                        self.csv_err_handle.flush()
                    except Exception:
                        pass

                try:
                    self.root.after(0, self._actualizar_gui_datos, t_rel, d_t, d_ph, d_f, d_env)
                except Exception:
                    pass

            t_espera = 1.0 - (time.time() - t_ciclo_inicio)
            if t_espera > 0:
                time.sleep(t_espera)


    def _detectar_incidencias_sensores(self, t_rel, d_t, d_ph, d_f, d_env, nom_etapa):
        """Audita en tiempo real a 1 Hz las lecturas para detectar saltos EMI, desconexiones y anomalías."""
        if not hasattr(self, '_prev_temps') or self._prev_temps is None:
            self._prev_temps = [None, None, None, None]

        # 1. Termopares SPI MAX6675 (T1..T4)
        tinas_cfg = [
            ("Tina 1 Limpieza", 92.0),
            ("Tina 2 Decapado", 92.0),
            ("Tina 3 Celda Hull", 35.0),
            ("Tina 4 Niquelado Watts", 68.0)
        ]

        for i in range(4):
            if i >= len(d_t):
                continue
            try:
                t_val = float(d_t[i].get("t", 0.0))
            except (ValueError, TypeError):
                continue

            nombre_tina, temp_limite = tinas_cfg[i]
            prev_t = self._prev_temps[i]

            # A) Sonda desconectada / circuito abierto (MAX6675 entrega 0.0°C o fuera de rango)
            es_desconexion = (t_val <= 0.0 or t_val >= 135.0)
            recupero_de_desconexion = False
            if es_desconexion:
                if not self._falla_sonda_activa[i]:
                    self.registrar_evento(
                        tipo_evento="SONDA_DESCONECTADA",
                        sensor=f"MAX6675 {nombre_tina}",
                        severidad="CRITICO",
                        valor_detectado=f"{t_val:.1f} °C",
                        descripcion=f"Sonda de temperatura desconectada o circuito abierto en {nombre_tina}.",
                        t_rel=t_rel,
                        nom_etapa=nom_etapa
                    )
                    self._falla_sonda_activa[i] = True
            else:
                if self._falla_sonda_activa[i] and (5.0 <= t_val <= 125.0):
                    self.registrar_evento(
                        tipo_evento="RECUPERACION_SENSOR",
                        sensor=f"MAX6675 {nombre_tina}",
                        severidad="INFO",
                        valor_detectado=f"{t_val:.1f} °C",
                        descripcion=f"Sonda {nombre_tina} reconectada. Lectura nominal restablecida.",
                        t_rel=t_rel,
                        nom_etapa=nom_etapa
                    )
                    self._falla_sonda_activa[i] = False
                    recupero_de_desconexion = True
                    prev_t = t_val

            # B) Salto térmico abrupto / Ruido EMI / Transitorio inductivo
            # La inercia térmica de los líquidos no permite variaciones >= 8°C en 1 segundo
            if prev_t is not None and not self._falla_sonda_activa[i] and not es_desconexion and not recupero_de_desconexion:
                delta_t = t_val - prev_t
                if abs(delta_t) >= 8.0:
                    if not self._salto_termico_activo[i]:
                        sev = "CRITICO" if abs(delta_t) >= 15.0 else "ADVERTENCIA"
                        self.registrar_evento(
                            tipo_evento="SALTO_TERMICO_EMI",
                            sensor=f"MAX6675 {nombre_tina}",
                            severidad=sev,
                            valor_detectado=f"ΔT = {delta_t:+.1f} °C/s ({t_val:.1f} °C)",
                            descripcion=f"Salto térmico abrupto en {nombre_tina}. Perturbación incompatible con inercia de baño (posible ruido EMI o falso contacto).",
                            t_rel=t_rel,
                            nom_etapa=nom_etapa
                        )
                        self._salto_termico_activo[i] = True
                else:
                    if self._salto_termico_activo[i] and abs(delta_t) <= 1.5:
                        self.registrar_evento(
                            tipo_evento="RECUPERACION_SENSOR",
                            sensor=f"MAX6675 {nombre_tina}",
                            severidad="INFO",
                            valor_detectado=f"{t_val:.1f} °C",
                            descripcion=f"Lectura de {nombre_tina} normalizada y estable tras transitorio.",
                            t_rel=t_rel,
                            nom_etapa=nom_etapa
                        )
                        self._salto_termico_activo[i] = False

            # C) Alarma de Sobretemperatura de Seguridad Crítica
            if not self._falla_sonda_activa[i] and not es_desconexion:
                if t_val > temp_limite:
                    if not self._sobretemp_activa[i]:
                        self.registrar_evento(
                            tipo_evento="SOBRETEMPERATURA",
                            sensor=f"Calentador {nombre_tina}",
                            severidad="CRITICO",
                            valor_detectado=f"{t_val:.1f} °C > {temp_limite:.1f} °C",
                            descripcion=f"Límite de seguridad térmica superado en {nombre_tina}. Riesgo de degradación electroquímica o evaporación.",
                            t_rel=t_rel,
                            nom_etapa=nom_etapa
                        )
                        self._sobretemp_activa[i] = True
                else:
                    if self._sobretemp_activa[i] and t_val <= (temp_limite - 2.0):
                        self.registrar_evento(
                            tipo_evento="RECUPERACION_SENSOR",
                            sensor=f"Calentador {nombre_tina}",
                            severidad="INFO",
                            valor_detectado=f"{t_val:.1f} °C",
                            descripcion=f"Temperatura de {nombre_tina} retornó a zona de operación segura.",
                            t_rel=t_rel,
                            nom_etapa=nom_etapa
                        )
                        self._sobretemp_activa[i] = False

            self._prev_temps[i] = t_val

        # 2. Fuente Galvánica de Corriente Lazo Cerrado VCSS
        if d_f:
            act = int(d_f.get("act", 0))
            i_real = float(d_f.get("i_real", 0.0))
            i1 = float(d_f.get("i1", 0.0))
            i2 = float(d_f.get("i2", 0.0))
            salud = int(d_f.get("salud", 0))

            if act == 1 and i_real > 0.20:
                diff_i = abs(i1 - i2)
                if diff_i > 0.12:
                    if not self._desbalance_shunt_activo:
                        self.registrar_evento(
                            tipo_evento="DESBALANCE_SHUNTS",
                            sensor="Fuente VCSS Shunts 1/2",
                            severidad="ADVERTENCIA",
                            valor_detectado=f"I1={i1:.3f}A, I2={i2:.3f}A (Δ={diff_i:.3f}A)",
                            descripcion="Desbalance de corriente entre ramas MOSFET/Shunt de la fuente galvánica (> 0.12 A).",
                            t_rel=t_rel,
                            nom_etapa=nom_etapa
                        )
                        self._desbalance_shunt_activo = True
                else:
                    if self._desbalance_shunt_activo and diff_i <= 0.05:
                        self.registrar_evento(
                            tipo_evento="RECUPERACION_SENSOR",
                            sensor="Fuente VCSS Shunts 1/2",
                            severidad="INFO",
                            valor_detectado=f"Δ={diff_i:.3f}A",
                            descripcion="Balance de corriente restaurado entre ramas de la etapa de potencia.",
                            t_rel=t_rel,
                            nom_etapa=nom_etapa
                        )
                        self._desbalance_shunt_activo = False

                if salud == 1:
                    if not self._salud_celda_activa:
                        self.registrar_evento(
                            tipo_evento="SATURACION_CELDA",
                            sensor="Celda Galvánica / Lazo VCSS",
                            severidad="CRITICO",
                            valor_detectado="Salud = 1 (Tensión saturada en VDD)",
                            descripcion="Tensión de celda alcanzó el límite de saturación. Ánodo desconectado, pasivado o celda abierta.",
                            t_rel=t_rel,
                            nom_etapa=nom_etapa
                        )
                        self._salud_celda_activa = True
                else:
                    if self._salud_celda_activa and salud == 0:
                        self.registrar_evento(
                            tipo_evento="RECUPERACION_SENSOR",
                            sensor="Celda Galvánica / Lazo VCSS",
                            severidad="INFO",
                            valor_detectado="Salud = 0 (Lazo regulado)",
                            descripcion="Celda galvánica restablecida y en regulación activa.",
                            t_rel=t_rel,
                            nom_etapa=nom_etapa
                        )
                        self._salud_celda_activa = False

        # 3. Módulo de pH (ADS1115)
        if d_ph and int(d_ph.get("on", 0)) == 1:
            for idx_ph, key_ph in enumerate(["p1", "p2"]):
                try:
                    ph_val = float(d_ph.get(key_ph, 7.0))
                except (ValueError, TypeError):
                    continue

                es_ph_invalido = (ph_val < 0.5 or ph_val > 14.0)
                if es_ph_invalido:
                    if not self._falla_ph_activa[idx_ph]:
                        self.registrar_evento(
                            tipo_evento="PH_FUERA_RANGO",
                            sensor=f"Electrodo pH Tina {idx_ph+1}",
                            severidad="ADVERTENCIA",
                            valor_detectado=f"{ph_val:.2f} pH",
                            descripcion=f"Lectura de pH fuera de escala electroquímica válida (0.5 - 14.0 pH) en Tina {idx_ph+1}.",
                            t_rel=t_rel,
                            nom_etapa=nom_etapa
                        )
                        self._falla_ph_activa[idx_ph] = True
                else:
                    if self._falla_ph_activa[idx_ph] and (0.8 <= ph_val <= 13.5):
                        self.registrar_evento(
                            tipo_evento="RECUPERACION_SENSOR",
                            sensor=f"Electrodo pH Tina {idx_ph+1}",
                            severidad="INFO",
                            valor_detectado=f"{ph_val:.2f} pH",
                            descripcion=f"Lectura de electrodo pH Tina {idx_ph+1} normalizada.",
                            t_rel=t_rel,
                            nom_etapa=nom_etapa
                        )
                        self._falla_ph_activa[idx_ph] = False

        # 4. Enlace Wi-Fi ESP32
        if not self.modo_demo:
            if not self.conectado and self._enlace_wifi_ok:
                self.registrar_evento(
                    tipo_evento="CAIDA_COMUNICACION",
                    sensor="Enlace Wi-Fi ESP32",
                    severidad="ADVERTENCIA",
                    valor_detectado="HTTP Timeout / Desconectado",
                    descripcion="Pérdida de enlace de comunicación o timeout con el microcontrolador ESP32.",
                    t_rel=t_rel,
                    nom_etapa=nom_etapa
                )
                self._enlace_wifi_ok = False
            elif self.conectado and not self._enlace_wifi_ok:
                self.registrar_evento(
                    tipo_evento="RECUPERACION_ENLACE",
                    sensor="Enlace Wi-Fi ESP32",
                    severidad="INFO",
                    valor_detectado="HTTP 200 OK",
                    descripcion="Enlace Wi-Fi con ESP32 restablecido correctamente.",
                    t_rel=t_rel,
                    nom_etapa=nom_etapa
                )
                self._enlace_wifi_ok = True

