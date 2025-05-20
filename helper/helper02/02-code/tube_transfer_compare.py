#!/usr/bin/env python3
"""tube_transfer_compare.py
生成有限长圆管在空气和水中的传递函数对比图。
情形 (空气 vs 水):
  1) 左端 hard, 右端 zero (H_hz)
  2) 左端 hard, 右端 hard (H_hh)
输出 PNG+PDF 保存到同目录。
"""
import numpy as np
# 使用无 GUI 后端，便于服务器环境生成图片
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from cyl_transfer import Tube
import os

D = 0.0295  # meters
L = 0.25758    # meters (25.758 cm)
T_air = 26.5 # Air temperature in Celsius
T_water = 20.0 # Water temperature in Celsius (can be same or different)

fmax = 10000
N = 2000
freq = np.linspace(1, fmax, N)

# ------------- 空气中的四种边界组合 -------------
print("Calculating for Air...")
H_hz_air = Tube(D, L, T_air, medium="air", end_left="hard", end_right="zero").transfer_function(freq)
H_hh_air = Tube(D, L, T_air, medium="air", end_left="hard", end_right="hard").transfer_function(freq)
H_zh_air = Tube(D, L, T_air, medium="air", end_left="zero", end_right="hard").transfer_function(freq)
H_zz_air = Tube(D, L, T_air, medium="air", end_left="zero", end_right="zero").transfer_function(freq)

# ------------- 水中的四种边界组合 -------------
print("Calculating for Water...")
H_hz_water = Tube(D, L, T_water, medium="water", end_left="hard", end_right="zero").transfer_function(freq)
H_hh_water = Tube(D, L, T_water, medium="water", end_left="hard", end_right="hard").transfer_function(freq)
H_zh_water = Tube(D, L, T_water, medium="water", end_left="zero", end_right="hard").transfer_function(freq)
H_zz_water = Tube(D, L, T_water, medium="water", end_left="zero", end_right="zero").transfer_function(freq)

fig, ax = plt.subplots(2, 2, figsize=(16, 10), sharex=True)

# 空气中的结果图 (左侧列)
ax[0,0].plot(freq, 20*np.log10(np.abs(H_hz_air)), label="H-Z (Air)", linewidth=1.2, color="blue")
ax[0,0].plot(freq, 20*np.log10(np.abs(H_hh_air)), label="H-H (Air)", linestyle="--", linewidth=1.2, color="lightblue")
ax[0,0].plot(freq, 20*np.log10(np.abs(H_zh_air)), label="Z-H (Air)", linestyle=":", linewidth=1, color="skyblue")
ax[0,0].plot(freq, 20*np.log10(np.abs(H_zz_air)), label="Z-Z (Air)", linestyle="-.", linewidth=1, color="deepskyblue")
ax[0,0].set_ylabel("|H| (dB)")
ax[0,0].legend()
ax[0,0].grid(True)
ax[0,0].set_title(f"Air (T={T_air}°C)")

ax[1,0].plot(freq, np.unwrap(np.angle(H_hz_air)), label="H-Z (Air)", linewidth=1.2, color="blue")
ax[1,0].plot(freq, np.unwrap(np.angle(H_hh_air)), label="H-H (Air)", linestyle="--", linewidth=1.2, color="lightblue")
ax[1,0].plot(freq, np.unwrap(np.angle(H_zh_air)), label="Z-H (Air)", linestyle=":", linewidth=1, color="skyblue")
ax[1,0].plot(freq, np.unwrap(np.angle(H_zz_air)), label="Z-Z (Air)", linestyle="-.", linewidth=1, color="deepskyblue")
ax[1,0].set_xlabel("Frequency (Hz)")
ax[1,0].set_ylabel("Phase (rad)")
ax[1,0].grid(True)

# 水中的结果图 (右侧列)
ax[0,1].plot(freq, 20*np.log10(np.abs(H_hz_water)), label="H-Z (Water)", linewidth=1.2, color="red")
ax[0,1].plot(freq, 20*np.log10(np.abs(H_hh_water)), label="H-H (Water)", linestyle="--", linewidth=1.2, color="lightcoral")
ax[0,1].plot(freq, 20*np.log10(np.abs(H_zh_water)), label="Z-H (Water)", linestyle=":", linewidth=1, color="salmon")
ax[0,1].plot(freq, 20*np.log10(np.abs(H_zz_water)), label="Z-Z (Water)", linestyle="-.", linewidth=1, color="tomato")
ax[0,1].legend()
ax[0,1].grid(True)
ax[0,1].set_title(f"Water (T={T_water}°C)")

ax[1,1].plot(freq, np.unwrap(np.angle(H_hz_water)), label="H-Z (Water)", linewidth=1.2, color="red")
ax[1,1].plot(freq, np.unwrap(np.angle(H_hh_water)), label="H-H (Water)", linestyle="--", linewidth=1.2, color="lightcoral")
ax[1,1].plot(freq, np.unwrap(np.angle(H_zh_water)), label="Z-H (Water)", linestyle=":", linewidth=1, color="salmon")
ax[1,1].plot(freq, np.unwrap(np.angle(H_zz_water)), label="Z-Z (Water)", linestyle="-.", linewidth=1, color="tomato")
ax[1,1].set_xlabel("Frequency (Hz)")
ax[1,1].grid(True)

# 统一Y轴范围，便于比较
min_db_air = np.min([20*np.log10(np.abs(H_hz_air)), 20*np.log10(np.abs(H_hh_air)), 20*np.log10(np.abs(H_zh_air)), 20*np.log10(np.abs(H_zz_air))])
max_db_air = np.max([20*np.log10(np.abs(H_hz_air)), 20*np.log10(np.abs(H_hh_air)), 20*np.log10(np.abs(H_zh_air)), 20*np.log10(np.abs(H_zz_air))])
min_db_water = np.min([20*np.log10(np.abs(H_hz_water)), 20*np.log10(np.abs(H_hh_water)), 20*np.log10(np.abs(H_zh_water)), 20*np.log10(np.abs(H_zz_water))])
max_db_water = np.max([20*np.log10(np.abs(H_hz_water)), 20*np.log10(np.abs(H_hh_water)), 20*np.log10(np.abs(H_zh_water)), 20*np.log10(np.abs(H_zz_water))])

global_min_db = min(min_db_air, min_db_water) - 10 # Add some padding
global_max_db = max(max_db_air, max_db_water) + 10 # Add some padding

ax[0,0].set_ylim([global_min_db, global_max_db])
ax[0,1].set_ylim([global_min_db, global_max_db])

# ----- 标注共振峰 (Hard-Hard & Hard-Zero, 仅空气) -----
def annotate_peaks(target_ax, mag_db: np.ndarray, freq_array: np.ndarray, label_prefix: str, label_color: str):
    """在幅度曲线中标注局部峰值位置"""
    for i in range(1, len(freq_array)-1):
        # 寻找显著峰值
        if mag_db[i] > mag_db[i-1] and mag_db[i] > mag_db[i+1]:
            prominence = mag_db[i] - max(mag_db[max(0,i-50):i].max() if i > 0 else -np.inf,
                                         mag_db[i+1:min(len(mag_db),i+50)].max() if i < len(mag_db)-1 else -np.inf)
            if prominence > 6: # 峰值至少比周围高6dB
                f_peak = freq_array[i]
                target_ax.annotate(
                    f"{f_peak/1000:.1f}k", xy=(f_peak, mag_db[i]), xytext=(f_peak, mag_db[i]+8),
                    arrowprops=dict(arrowstyle="->", color=label_color, lw=0.8),
                    fontsize=7, color=label_color, rotation=45,
                )

print("Annotating peaks for Air...")
annotate_peaks(ax[0,0], 20*np.log10(np.abs(H_hh_air)), freq, "H-H Air", "darkblue")
annotate_peaks(ax[0,0], 20*np.log10(np.abs(H_hz_air)), freq, "H-Z Air", "dodgerblue")

print("Annotating peaks for Water...")
annotate_peaks(ax[0,1], 20*np.log10(np.abs(H_hh_water)), freq, "H-H Water", "darkred")
annotate_peaks(ax[0,1], 20*np.log10(np.abs(H_hz_water)), freq, "H-Z Water", "crimson")


fig.suptitle(f"Tube Transfer Function Comparison: Air vs Water\nD={D*1e3:.1f}mm, L={L*100:.1f}cm", fontsize=16)

plt.tight_layout(rect=[0, 0, 1, 0.95]) # Adjust layout for suptitle

# 保存到当前脚本所在目录，确保路径正确
out_dir = os.path.dirname(os.path.abspath(__file__))
base_filename = "tube_transfer_air_vs_water_compare"
png_path = os.path.join(out_dir, base_filename + ".png")
pdf_path = os.path.join(out_dir, base_filename + ".pdf")
fig.savefig(png_path, dpi=300)
fig.savefig(pdf_path)
print(f"Saved figures to {out_dir}")
