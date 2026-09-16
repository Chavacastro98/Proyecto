"""
============================================================================
VERIFICACIÓN DE LUT DE LINEALIZACIÓN TRIAC — 60 Hz
============================================================================
Verifica que la tabla de búsqueda (LUT) del Arduino Nano linealiza
correctamente la potencia RMS de la onda senoidal recortada.

Ejecutar: python verificar_lut.py
Requiere: pip install matplotlib numpy
"""
import numpy as np
import matplotlib.pyplot as plt

# LUT real del firmware (101 valores, de nano.ino)
lut_firmware = np.array([
    8333, 7366, 7108, 6924, 6776, 6649, 6538, 6436, 6343, 6256,
    6176, 6099, 6026, 5956, 5889, 5824, 5763, 5703, 5643, 5586,
    5531, 5476, 5423, 5371, 5319, 5269, 5221, 5171, 5124, 5076,
    5029, 4984, 4937, 4892, 4847, 4804, 4759, 4716, 4672, 4629,
    4587, 4544, 4502, 4459, 4417, 4376, 4334, 4292, 4251, 4207,
    4167, 4126, 4082, 4041, 3999, 3957, 3916, 3874, 3831, 3789,
    3746, 3704, 3661, 3617, 3574, 3529, 3486, 3441, 3396, 3349,
    3304, 3257, 3209, 3162, 3112, 3064, 3014, 2962, 2910, 2857,
    2802, 2747, 2690, 2630, 2570, 2509, 2444, 2377, 2307, 2234,
    2157, 2077, 1990, 1897, 1795, 1684, 1557, 1409, 1225, 967, 0
])

T_semi = 8333  # µs (semiciclo a 60 Hz)
pct = np.arange(101)

# Calcular ángulo de fase y potencia RMS teórica
alpha_fw = (lut_firmware / T_semi) * np.pi  # Ángulo en radianes
P_rms_fw = (1 - alpha_fw/np.pi + np.sin(2*alpha_fw)/(2*np.pi)) * 100

# Curva ideal
P_ideal = pct.astype(float)

# Error de linealización
error_pct = P_rms_fw - P_ideal

fig, axes = plt.subplots(2, 1, figsize=(14, 10), dpi=120,
                          gridspec_kw={'height_ratios': [2, 1]})
fig.suptitle("Verificación de LUT de Linealización TRIAC — 60 Hz\n"
             "Conversión Porcentaje → Retardo de Fase → Potencia RMS",
             fontsize=14, fontweight='bold', y=0.98)

# Panel 1: Potencia RMS vs Porcentaje
axes[0].plot(pct, P_ideal, color='#64748b', linewidth=1.5, linestyle='--',
             label='Ideal (lineal)', alpha=0.7)
axes[0].plot(pct, P_rms_fw, color='#38bdf8', linewidth=2.5,
             label='LUT del firmware (101 valores)')
axes[0].fill_between(pct, P_ideal, P_rms_fw, alpha=0.1, color='#38bdf8')
axes[0].set_xlabel('Porcentaje comandado (%)')
axes[0].set_ylabel('Potencia RMS real (%)')
axes[0].set_title('Linealización: Potencia Real vs Comandada', fontsize=11)
axes[0].legend(fontsize=10)
axes[0].grid(True, alpha=0.2)
axes[0].set_xlim(0, 100)
axes[0].set_ylim(0, 105)

# Panel 2: Error de linealización
axes[1].fill_between(pct, 0, error_pct, where=(error_pct >= 0),
                     color='#34d399', alpha=0.4, label='Sobrepotencia')
axes[1].fill_between(pct, 0, error_pct, where=(error_pct < 0),
                     color='#f87171', alpha=0.4, label='Subpotencia')
axes[1].axhline(y=0, color='#64748b', linewidth=0.8)
axes[1].axhline(y=1, color='#f97316', linewidth=1, linestyle=':', alpha=0.5)
axes[1].axhline(y=-1, color='#f97316', linewidth=1, linestyle=':', alpha=0.5,
                label='Banda ±1%')
axes[1].set_xlabel('Porcentaje comandado (%)')
axes[1].set_ylabel('Error (%)')
axes[1].set_title('Error de Linealización de la LUT', fontsize=11)
axes[1].legend(fontsize=9)
axes[1].grid(True, alpha=0.2)
axes[1].set_xlim(0, 100)

max_err = np.max(np.abs(error_pct))
axes[1].text(50, max(error_pct)*0.7,
             f'Error máximo: ±{max_err:.2f}%',
             fontsize=11, ha='center', fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='#1e293b',
                       edgecolor='#38bdf8', alpha=0.8),
             color='#38bdf8')

plt.tight_layout(rect=[0, 0, 1, 0.94])
plt.savefig('verificacion_lut_triac.png', dpi=200, bbox_inches='tight',
            facecolor='white')
plt.show()
print("✅ Gráfica guardada: verificacion_lut_triac.png")
