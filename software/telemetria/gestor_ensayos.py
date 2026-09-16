#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de gestión de ensayos (ISA-88), matriz de 32 placas, etapas, setpoints y alarmas.
"""

import os
import time
import threading
import pandas as pd
import requests
import tkinter as tk
from tkinter import messagebox, filedialog

try:
    from utilidades.alarma import reproducir_alarma_sonora
except ImportError:
    try:
        from telemetria.utilidades.alarma import reproducir_alarma_sonora
    except ImportError:
        def reproducir_alarma_sonora(tipo="test"):
            pass


class GestorEnsayosMixin:

    def _buscar_excel_defecto(self):
        directorio_actual = os.path.dirname(os.path.abspath(__file__))
        candidatos = [
            os.path.join(directorio_actual, "datos", "matriz_experimentos.xlsx"),
            os.path.join(directorio_actual, "datos", "Hoja de resultados matriz de experimentos.xlsx"),
            os.path.join(directorio_actual, "Hoja de resultados matriz de experimentos.xlsx"),
            os.path.join(directorio_actual, "..", "telemetria", "datos", "matriz_experimentos.xlsx"),
            os.path.join(directorio_actual, "..", "telemetria", "Hoja de resultados matriz de experimentos.xlsx"),
            os.path.join(directorio_actual, "..", "Hoja de resultados matriz de experimentos.xlsx"),
        ]
        for c in candidatos:
            if os.path.exists(c):
                return os.path.abspath(c)
        return ""


    def _cargar_datos_excel(self, ruta_custom=None):
        ruta = ruta_custom or self.excel_path
        self.lista_placas = []
        if not ruta or not os.path.exists(ruta):
            for i in range(1, 33):
                self.lista_placas.append({
                    "num": i,
                    "ronda": "Ronda 1" if i <= 16 else "Ronda 2",
                    "limpieza_s": 240,
                    "matizado_s": 120,
                    "ph": 2 if i % 2 == 1 else 4,
                    "temp_zin": 25 if i <= 8 or (17 <= i <= 24) else 40,
                    "tiem_zin_s": 120 if i % 4 in (1, 2) else 300,
                    "pulsado": 1 if i % 2 == 0 else 0,
                    "tiem_niq_s": 600,
                    "tag_filtro": f"pH {2 if i % 2 == 1 else 4} — {25 if i <= 8 or (17 <= i <= 24) else 40}°C"
                })
            return

        try:
            wb = pd.ExcelFile(ruta)
            for sheet in wb.sheet_names:
                df = pd.read_excel(ruta, sheet_name=sheet)
                for _, row in df.iterrows():
                    p_val = row.get("Placas")
                    if pd.notna(p_val):
                        placa_num = int(p_val)
                        limp = row.get("Limpieza")
                        limp_s = 240 if (pd.isna(limp) or limp == "") else int(float(limp))
                        mat = row.get("Tiempo de mat.")
                        mat_s = 120 if (pd.isna(mat) or mat == "") else int(float(mat))
                        ph = row.get("pH")
                        ph_val = 2 if (pd.isna(ph) or ph == "") else int(float(ph))
                        temp_z = row.get("Temperatura de zin.")
                        temp_z_val = 25 if (pd.isna(temp_z) or temp_z == "") else int(float(temp_z))
                        tiem_z = row.get("Tiempo de zin.")
                        tiem_z_val = 120 if (pd.isna(tiem_z) or tiem_z == "") else int(float(tiem_z))
                        puls = row.get("Corriente Pul.")
                        puls_val = 0 if (pd.isna(puls) or puls == "") else int(float(puls))
                        tiem_niq = row.get("Tiem. Niquelado")
                        tiem_niq_val = 600 if (pd.isna(tiem_niq) or tiem_niq == "") else int(float(tiem_niq))

                        tag = f"pH {ph_val} — {temp_z_val}°C"

                        self.lista_placas.append({
                            "num": placa_num,
                            "ronda": sheet,
                            "limpieza_s": limp_s,
                            "matizado_s": mat_s,
                            "ph": ph_val,
                            "temp_zin": temp_z_val,
                            "tiem_zin_s": tiem_z_val,
                            "pulsado": puls_val,
                            "tiem_niq_s": tiem_niq_val,
                            "tag_filtro": tag
                        })
            self.excel_path = ruta
        except Exception as e:
            print(f"[AVISO] Error al leer Excel ({e}). Se usarán valores predeterminados.")


    def _aplicar_filtro(self, tag):
        self.filtro_actual = tag
        todos_btns = [
            (self.btn_f_all, "TODOS"),
            (self.btn_f_p2_25, "pH 2 — 25°C"),
            (self.btn_f_p2_40, "pH 2 — 40°C"),
            (self.btn_f_p4_25, "pH 4 — 25°C"),
            (self.btn_f_p4_40, "pH 4 — 40°C"),
        ]
        for btn, b_tag in todos_btns:
            btn.config(bg="#2563eb" if b_tag == tag else "#1e293b")
        self._actualizar_lista_combo()


    def _actualizar_lista_combo(self):
        filtradas = []
        for p in self.lista_placas:
            if self.filtro_actual == "TODOS" or p["tag_filtro"] == self.filtro_actual:
                pul_txt = "Zin: Pul 1.5A" if p["pulsado"] == 1 else "Zin: DC 1.5A"
                label = f"Placa {p['num']:02d} — {p['ronda']} | {p['tag_filtro']} | Zin: {p['tiem_zin_s']}s | {pul_txt}"
                filtradas.append((label, p))

        self.mapa_combo = {item[0]: item[1] for item in filtradas}
        self.combo_placas["values"] = [item[0] for item in filtradas]
        if filtradas:
            self.combo_placas.current(0)
            self._on_placa_seleccionada(None)
        else:
            self.combo_placas.set("Sin placas en este filtro")


    def _on_placa_seleccionada(self, event):
        sel_text = self.combo_placas.get()
        if sel_text not in self.mapa_combo:
            return
        self.placa_activa = self.mapa_combo[sel_text]
        p = self.placa_activa

        self.lbl_badge_ronda.config(text=f"🏷️ {p['ronda']} — Placa #{p['num']:02d}")
        self.lbl_badge_cond.config(text=f"🧪 pH Ref: {p['ph']}  |  🌡️ Zincado: {p['temp_zin']} °C ({p['tiem_zin_s']}s)")

        if p["pulsado"] == 1:
            self.lbl_badge_zin.config(text="⚡ Zincado: PULSADO 1.50 A @ 10Hz (20% Duty)", fg="#f472b6")
        else:
            self.lbl_badge_zin.config(text="⚡ Zincado: DC CONTINUO 1.50 A", fg="#34d399")

        self.lbl_badge_niq.config(text="⚡ Níquel: DC CONTINUO 1.13 A (600s / 10 min)", fg="#a78bfa")

        self.lbl_e1.config(text=f"Limpieza (T1): {p['limpieza_s']}s @ 85°C | 0.00A")
        self.lbl_e2.config(text=f"Decapado (T2): {p['matizado_s']}s @ 85°C | 0.00A")
        zin_modo = "Pul 1.5A" if p["pulsado"] == 1 else "DC 1.5A"
        self.lbl_e3.config(text=f"Zincado (T3): {p['tiem_zin_s']}s @ {p['temp_zin']}°C | {zin_modo}")
        self.lbl_e4.config(text=f"Niquelado (T4): {p['tiem_niq_s']}s @ 30°C | 1.13A DC (pH 5.5)")

        self.etapa_activa_idx = 0
        self.etapa_corriendo = False
        self._cargar_etapa_actual()


    def _obtener_datos_etapa_actual(self):
        if not self.placa_activa:
            return "Limpieza", 240, 85.0, 0.0, "OFF"
        p = self.placa_activa
        if self.etapa_activa_idx == 0:
            return "Limpieza Electrolítica (T1)", p["limpieza_s"], 85.0, 0.0, "OFF"
        elif self.etapa_activa_idx == 1:
            return "Decapado Ácido (T2)", p["matizado_s"], 85.0, 0.0, "OFF"
        elif self.etapa_activa_idx == 2:
            modo = "PULSADO" if p["pulsado"] == 1 else "DC"
            return "Zincado Químico / Celda (T3)", p["tiem_zin_s"], float(p["temp_zin"]), 1.50, modo
        else:
            return "Niquelado Watts (T4)", p["tiem_niq_s"], 30.0, 1.13, "DC"


    def _cargar_etapa_actual(self):
        nombre, duracion, sp_t, curr, modo = self._obtener_datos_etapa_actual()
        self.etapa_duracion_total = duracion
        self.etapa_segundos_restantes = duracion
        self.etapa_segundos_transcurridos = 0
        self.t_inicio_etapa_real = None
        self.t_acumulado_etapa = 0.0

        self.lbl_etapa_titulo.config(text=f"ETAPA {self.etapa_activa_idx + 1}/4: {nombre.upper()}")
        self._actualizar_display_reloj()
        self.btn_stage_toggle.config(text="▶ Iniciar Etapa", bg="#059669", activebackground="#10b981")
        self.lbl_aviso_etapa.config(text=f"Objetivo: SP Temp {sp_t:.0f}°C | Corriente: {curr:.2f}A ({modo})", fg="#94a3b8")

        if hasattr(self, 'btn_stage_prev'):
            self.btn_stage_prev.config(state="normal" if self.etapa_activa_idx > 0 else "disabled")

        if hasattr(self, 'lbl_hw_sync_status'):
            self.lbl_hw_sync_status.config(text=f"📡 SPs listos: {curr:.2f}A ({modo}) | T{self.etapa_activa_idx+1}:{sp_t:.0f}°C", fg="#94a3b8")

        filas = [self.lbl_e1, self.lbl_e2, self.lbl_e3, self.lbl_e4]
        for idx, f in enumerate(filas):
            if idx == self.etapa_activa_idx:
                f.config(fg="#38bdf8", font=("Segoe UI", 7, "bold"))
            elif idx < self.etapa_activa_idx:
                f.config(fg="#34d399", font=("Segoe UI", 7))
            else:
                f.config(fg="#64748b", font=("Segoe UI", 7))


    def _actualizar_display_reloj(self):
        mins = int(self.etapa_segundos_restantes // 60)
        segs = int(self.etapa_segundos_restantes % 60)
        self.lbl_timer_big.config(text=f"{mins:02d}:{segs:02d}")
        if self.etapa_duracion_total > 0:
            prog = ((self.etapa_duracion_total - self.etapa_segundos_restantes) / self.etapa_duracion_total) * 100
            if hasattr(self, 'progress_etapa'):
                self.progress_etapa["value"] = prog
            if hasattr(self, '_dibujar_progreso_canvas'):
                self._dibujar_progreso_canvas(prog)


    def toggle_etapa(self):
        if not self.etapa_corriendo:
            self.etapa_corriendo = True
            self.t_inicio_etapa_real = time.time()
            nom_etapa, _, _, _, _ = self._obtener_datos_etapa_actual()
            t_now = self.buf_t[-1] if (hasattr(self, 'buf_t') and self.buf_t) else 0.0
            if hasattr(self, 'marcadores_etapas'):
                self.marcadores_etapas.append((t_now, f"E{self.etapa_activa_idx+1}: {nom_etapa}"))

            self.btn_stage_toggle.config(text="⏸ Pausar", bg="#d97706", activebackground="#f59e0b")
            self.lbl_timer_big.config(fg="#34d399")
            self.lbl_aviso_etapa.config(text="⏳ Etapa en progreso...", fg="#34d399")
            
            # Suministro de corriente y sincronización garantizada al iniciar
            self.enviar_setpoints_esp32(feedback_usuario=False)
            
            if hasattr(self, 'sonar_beep'):
                self.sonar_beep(750, 100)
            if hasattr(self, 'show_toast'):
                self.show_toast(f"▶ {nom_etapa} iniciada", tipo="success")

            if not self.grabando:
                self.iniciar_grabacion()
        else:
            self.etapa_corriendo = False
            if getattr(self, 't_inicio_etapa_real', None) is not None:
                self.t_acumulado_etapa = getattr(self, 't_acumulado_etapa', 0.0) + (time.time() - self.t_inicio_etapa_real)
                self.t_inicio_etapa_real = None
            self.btn_stage_toggle.config(text="▶ Reanudar", bg="#059669", activebackground="#10b981")
            self.lbl_timer_big.config(fg="#fbbf24")
            self.lbl_aviso_etapa.config(text="⏸ Etapa en pausa (Fuente VCSS apagada y relé abierto).", fg="#fbbf24")
            # Corte inmediato de corriente por seguridad al pausar
            self.apagar_fuente_esp32()
            if hasattr(self, 'sonar_beep'):
                self.sonar_beep(450, 120)
            if hasattr(self, 'show_toast'):
                self.show_toast("⏸ Etapa en pausa — Relé abierto", tipo="warning")


    def avanzar_siguiente_etapa(self):
        if self.etapa_activa_idx < 3:
            # Apagar fuente de corriente incondicionalmente antes de cambiar de tina
            self.apagar_fuente_esp32()
            self.etapa_activa_idx += 1
            self.etapa_corriendo = False
            self._cargar_etapa_actual()
            nom_etapa, _, _, _, _ = self._obtener_datos_etapa_actual()
            t_now = self.buf_t[-1] if (hasattr(self, 'buf_t') and self.buf_t) else 0.0
            if hasattr(self, 'marcadores_etapas'):
                self.marcadores_etapas.append((t_now, f"E{self.etapa_activa_idx+1}: {nom_etapa}"))
            # Sincronizar setpoints térmicos y precargar DAC sin cerrar relé (run=0)
            if hasattr(self, 'var_auto_sync_hw') and self.var_auto_sync_hw.get():
                self.enviar_setpoints_esp32(feedback_usuario=False)
        else:
            self.etapa_corriendo = False
            self.apagar_fuente_esp32()
            reproducir_alarma_sonora("fin_ensayo")
            p_num = self.placa_activa.get("num", 1) if self.placa_activa else 1
            self.lbl_aviso_etapa.config(
                text=f"🏆 ¡ENSAYO FINALIZADO! Enjuague/seque la probeta y registre en '⚖️ Faraday / Balanza'.",
                fg="#34d399"
            )
            messagebox.showinfo(
                "Ensayo Finalizado",
                f"✅ ¡Ensayo de la Placa #{p_num:02d} completado con éxito!\n\n"
                f"• La fuente VCSS está apagada y la celda aislada con relé ZCS.\n"
                f"• Retire la probeta, enjuáguela con agua destilada y séquela.\n"
                f"• Cuando esté seca y pesada, ingrese los valores en '⚖️ Faraday / Balanza'."
            )


    def retroceder_etapa_anterior(self):
        if self.etapa_activa_idx > 0:
            self.apagar_fuente_esp32()
            self.etapa_activa_idx -= 1
            self.etapa_corriendo = False
            self._cargar_etapa_actual()
            if hasattr(self, 'var_auto_sync_hw') and self.var_auto_sync_hw.get():
                self.enviar_setpoints_esp32(feedback_usuario=False)


    def reiniciar_etapa_actual(self):
        self.etapa_corriendo = False
        self.apagar_fuente_esp32()
        self._cargar_etapa_actual()


    def apagar_fuente_esp32(self, feedback_usuario=False):
        """
        Envía comando HTTP al ESP32 para cortar inmediatamente la corriente (DAC=0)
        y abrir mecánicamente el contacto del relé de aislamiento (+12V VCSS).
        """
        if getattr(self, 'modo_demo', False):
            if hasattr(self, 'lbl_hw_sync_status'):
                self.lbl_hw_sync_status.config(text="🎮 Modo Demo: Fuente VCSS apagada (Relé abierto)", fg="#94a3b8")
            return

        ip = self.entry_ip.get().strip() if hasattr(self, 'entry_ip') else "192.168.4.1"

        def _cut_thread():
            try:
                if hasattr(self, 'destellar_tx'):
                    self.root.after(0, self.destellar_tx)
                base_url = f"http://{ip}"
                session = requests.Session()
                # 1. Apagar fuente en firmware (DAC a 0V, espera descarga y abre relé físico)
                session.get(f"{base_url}/act_f?run=0", timeout=1.5)
                # 2. Amplitud a 0 por seguridad redundante
                session.get(f"{base_url}/set_f?p=a&v=0", timeout=1.5)
                session.get(f"{base_url}/modo_f?v=0", timeout=1.5)

                if hasattr(self, 'lbl_hw_sync_status'):
                    self.root.after(0, lambda: self.lbl_hw_sync_status.config(
                        text="⚡ Fuente VCSS APAGADA (Relé Abierto)", fg="#38bdf8"
                    ))
                if feedback_usuario:
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Seguridad Eléctrica",
                        f"✅ Fuente VCSS apagada y relé abierto con éxito en el ESP32 ({ip})."
                    ))
            except Exception as e:
                if hasattr(self, 'lbl_hw_sync_status'):
                    self.root.after(0, lambda: self.lbl_hw_sync_status.config(
                        text=f"⚠️ Error corte fuente: {str(e)[:22]}", fg="#ef4444"
                    ))

        threading.Thread(target=_cut_thread, daemon=True).start()


    def enviar_setpoints_esp32(self, feedback_usuario=False):
        """
        Envía los setpoints de temperatura y corriente de la etapa y placa activas al ESP32.
        - Etapa 1 (Limpieza - T1): SP T1=85°C, Fuente OFF (0.00A)
        - Etapa 2 (Decapado - T2): SP T2=85°C, Fuente OFF (0.00A)
        - Etapa 3 (Zincado - T3): SP T3=(25°C o 40°C), Fuente ON a 1.50A SOLO cuando etapa_corriendo es True
        - Etapa 4 (Niquelado - T4): SP T4=30°C, Fuente ON a 1.13A DC SOLO cuando etapa_corriendo es True

        INTERLOCK DE SEGURIDAD ELÉCTRICA:
        Al cambiar de etapa (dar Siguiente o Anterior), la fuente se precarga pero el relé
        PERMANECE ABIERTO (run=0). El suministro eléctrico y el conteo SOLO se energizan
        cuando el operador presiona explícitamente '▶ Iniciar Etapa'.
        """
        nombre, dur, sp_t, curr_sp, modo_corr = self._obtener_datos_etapa_actual()
        p = self.placa_activa or {"num": 1, "temp_zin": 25, "pulsado": 0}

        # Comprobar si la etapa está en ejecución real para permitir energización
        debe_energizar = bool(getattr(self, 'etapa_corriendo', False) and self.etapa_activa_idx in (2, 3))
        run_val = 1 if debe_energizar else 0
        desc_rele = "RELÉ CERRADO (CORRIENTE ON)" if run_val == 1 else "RELÉ ABIERTO (EN REPOSO)"

        if self.modo_demo:
            txt_demo = f"🎮 Modo Demo: SPs listos ({curr_sp:.2f}A {modo_corr} [{desc_rele}] | T{self.etapa_activa_idx+1}:{sp_t:.0f}°C)"
            if hasattr(self, 'lbl_hw_sync_status'):
                self.lbl_hw_sync_status.config(text=txt_demo, fg="#fbbf24")
            if feedback_usuario:
                messagebox.showinfo("Modo Demo", f"En Modo Demo los setpoints se aplican virtualmente:\n\n• Etapa {self.etapa_activa_idx+1}: {nombre}\n• Corriente: {curr_sp:.2f} A ({modo_corr})\n• Estado de la Fuente: {desc_rele}\n• Temperatura T{self.etapa_activa_idx+1}: {sp_t:.1f} °C")
            return

        ip = self.entry_ip.get().strip() if hasattr(self, 'entry_ip') else "192.168.4.1"

        def _sync_thread():
            try:
                if hasattr(self, 'lbl_hw_sync_status'):
                    self.root.after(0, lambda: self.lbl_hw_sync_status.config(text="⏳ Enviando parámetros a ESP32...", fg="#38bdf8"))
                if hasattr(self, 'destellar_tx'):
                    self.root.after(0, self.destellar_tx)
                base_url = f"http://{ip}"
                session = requests.Session()

                # 1. Configuración de la Fuente de Corriente (VCSS)
                if self.etapa_activa_idx in (0, 1):
                    # Etapas 1 y 2: Fuente apagada con ZCS y amplitud a 0
                    session.get(f"{base_url}/act_f?run=0", timeout=1.5)
                    session.get(f"{base_url}/set_f?p=a&v=0", timeout=1.5)
                    session.get(f"{base_url}/modo_f?v=0", timeout=1.5)
                elif self.etapa_activa_idx == 2:
                    # Etapa 3 (Zincado): 1.50 A (DAC = 870 @ 7.06A fondo de escala / 3.53V)
                    dac_val = int((1.50 / 7.06) * 4095.0)
                    es_pulsado = 1 if p.get("pulsado", 0) == 1 else 0
                    session.get(f"{base_url}/modo_f?v={es_pulsado}", timeout=1.5)
                    session.get(f"{base_url}/set_f?p=a&v={dac_val}", timeout=1.5)
                    if es_pulsado:
                        session.get(f"{base_url}/set_f?p=f&v=10", timeout=1.5)  # 10 Hz
                        session.get(f"{base_url}/set_f?p=d&v=20", timeout=1.5)  # 20% duty
                    # SEGURIDAD CRÍTICA: solo suministrar corriente si el operador presionó 'Iniciar Etapa'
                    session.get(f"{base_url}/act_f?run={run_val}", timeout=1.5)
                elif self.etapa_activa_idx == 3:
                    # Etapa 4 (Niquelado Watts): DC 1.13 A continuo (DAC = 655 @ 7.06A fondo de escala / 3.53V)
                    dac_val = int((1.13 / 7.06) * 4095.0)
                    session.get(f"{base_url}/modo_f?v=0", timeout=1.5)
                    session.get(f"{base_url}/set_f?p=a&v={dac_val}", timeout=1.5)
                    # SEGURIDAD CRÍTICA: solo suministrar corriente si el operador presionó 'Iniciar Etapa'
                    session.get(f"{base_url}/act_f?run={run_val}", timeout=1.5)

                # 2. Configuración del Setpoint Térmico del canal de la etapa actual
                canal_id = self.etapa_activa_idx
                session.get(f"{base_url}/set_t?id={canal_id}&v={sp_t:.1f}", timeout=1.5)

                if run_val == 1:
                    txt_ok = f"⚡ ENERGIZADO: {curr_sp:.2f}A ({modo_corr}) | T{canal_id+1}:{sp_t:.0f}°C"
                    color_ok = "#34d399"
                else:
                    txt_ok = f"🟢 ESP32 LISTO (Relé en Reposo): {curr_sp:.2f}A ({modo_corr}) | T{canal_id+1}:{sp_t:.0f}°C"
                    color_ok = "#38bdf8"

                if hasattr(self, 'lbl_hw_sync_status'):
                    self.root.after(0, lambda: self.lbl_hw_sync_status.config(text=txt_ok, fg=color_ok))
                if feedback_usuario:
                    msg = (
                        f"✅ Parámetros cargados en el ESP32 ({ip}):\n\n"
                        f"• Etapa {self.etapa_activa_idx + 1}/4: {nombre}\n"
                        f"• Consigna Corriente: {curr_sp:.2f} A ({modo_corr})\n"
                        f"• Estado Relé VCSS: {desc_rele}\n"
                        f"• Consigna Térmica T{canal_id + 1}: {sp_t:.1f} °C\n\n"
                        f"ℹ️ Por seguridad, la corriente solo circulará al presionar 'Iniciar Etapa'."
                    )
                    self.root.after(0, lambda: messagebox.showinfo("Sincronización Exitosa", msg))
            except Exception as e:
                txt_err = f"🔴 Error ESP32: {str(e)[:28]}"
                if hasattr(self, 'lbl_hw_sync_status'):
                    self.root.after(0, lambda: self.lbl_hw_sync_status.config(text=txt_err, fg="#ef4444"))
                if feedback_usuario:
                    self.root.after(0, lambda: messagebox.showwarning(
                        "Error de Comunicación",
                        f"No se pudieron enviar los parámetros al ESP32 en http://{ip}\n\nDetalle: {e}\n\nVerifique la red Wi-Fi o active el 'Modo Demo'."
                    ))

        threading.Thread(target=_sync_thread, daemon=True).start()


    def probar_alarma(self):
        reproducir_alarma_sonora("test")


    def _iniciar_timer_etapa_loop(self):
        def _loop():
            if self.etapa_corriendo and getattr(self, 't_inicio_etapa_real', None) is not None:
                t_transcurrido = (time.time() - self.t_inicio_etapa_real) + getattr(self, 't_acumulado_etapa', 0.0)
                self.etapa_segundos_transcurridos = int(t_transcurrido)
                seg_rest = max(0, int(self.etapa_duracion_total - t_transcurrido))
                self.etapa_segundos_restantes = seg_rest
                self._actualizar_display_reloj()

                if seg_rest > 0:
                    # Parpadeo de alerta cuando quedan <= 30 segundos (B3)
                    if seg_rest <= 30:
                        blink_color = "#ef4444" if (seg_rest % 2 == 1) else "#fbbf24"
                        self.lbl_timer_big.config(fg=blink_color)
                    else:
                        self.lbl_timer_big.config(fg="#34d399")
                else:
                    self.etapa_corriendo = False
                    self.t_inicio_etapa_real = None
                    self.t_acumulado_etapa = float(self.etapa_duracion_total)
                    self.btn_stage_toggle.config(text="▶ Iniciar", bg="#059669")
                    self.lbl_timer_big.config(fg="#fbbf24")
                    nom_etapa, _, _, _, _ = self._obtener_datos_etapa_actual()

                    # CORTE DE SEGURIDAD AUTOMÁTICO INMEDIATO:
                    # En cuanto suena la alarma (00:00), apagar DAC a 0V y abrir relé
                    if self.etapa_activa_idx in (2, 3):
                        self.apagar_fuente_esp32()

                    if self.etapa_activa_idx == 3:
                        # Finalización de la Etapa 4: Niquelado Watts (Fin de la Receta Bicapa)
                        reproducir_alarma_sonora("fin_ensayo")
                        self.lbl_aviso_etapa.config(
                            text=f"🏆 ¡BICAPA FINALIZADA! Enjuague, seque la probeta y registre el Peso Final en '⚖️ Faraday'.",
                            fg="#34d399"
                        )
                    elif self.etapa_activa_idx == 2:
                        reproducir_alarma_sonora("fin_etapa")
                        self.lbl_aviso_etapa.config(
                            text=f"🔔 ¡ZINCADO FINALIZADO! Enjuague rápido con agua DI (NO secar ni pesar). Pase a Tina 4.",
                            fg="#fbbf24"
                        )
                    else:
                        reproducir_alarma_sonora("fin_etapa")
                        self.lbl_aviso_etapa.config(
                            text=f"🔔 ¡{nom_etapa} FINALIZADA! Cambie de tina y presione 'Siguiente'.",
                            fg="#fbbf24"
                        )

            # Refresco determinista a 5 Hz (200 ms) sin doble delay recursivo
            self.root.after(200, _loop)

        self.root.after(200, _loop)


    def cargar_archivo_excel(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar Matriz Experimental en Excel",
            filetypes=[("Archivos Excel", "*.xlsx *.xls")]
        )
        if ruta and os.path.exists(ruta):
            self._cargar_datos_excel(ruta)
            self.lbl_xl_info.config(text=f"📁 {len(self.lista_placas)} placas ({os.path.basename(ruta)[:18]}...)")
            self._actualizar_lista_combo()
            messagebox.showinfo("Excel Cargado", f"Se cargaron correctamente {len(self.lista_placas)} placas desde:\n{ruta}")

