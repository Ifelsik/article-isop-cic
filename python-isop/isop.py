import numpy as np
import scipy.signal as signal
import matplotlib.pyplot as plt

# --- 1. ПАРАМЕТРЫ ФИЛЬТРА ---
R = 4            # Коэффициент децимации
N = 5            # Порядок CIC
ISOP_TAPS = 15   # Порядок FIR (нечетный)
BIT_WIDTH = 24   # Разрядность коэффициентов

# Настройка границ частот (относительно Найквиста)
# Найквист = 0.5 * Fs
# Мы корректируем до 80% от Найквиста (Passband)
fp_norm = 0.8 

# --- 2. РАСЧЕТ ИДЕАЛЬНОЙ АЧХ ---
def cic_magnitude(f):
    f = np.where(f == 0, 1e-9, f)
    # H(f) ~ |sinc(f)|^N
    val = np.abs(np.sin(np.pi * f) / (np.pi * f)) ** N
    return val

# --- 3. РАСЧЕТ КОЭФФИЦИЕНТОВ ISOP ---
num_points = 1000
freq_grid_norm = np.linspace(0, 1.0, num_points)

target_gain = []
for f_n in freq_grid_norm:
    f_real = f_n * 0.5 # Пересчет в шкалу CIC (0..0.5)
    
    if f_n <= fp_norm:
        # Passband: Компенсируем завал
        gain = 1.0 / cic_magnitude(f_real)
    else:
        # Stopband: Плавный спад в ноль
        t = (f_n - fp_norm) / (1.0 - fp_norm)
        gain = (1.0 / cic_magnitude(fp_norm * 0.5)) * (1 - t)
        if gain < 0: gain = 0
    target_gain.append(gain)

coeffs = signal.firwin2(ISOP_TAPS, freq_grid_norm, target_gain, window='hamming')

# --- 4. ВЫВОД КОЭФФИЦИЕНТОВ ---
scale_factor = 2**(BIT_WIDTH - 1) - 1
coeffs_fixed = np.round(coeffs * scale_factor).astype(int)

print(f"\n=== КОЭФФИЦИЕНТЫ (Verilog signed {BIT_WIDTH}) ===")
print(f"localparam signed [{BIT_WIDTH-1}:0] COEFFS [0:{ISOP_TAPS-1}] = '{{")
str_coeffs = ", ".join([str(c) for c in coeffs_fixed])
print(str_coeffs + "};")

# --- 5. ГЕНЕРАЦИЯ ЛЧМ (CHIRP) ---
num_samples = 2000
t = np.linspace(0, 1, num_samples)

# Генерируем сигнал от 0 до Частоты Найквиста
# Частота Найквиста = num_samples / 2 (так как длина массива = 1 сек "условно")
chirp_ideal = 100 * signal.chirp(t, f0=0, t1=1, f1=num_samples/2) 

# Эмуляция завала CIC
freqs_instant = np.linspace(0, 0.5, num_samples)
attenuation = cic_magnitude(freqs_instant)
chirp_droopy = chirp_ideal * attenuation

# Квантование
data_in_verilog = np.round(chirp_droopy).astype(int)
data_in_verilog = np.clip(data_in_verilog, -127, 127)

np.savetxt("../data/isop_input_chirp.txt", data_in_verilog, fmt="%d")

# --- 6. МОДЕЛИРОВАНИЕ ---
filtered_python = signal.lfilter(coeffs, 1.0, chirp_droopy)

# --- 7. ГРАФИКИ С ЛИНИЯМИ ---
plt.figure(figsize=(12, 10))

# Функция для рисования маркеров
def draw_markers(ax):
    # Линия 1: Конец коррекции (fp_norm)
    # Так как ось X - это отсчеты (0..num_samples), то позиция = num_samples * fp_norm
    idx_cutoff = num_samples * fp_norm
    ax.axvline(idx_cutoff, color='red', linestyle='--', linewidth=1.5)
    ax.text(idx_cutoff - 50, 110, 'Граница коррекции\n(Passband)', color='red', ha='right', fontweight='bold')
    
    # Линия 2: Найквист (Конец графика)
    idx_nyquist = num_samples
    ax.axvline(idx_nyquist, color='black', linestyle='-', linewidth=2)
    ax.text(idx_nyquist - 50, 110, 'Частота Найквиста\n(Fs/2)', color='black', ha='right', fontweight='bold')

    # Заливка зоны "мусора" (Aliasing zone)
    ax.axvspan(idx_cutoff, idx_nyquist, color='gray', alpha=0.1, hatch='///')
    ax.text((idx_cutoff + idx_nyquist)/2, 50, 'Зона подавления\n(Stopband)', color='gray', ha='center', alpha=0.7)

# График 1: Вход
plt.subplot(2, 1, 1)
plt.title("Входной сигнал: Выход CIC фильтра (с завалом АЧХ)")
plt.plot(data_in_verilog, color='orange', label="Вход ISOP")
plt.plot(100 * attenuation, color='blue', linestyle='--', alpha=0.6, label="Теоретическая огибающая")
plt.plot(-100 * attenuation, color='blue', linestyle='--', alpha=0.6)
draw_markers(plt.gca())
plt.ylabel("Амплитуда")
plt.legend(loc='lower left')
plt.grid(True)
plt.xlim(0, num_samples)

# График 2: Выход
plt.subplot(2, 1, 2)
plt.title("Выходной сигнал: После ISOP корректора")
plt.plot(filtered_python, color='green', label="Выход ISOP")
draw_markers(plt.gca())
plt.ylabel("Амплитуда")
plt.xlabel("Отсчеты (Время ~ Частота)")
plt.legend(loc='lower left')
plt.grid(True)
plt.xlim(0, num_samples)

plt.tight_layout()
plt.show()