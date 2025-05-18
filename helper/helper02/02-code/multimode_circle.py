# multimode_circle.py
import numpy as np
# 使用无 GUI 后端以便在服务器/脚本环境生成图片而无需显示
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as tri
from scipy import special

# ---------- 基本参数 ----------
# === 介质及声速 ===
T = 26.5  # ℃

# 两种介质参数配置
MEDIA = {
    "air": {},  # 空气无需额外参数
    "sea": {"S": 35.0, "Z": 0.0},
}

# 待计算的圆管直径列表 (单位: m)
DIAMETERS = [29.5e-3, 0.2, 0.54]  # 0.0295 m, 0.2 m, 0.54 m

fc_max = 20e3  # 关注 20 kHz 以内模态

# ---------- 公共极坐标网格（按最大半径生成一次即可） ----------
R_max = max(DIAMETERS) / 2
Nr, Nth = 180, 360
r_grid = np.linspace(0, R_max, Nr)
th_grid = np.linspace(0, 2 * np.pi, Nth, endpoint=False)
Rg_full, Tg_full = np.meshgrid(r_grid, th_grid, indexing="ij")
X_full = (Rg_full * np.cos(Tg_full)).ravel()
Y_full = (Rg_full * np.sin(Tg_full)).ravel()
triang_full = tri.Triangulation(X_full, Y_full)


def sound_speed_air(Tc: float) -> float:
    """摄氏温度下空气声速近似公式 (m/s)"""
    return 331.3 * np.sqrt(1 + Tc / 273.15)


def sound_speed_sea(Tc: float, S: float = 35.0, Z: float = 0.0) -> float:
    """Mackenzie (1981) 海水声速公式, 误差±0.3 m/s"""
    return (
        1448.96
        + 4.591 * Tc
        - 5.304e-2 * Tc**2
        + 2.374e-4 * Tc**3
        + 1.340 * (S - 35.0)
        + 1.630e-2 * Z
        + 1.675e-7 * Z**2
        - 1.025e-2 * Tc * (S - 35.0)
        - 7.139e-13 * Tc * Z**3
    )


# ---------- 模态计算函数 ----------
def compute_modes(D: float, c_speed: float):
    """返回给定直径 D (m) 的模态列表 [(m,n,γ,fc)]，已按 fc 升序"""
    R = D / 2
    modes = [(0, 0, 0.0, 0.0)]  # 平面波
    N_n_max, M_m_max = 5, 5
    for n in range(N_n_max):
        gamma = special.jnp_zeros(n, M_m_max)
        for m, gm in enumerate(gamma, start=1):
            fc = c_speed * gm / (2 * np.pi * R)
        if fc <= fc_max:
            modes.append((m, n, gm, fc))
modes.sort(key=lambda x: x[3])
    return modes, R


# 用于收集对比结果
compare_rows = []

# 外层循环: 介质
for medium, cfg in MEDIA.items():
    if medium == "air":
        c = sound_speed_air(T)
    elif medium == "sea":
        c = sound_speed_sea(T, cfg["S"], cfg["Z"])
    else:
        raise ValueError("Unsupported medium")

    print(f"\n===== MEDIUM: {medium.upper()}  c={c:.2f} m/s =====")

    # 内层循环: 直径
    for D in DIAMETERS:
        modes, R = compute_modes(D, c)

        # 直接解析计算 (1,1) 截止频率，避免被 fc_max 筛掉
        fc11 = 0.586 * c / D  # 0.293*c/R = 0.586*c/D

        compare_rows.append((D, medium, fc11))

        print(f"D={D*1000:.1f} mm   fc11={fc11/1000:.2f} kHz")

        # 针对当前 R 裁剪网格（加快绘图）
        mask = Rg_full <= R  # 仅保留圆内节点
        Rg = Rg_full[mask]
        Tg = Tg_full[mask]
X = (Rg * np.cos(Tg)).ravel()
Y = (Rg * np.sin(Tg)).ravel()
triang = tri.Triangulation(X, Y)

        # 生成模态形状图
cols = 4
        rows = int(np.ceil(len(modes) / cols))
        fig, axes = plt.subplots(rows, cols, figsize=(cols * 3, rows * 3), subplot_kw={"aspect": "equal"})
axes = axes.flatten()

for ax, (m, n, gm, fc) in zip(axes, modes):
    J = special.jv(n, gm * Rg / R)
            psi = J if n == 0 else J * np.sin(n * Tg)
            ax.scatter(X * 1e3, Y * 1e3, c=psi.ravel(), cmap="seismic", s=4, marker="s", vmin=-1, vmax=1)
            th = np.linspace(0, 2 * np.pi, 720)
            ax.plot(R * np.cos(th) * 1e3, R * np.sin(th) * 1e3, "k", lw=1)
    ax.set_xticks([])
    ax.set_yticks([])
            ax.set_title(rf"$\psi_{{{n}{m}}}$\n$f_c={fc:.0f}$ Hz", fontsize=8)

for ax in axes[len(modes):]:
            ax.axis("off")

        fig.suptitle(f"Circular Waveguide Modes (D={D*1e3:.1f} mm, T={T}℃)", fontsize=12)
plt.tight_layout()
        fname = f"circle_modes_{int(D*1e3)}mm"
        fig.savefig(fname + ".png", dpi=300)
        fig.savefig(fname + ".pdf")
        plt.close(fig)

# -------- 保存 compare.txt --------
with open("compare.txt", "w", encoding="utf-8") as f_cmp:
    f_cmp.write("Diameter_mm\tMedium\tfc11_Hz\n")
    for D, medium, fc in compare_rows:
        f_cmp.write(f"{D*1e3:.1f}\t{medium}\t{fc:.2f}\n")
print("\nComparison table saved to compare.txt")
