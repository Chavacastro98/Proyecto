"""
============================================================================
SIMULACIÓN DE RESPUESTA TÉRMICA — Control PI del Sistema de Galvanoplastia
============================================================================
Genera gráficas de estabilización de temperatura para las 4 tinas usando
los parámetros reales del firmware v3.1 (Kp, Ki) y el modelo térmico
del script MATLAB Control_termico.m.

Ejecutar: python sim_termica.py
Requiere: pip install matplotlib numpy
"""
import matplotlib.pyplot as plt
import numpy as np

# ── Parámetros termodinámicos (de Control_termico.m) ──
T_AMB_DEF = 25.0
RHO_DEF = 1.0        # kg/L
CP_DEF = 4184.3      # J/(kg·K)
H_EFF_DEF = 65.0     # W/(m²·K)

TINAS_DEFAULT = [
    {"nombre": "Tina 1: Desengrase Alcalino (450W)",
     "vol": 1.0, "A_s": 0.0470, "P_max": 450, "retardo": 6,
     "T_set": 90, "Kp": 62.65, "Ki": 0.0897},
    {"nombre": "Tina 2: Decapado Ácido (450W)",
     "vol": 1.0, "A_s": 0.0470, "P_max": 450, "retardo": 6,
     "T_set": 90, "Kp": 62.65, "Ki": 0.0897},
    {"nombre": "Tina 3: Celda Hull / Zincado (18W)",
     "vol": 0.267, "A_s": 0.0210, "P_max": 18, "retardo": 3,
     "T_set": 30, "Kp": 16.71, "Ki": 0.0239},
    {"nombre": "Tina 4: Niquelado (450W)",
     "vol": 1.0, "A_s": 0.0470, "P_max": 450, "retardo": 6,
     "T_set": 30, "Kp": 62.51, "Ki": 0.0895},
]


def simular_tina(tina, t_total=1200, dt=1.0, t_amb=T_AMB_DEF, rho=RHO_DEF, cp=CP_DEF, h_eff=H_EFF_DEF):
    """
    Simula la respuesta térmica de una tina con control PI y modelo de retardo térmico.
    Retorna: (t, T, power)
    """
    n_steps = int(t_total / dt)
    ramp_period = 0.2
    ramp_increment = 1.0
    ramp_steps_per_pi = int(dt / ramp_period)

    m = tina["vol"] * rho
    c_th = m * cp
    r_th = 1.0 / (h_eff * tina["A_s"])

    t = np.zeros(n_steps)
    T = np.zeros(n_steps)
    T[0] = t_amb
    power = np.zeros(n_steps)
    integral = 0.0
    lim_pot = 0.0

    for k in range(1, n_steps):
        t[k] = k * dt
        # Rampa de arranque
        for _ in range(ramp_steps_per_pi):
            if lim_pot < 100.0:
                lim_pot += ramp_increment

        # Control PI
        error = tina["T_set"] - T[k - 1]
        P = tina["Kp"] * error
        integral += error * dt
        if tina["Ki"] > 0:
            if integral * tina["Ki"] > 100:
                integral = 100 / tina["Ki"]
            if integral * tina["Ki"] < 0:
                integral = 0
        I_term = tina["Ki"] * integral
        u = float(np.clip(P + I_term, 0, 100))

        if T[k - 1] >= tina["T_set"] + 2.0:
            u = 0.0

        u = min(u, lim_pot)
        power[k] = u

        # Modelo térmico (Retardo de transporte + primer orden)
        k_delay = max(0, k - int(tina["retardo"] / dt))
        u_delayed = power[k_delay] / 100.0

        Q_in = u_delayed * tina["P_max"]
        Q_out = (T[k - 1] - t_amb) / r_th
        dT = (Q_in - Q_out) / c_th * dt
        T[k] = T[k - 1] + dT

    return t, T, power


def graficar_simulacion_termica(guardar_archivo=False, mostrar=False, ruta_salida="respuesta_termica_PI.png", t_total=1200, dt=1.0):
    """Genera las gráficas de simulación de respuesta térmica para las 4 tinas."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 10), dpi=120)
    fig.suptitle("Simulación de Respuesta Térmica PI — Firmware v3.1\n"
                 "Parámetros reales del sistema de galvanoplastia",
                 fontsize=14, fontweight='bold', y=0.98)

    for idx, tina in enumerate(TINAS_DEFAULT):
        ax = axes[idx // 2][idx % 2]
        t, T, power = simular_tina(tina, t_total=t_total, dt=dt)

        color_t = '#38bdf8'
        color_sp = '#ef4444'
        color_p = '#34d399'

        ax.plot(t, T, color=color_t, linewidth=2, label='Temperatura (°C)')
        ax.axhline(y=tina["T_set"], color=color_sp, linestyle='--', linewidth=1.5,
                   label=f'Setpoint = {tina["T_set"]}°C', alpha=0.8)
        ax.fill_between(t, tina["T_set"]-1, tina["T_set"]+1,
                        color=color_sp, alpha=0.08, label='Banda ±1°C')

        ax2 = ax.twinx()
        ax2.fill_between(t, 0, power, color=color_p, alpha=0.15, label='Potencia (%)')
        ax2.set_ylabel('Potencia (%)', color=color_p, fontsize=9)
        ax2.set_ylim(0, 120)
        ax2.tick_params(axis='y', labelcolor=color_p)

        ax.set_title(tina["nombre"], fontsize=11, fontweight='bold')
        ax.set_xlabel('Tiempo (s)')
        ax.set_ylabel('Temperatura (°C)')
        ax.legend(loc='lower right', fontsize=8)
        ax.grid(True, alpha=0.2)
        ax.set_xlim(0, t_total)

    plt.tight_layout(rect=[0, 0, 1, 0.94])
    if guardar_archivo:
        plt.savefig(ruta_salida, dpi=200, bbox_inches='tight', facecolor='white')
        print(f"✅ Gráfica guardada: {ruta_salida}")
    if mostrar:
        plt.show()
    plt.close(fig)
    return fig


if __name__ == '__main__':
    graficar_simulacion_termica(guardar_archivo=True, mostrar=True)
