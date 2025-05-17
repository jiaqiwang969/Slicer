#!/usr/bin/env python3
"""tube_transfer_compare.py
生成有限长圆管传递函数对比图。
情形:
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
L = 0.25758    # meters (29.5 cm)
T = 26.5
fmax = 10000
N = 2000
freq = np.linspace(1, fmax, N)

# ------------- 四种边界组合 -------------
# 1) Hard — Zero
H_hz = Tube(D, L, T, end_left="hard", end_right="zero").transfer_function(freq)
# 2) Hard — Hard
H_hh = Tube(D, L, T, end_left="hard", end_right="hard").transfer_function(freq)
# 3) Zero — Hard
H_zh = Tube(D, L, T, end_left="zero", end_right="hard").transfer_function(freq)
# 4) Zero — Zero
H_zz = Tube(D, L, T, end_left="zero", end_right="zero").transfer_function(freq)

fig, ax = plt.subplots(2, 1, figsize=(9, 6), sharex=True)

ax[0].plot(freq, 20*np.log10(np.abs(H_hz)), label="Hard-Zero", linewidth=1.2)
ax[0].plot(freq, 20*np.log10(np.abs(H_hh)), label="Hard-Hard", linestyle="--", linewidth=1.2)
ax[0].plot(freq, 20*np.log10(np.abs(H_zh)), label="Zero-Hard", linestyle=":", linewidth=1)
ax[0].plot(freq, 20*np.log10(np.abs(H_zz)), label="Zero-Zero", linestyle="-.", linewidth=1)
ax[0].set_ylabel("|H| (dB)")
ax[0].legend()
ax[0].grid()

ax[1].plot(freq, np.unwrap(np.angle(H_hz)), label="Hard-Zero", linewidth=1.2)
ax[1].plot(freq, np.unwrap(np.angle(H_hh)), label="Hard-Hard", linestyle="--", linewidth=1.2)
ax[1].plot(freq, np.unwrap(np.angle(H_zh)), label="Zero-Hard", linestyle=":", linewidth=1)
ax[1].plot(freq, np.unwrap(np.angle(H_zz)), label="Zero-Zero", linestyle="-.", linewidth=1)
ax[1].set_xlabel("Frequency (Hz)")
ax[1].set_ylabel("Phase (rad)")
ax[1].grid()

# ----- 标注共振峰 (Hard-Hard & Hard-Zero) -----
def annotate_peaks(mag_db: np.ndarray, label_color: str):
    """在幅度曲线中标注局部峰值位置"""
    for i in range(1, len(freq)-1):
        if mag_db[i] > mag_db[i-1] and mag_db[i] > mag_db[i+1]:
            # 峰值高出邻域 3 dB
            if mag_db[i] - np.mean(mag_db[max(0, i-20):i+20]) > 3:
                f_peak = freq[i]
                ax[0].annotate(
                    f"{f_peak/1000:.2f}k", xy=(f_peak, mag_db[i]), xytext=(f_peak, mag_db[i]+8),
                    arrowprops=dict(arrowstyle="->", color=label_color, lw=0.8),
                    fontsize=7, color=label_color, rotation=45,
                )

annotate_peaks(20*np.log10(np.abs(H_hh)), label_color="red")
annotate_peaks(20*np.log10(np.abs(H_hz)), label_color="blue")

fig.suptitle(f"Transfer Function Comparison – Air (T={T}°C, D=29.5 mm, L=25.758 cm)")

plt.tight_layout()

# 保存到当前脚本所在目录，确保路径正确
out_dir = os.path.dirname(os.path.abspath(__file__))
png_path = os.path.join(out_dir, "tube_transfer_compare.png")
pdf_path = os.path.join(out_dir, "tube_transfer_compare.pdf")
fig.savefig(png_path, dpi=300)
fig.savefig(pdf_path)
print("Saved figure to", png_path, "and", pdf_path)
