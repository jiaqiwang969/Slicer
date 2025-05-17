#!/usr/bin/env python3
"""cyl_transfer.py
================================
简易圆柱硬壁管道(一维平面波近似)传递函数计算脚本。
支持三种端口边界:
    - radiation  (开口辐射阻抗)
    - hard       (硬壁/速度零)
    - zero       (零压力)

作者: 自动生成
"""
from __future__ import annotations
import argparse
import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass

# ----------------------------- 物理参数 -----------------------------

def air_density(Tc: float = 20.0) -> float:
    """简易理想气体:  rho = 1.204 kg/m^3 @ 20ºC, 线性校正."""
    return 1.204 * (273.15/(Tc+273.15))

def sound_speed_air(Tc: float = 20.0) -> float:
    return 331.3 * np.sqrt(1 + Tc/273.15)

# ----------------------------- 阻抗模型 -----------------------------

def radiation_impedance(r: float, freq: np.ndarray, rho: float, c: float) -> np.ndarray:
    """平面圆活塞辐射阻抗近似 (Rayleigh, 低阶展开)。返回复数数组。"""
    k = 2 * np.pi * freq / c
    ka = k * r
    # 防止除零
    ka[ka==0] = 1e-12
    Z_rad = rho * c * (1 - 2j/(np.pi * ka))
    return Z_rad

@dataclass
class Tube:
    D: float   # 直径 (m)
    L: float   # 长度 (m)
    T: float   # 温度(ºC)
    end_left: str  = "hard"     # 'radiation' / 'hard' / 'zero'
    end_right: str = "radiation"

    def characteristic(self):
        c = sound_speed_air(self.T)
        rho = air_density(self.T)
        a = self.D/2
        Z0 = rho * c / (np.pi * a**2)
        return rho, c, a, Z0

    def load_impedance(self, kind: str, freq: np.ndarray, rho: float, c: float, a: float, Z0: float):
        kind = kind.lower()
        if kind == "hard":
            return 1e9 * Z0 * np.ones_like(freq)
        elif kind == "zero":
            return 1e-9 * Z0 * np.ones_like(freq)
        elif kind == "radiation":
            return radiation_impedance(a, freq, rho, c)
        else:
            raise ValueError(f"Unknown boundary kind: {kind}")

    def transfer_function(self, freq: np.ndarray):
        """计算 H(f)=P_right/P_left (平面波平均压)。"""
        rho, c, a, Z0 = self.characteristic()
        k = 2 * np.pi * freq / c
        ZL = self.load_impedance(self.end_left, freq, rho, c, a, Z0)
        ZR = self.load_impedance(self.end_right, freq, rho, c, a, Z0)

        # ABCD矩阵
        A = np.cos(k * self.L)
        B = 1j * Z0 * np.sin(k * self.L)
        C = 1j * np.sin(k * self.L) / Z0
        D = A.copy()  # cos(kL)

        # 两端负载, 假设左端由体积流速度源 U_s=1 且阻抗Zs=0 驱动
        # 使用端口网络求解: P_left = ZL * U_left
        # 联立方程可得 P_right
        # 这里简化: 计算输入阻抗 Zin, 然后得到右端压强
        Zin = A*ZR + B
        Zin /= C*ZR + D
        # 源体积速度 =1 m^3/s, P_left = Zin * 1
        P_left = Zin
        # 右端流量, 由ABCD关系: U_right = (A*1 + B/ZR)/(C*1 + D/ZR) ??? easier: compute P_right = ZR * U_right.
        # 用传输矩阵
        # [P_left]   [A B][P_right]
        # [U_left] = [C D][U_right]
        # U_left=1, P_left=Zin
        # Solve for P_right: from first row: P_left = A*P_right + B*U_right; second row: 1 = C*P_right + D*U_right
        # Solve linear equations
        denom = A*D - B*C
        P_right = (P_left*D - B) / denom
        return P_right / P_left


def main():
    parser = argparse.ArgumentParser(description="Finite circular tube transfer function (plane wave)")
    parser.add_argument("--D", type=float, default=0.0295, help="Diameter in m (default 0.0295)")
    parser.add_argument("--L", type=float, default=0.1, help="Length in m (default 0.1)")
    parser.add_argument("--T", type=float, default=26.5, help="Temperature in Celsius (default 26.5)")
    parser.add_argument("--fmax", type=float, default=10000, help="Max frequency Hz")
    parser.add_argument("--n", type=int, default=2000, help="Number of freq samples")
    parser.add_argument("--left", choices=["hard","zero","radiation"], default="hard")
    parser.add_argument("--right", choices=["hard","zero","radiation"], default="radiation")
    parser.add_argument("--plot", action="store_true", help="Plot magnitude and phase")
    args = parser.parse_args()

    freq = np.linspace(1, args.fmax, args.n)
    tube = Tube(D=args.D, L=args.L, T=args.T, end_left=args.left, end_right=args.right)
    H = tube.transfer_function(freq)
    if args.plot:
        fig, ax = plt.subplots(2,1, figsize=(8,6), sharex=True)
        ax[0].plot(freq, 20*np.log10(np.abs(H)))
        ax[0].set_ylabel("|H| (dB)")
        ax[1].plot(freq, np.unwrap(np.angle(H)))
        ax[1].set_ylabel("Phase (rad)")
        ax[1].set_xlabel("Frequency (Hz)")
        ax[0].grid(); ax[1].grid()
        title = f"Tube D={args.D*1e3:.1f} mm, L={args.L*100:.1f} cm, left={args.left}, right={args.right}"
        ax[0].set_title(title)
        plt.tight_layout()
        plt.show()
    else:
        # 打印 10 行示例
        for f, mag in zip(freq[::args.n//10], 20*np.log10(np.abs(H))[::args.n//10]):
            print(f"{f:.0f} Hz\t{mag:.2f} dB")

if __name__ == "__main__":
    main() 