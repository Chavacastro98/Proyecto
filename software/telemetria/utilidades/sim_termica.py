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
import numpy as np
import matplotlib.pyplot as plt

# ── Parámetros termodinámicos (de Control_termico.m) ──
T_AMB = 25.0
rho = 1.0        # kg/L
cp = 4184.3      # J/(kg·K)
h_eff = 65.0     # W/(m²·K)

tinas = [
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

dt = 1.0          # Período PI (1 s)
t_total = 1200    # Tiempo de simulación (s)
n_steps = int(t_total / dt)
RAMP_PERIOD = 0.2  # 200 ms
RAMP_INCREMENT = 1.0
RAMP_STEPS_PER_PI = int(dt / RAMP_PERIOD)

fig, axes = plt.subplots(2, 2, figsize=(16, 10), dpi=120)
fig.suptitle("Simulación de Respuesta Térmica PI — Firmware v3.1\n"
             "Parámetros reales del sistema de galvanoplastia",
             fontsize=14, fontweight='bold', y=0.98)

for idx, tina in enumerate(tinas):
    ax = axes[idx // 2][idx % 2]

    m = tina["vol"] * rho
    C_th = m * cp
    R_th = 1.0 / (h_eff * tina["A_s"])
    tau = C_th * R_th

    t = np.zeros(n_steps)
    T = np.zeros(n_steps)
    T[0] = T_AMB
    power = np.zeros(n_steps)
    integral = 0.0
    lim_pot = 0.0

    for k in range(1, n_steps):
        t[k] = k * dt
        # ── Rampa de arranque ──
        for _ in range(RAMP_STEPS_PER_PI):
            if lim_pot < 100.0:
                lim_pot += RAMP_INCREMENT

        # ── Control PI ──
        error = tina["T_set"] - T[k-1]
        P = tina["Kp"] * error
        integral += error * dt
        if tina["Ki"] > 0:
            if integral * tina["Ki"] > 100:
                integral = 100 / tina["Ki"]
            if integral * tina["Ki"] < 0:
                integral = 0
        I = tina["Ki"] * integral
        u = np.clip(P + I, 0, 100)

        if T[k-1] >= tina["T_set"] + 2.0:
            u = 0

        u = min(u, lim_pot)
        power[k] = u

        # ── Modelo térmico (Retardo de transporte + primer orden) ──
        k_delay = max(0, k - int(tina["retardo"] / dt))
        u_delayed = power[k_delay] / 100.0

        Q_in = u_delayed * tina["P_max"]
        Q_out = (T[k-1] - T_AMB) / R_th
        dT = (Q_in - Q_out) / C_th * dt
        T[k] = T[k-1] + dT

    # ── Graficar ──
    color_t = '#38bdf8'
    color_sp = '#ef4444'
    color_p = '#34d399'

    ax.plot(t, T, color=color_t, linewidth=2, label=f'Temperatura (°C)')
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
plt.savefig('respuesta_termica_PI.png', dpi=200, bbox_inches='tight',
            facecolor='white')
plt.show()
print("✅ Gráfica guardada: respuesta_termica_PI.png")
