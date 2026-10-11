"""
============================================================================
SIMULACIÓN DE RESPUESTA DE pH — Filtro de Mediana + Suavizado Adaptativo
============================================================================
Simula cómo el pipeline de filtrado del firmware responde a:
1. Señal estable con ruido gaussiano
2. Perturbación por paso (cambio real de pH)
3. Picos espurios (ruido impulsivo EMI de TRIACs)

Ejecutar: python sim_ph.py
Requiere: pip install matplotlib numpy
"""
import matplotlib.pyplot as plt
import numpy as np


def median3(a, b, c):
    """Retorna la mediana de 3 valores."""
    return sorted([a, b, c])[1]


def filtrar_senyal_ph(raw_signal, umbral_adaptativo=0.35, peso_anterior=0.7, peso_nuevo=0.3):
    """
    Aplica el pipeline de filtrado de pH del firmware:
    Mediana de 3 + Filtro Adaptativo (conmutación según delta).
    """
    n = len(raw_signal)
    if n == 0:
        return np.array([])

    hist = [raw_signal[0]] * 3
    hist_idx = 0
    ph_filtered = np.zeros(n)
    ph_filtered[0] = raw_signal[0]

    for k in range(1, n):
        hist[hist_idx] = raw_signal[k]
        hist_idx = (hist_idx + 1) % 3

        med = median3(hist[0], hist[1], hist[2])
        delta = abs(med - ph_filtered[k - 1])
        if delta > umbral_adaptativo:
            ph_filtered[k] = med
        else:
            ph_filtered[k] = peso_anterior * ph_filtered[k - 1] + peso_nuevo * med

    return ph_filtered


def generar_datos_simulacion_ph(n=500, seed=42):
    """
    Genera señal de pH simulada con ruido gaussiano y picos EMI.
    Retorna: (ph_real, raw_signal, spike_idx, time_s)
    """
    np.random.seed(seed)
    ph_real = np.full(n, 4.5)
    if n > 100:
        ph_real[100:] = 7.0
    if n > 300:
        ph_real[300:] = 3.8

    noise = np.random.normal(0, 0.05, n)
    spikes = np.zeros(n)
    spike_candidates = [45, 46, 150, 210, 211, 350, 420]
    spike_idx = [si for si in spike_candidates if si < n]
    for si in spike_idx:
        spikes[si] = np.random.choice([-1.5, 1.8, -2.0, 2.5])

    raw_signal = ph_real + noise + spikes
    time_s = np.arange(n) * 0.2
    return ph_real, raw_signal, spike_idx, time_s


def graficar_simulacion_ph(guardar_archivo=False, mostrar=False, ruta_salida="respuesta_filtro_ph.png", n=500):
    """Genera las gráficas de simulación del pipeline de filtrado de pH."""
    ph_real, raw_signal, spike_idx, time_s = generar_datos_simulacion_ph(n)
    ph_filtered = filtrar_senyal_ph(raw_signal)

    fig, axes = plt.subplots(3, 1, figsize=(16, 12), dpi=120,
                              gridspec_kw={'height_ratios': [1, 1, 0.6]})
    fig.suptitle("Simulación del Pipeline de Filtrado de pH — Firmware v3.1\n"
                 "Mediana de 3 + Suavizado Adaptativo 70/30",
                 fontsize=14, fontweight='bold', y=0.98)

    # Panel 1: Señal cruda con ruido + picos
    axes[0].plot(time_s, raw_signal, color='#94a3b8', linewidth=0.8, alpha=0.7,
                 label='Señal cruda (con ruido + picos EMI)')
    axes[0].plot(time_s, ph_real, color='#ef4444', linewidth=2, linestyle='--',
                 label='pH real (sin ruido)', alpha=0.8)
    for si in spike_idx:
        axes[0].axvline(x=si*0.2, color='#f97316', alpha=0.3, linewidth=1)
    axes[0].set_ylabel('pH')
    axes[0].set_title('Señal de Entrada: pH con Ruido Gaussiano y Picos EMI', fontsize=11)
    axes[0].legend(loc='upper right', fontsize=9)
    axes[0].grid(True, alpha=0.2)
    axes[0].set_xlim(0, n*0.2)

    # Panel 2: Comparación filtrada vs real
    axes[1].plot(time_s, ph_filtered, color='#38bdf8', linewidth=2,
                 label='pH filtrado (Mediana + Adaptativo)')
    axes[1].plot(time_s, ph_real, color='#ef4444', linewidth=2, linestyle='--',
                 label='pH real', alpha=0.8)
    axes[1].fill_between(time_s, ph_real-0.1, ph_real+0.1,
                         color='#34d399', alpha=0.1, label='Banda ±0.1 pH')
    axes[1].set_ylabel('pH')
    axes[1].set_title('Señal Filtrada: Eliminación de Outliers y Suavizado', fontsize=11)
    axes[1].legend(loc='upper right', fontsize=9)
    axes[1].grid(True, alpha=0.2)
    axes[1].set_xlim(0, n*0.2)

    # Panel 3: Error de tracking
    error = ph_filtered - ph_real
    axes[2].fill_between(time_s, 0, error, where=(error >= 0),
                         color='#38bdf8', alpha=0.3)
    axes[2].fill_between(time_s, 0, error, where=(error < 0),
                         color='#f87171', alpha=0.3)
    axes[2].axhline(y=0, color='#64748b', linewidth=0.5)
    axes[2].axhline(y=0.1, color='#f97316', linewidth=1, linestyle=':', alpha=0.5,
                    label='±0.1 pH')
    axes[2].axhline(y=-0.1, color='#f97316', linewidth=1, linestyle=':', alpha=0.5)
    axes[2].set_xlabel('Tiempo (s)')
    axes[2].set_ylabel('Error (pH)')
    axes[2].set_title('Error de Seguimiento (Filtrado − Real)', fontsize=11)
    axes[2].legend(loc='upper right', fontsize=9)
    axes[2].grid(True, alpha=0.2)
    axes[2].set_xlim(0, n*0.2)
    axes[2].set_ylim(-0.5, 0.5)

    plt.tight_layout(rect=[0, 0, 1, 0.94])
    if guardar_archivo:
        plt.savefig(ruta_salida, dpi=200, bbox_inches='tight', facecolor='white')
        print(f"✅ Gráfica guardada: {ruta_salida}")
    if mostrar:
        plt.show()
    plt.close(fig)
    return fig


if __name__ == '__main__':
    graficar_simulacion_ph(guardar_archivo=True, mostrar=True)
