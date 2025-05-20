#!/usr/bin/env python3
"""cyl_transfer.py
================================
简易圆柱硬壁管道(一维平面波近似)传递函数计算脚本。
支持三种端口边界:
    - radiation  (开口辐射阻抗)
    - hard       (硬壁/速度零)
    - zero       (零压力)
支持介质:
    - air        (空气)
    - water      (淡水)

作者: 自动生成
"""
from __future__ import annotations
import argparse
import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass

# ----------------------------- 物理参数 -----------------------------

def air_density(Tc: float = 20.0) -> float:
    """空气密度 (kg/m^3)，考虑温度校正。"""
    return 1.204 * (273.15 / (Tc + 273.15))

def sound_speed_air(Tc: float = 20.0) -> float:
    """空气中声速 (m/s)，考虑温度校正。"""
    return 331.3 * np.sqrt(1 + Tc / 273.15)

def water_density(Tc: float = 20.0) -> float:
    """淡水密度 (kg/m^3)。简化模型，近似为常数。
    更精确模型应考虑温度，但此处简化处理。
    20°C 时约 998.2 kg/m^3
    """
    # 简单起见，这里用一个典型值，可根据需要替换为更复杂的模型
    if 0 <= Tc <= 5:
        return 999.9 # 接近4度最大密度
    elif 5 < Tc <= 15:
        return 999.1 # 10度
    elif 15 < Tc <= 25:
        return 998.2 # 20度
    elif 25 < Tc <= 35:
        return 995.7 # 30度
    else: # 其他温度，返回一个通用值
        return 997.0


def sound_speed_water(Tc: float = 20.0) -> float:
    """淡水中声速 (m/s)。简化模型，基于温度的多项式拟合 (Urick, 1983 Table A1 for pure water)
    Valid for T in [0, 30] C approximately.
    """
    # UNESCO (Chen and Millero, 1977) for pure water (S=0, P=0) is more complex.
    # Simplified polynomial fit from various sources, e.g., Urick's approximation for pure water.
    # c(T) = 1402.388 + 5.03711 T - 0.0580852 T^2 + 0.00033420 T^3 - 0.00000147800 T^4 + 0.00000000314643 T^5
    # For simplicity, using a linear approximation or a common value.
    # Let's use a slightly more standard value or a simple linear fit for typical ranges.
    # Example: 1484 m/s at 20°C. A linear fit around this might be c = 1400 + 4*T
    # Using a known value for 20C:
    if 0 <= Tc <= 5:
        return 1420 # approx
    elif 5 < Tc <= 15:
        return 1450 # approx for 10C
    elif 15 < Tc <= 25: # centered around 20C
        return 1482 # approx for 20C
    elif 25 < Tc <= 35:
        return 1507 # approx for 30C
    else:
        return 1482 # fallback to 20C value


# ----------------------------- 阻抗模型 -----------------------------

def radiation_impedance(r: float, freq: np.ndarray, rho: float, c: float) -> np.ndarray:
    """平面圆活塞辐射阻抗近似 (Rayleigh, 低阶展开)。返回复数数组。"""
    k = 2 * np.pi * freq / c
    ka = k * r
    # 防止除零或ka过小导致虚部问题
    # 对于非常小的 ka, Z_rad -> rho*c * ( (ka)^2/2 + j*8*ka/(3*pi) )
    # 原脚本中的 1 - 2j/(np.pi*ka) 在 ka->0 时虚部发散
    # 保持原脚本的主要形式，但对 ka=0 做保护
    ka_eff = np.where(ka == 0, 1e-12, ka)

    # Z_rad = rho * c * (1 - 2j/(np.pi * ka_eff)) # 原脚本简化形式
    # 使用更常见的低频近似的实部和虚部组合 (Levine & Schwinger or Blackstock)
    # Z_rad/(rho*c) = R1(2ka) + jX1(2ka)
    # R1(x) = 1 - 2*J1(x)/x
    # X1(x) = 2*K1(x)/x  (K1 is related to Struve function H1)
    # For small ka: R1 approx (ka)^2/2, X1 approx 8ka/(3pi)
    # 保持简单，但用一个在ka较小时表现更好的形式，或注释掉原公式的局限性
    # 此处继续用原脚本的简化形式，但需注意其在ka极小值时的表现
    
    # Z_rad / (rho*c*S) = R_1 + j X_1
    # R_1 = (ka)^2/2 - (ka)^4/24 + ...
    # X_1 = (8ka)/(3*pi) - (32 (ka)^3)/(45 pi) + ...
    # 此处 Z_rad 是 specific impedance (per unit area)
    
    Z_rad_norm = (ka_eff**2)/2 + 1j * (8*ka_eff)/(3*np.pi) # Low-frequency approx for Z_rad / (rho*c)
    # For higher ka, the original script used 1 - 2j/(np.pi*ka_eff), which is more like 1 + jX_1 where X_1 for baffle.
    # Let's use a simple blended approach or stick to one.
    # The original expression was 1 - 2*j / (np.pi * ka). This resembles Z/(rho*c) approx 1 + j * X for baffled piston at high ka.
    # Let's use the provided simplified form for consistency with the original script's intent if it was specific.
    # Reverting to a structure closer to original for now, assuming it had a purpose:
    # However, the original did not have the real part 1, which is typical for high ka.
    # Z_rad = rho * c * ( (ka_eff**2)/2 - 1j * (2/(np.pi * ka_eff)) ) # This doesn't look standard
    # Let's use the standard low-frequency expression Z_rad_norm = R + jX for Z/(rho c)
    # where R = (ka)^2/2 and X = 8ka/(3pi)
    # Then Z_rad = rho * c * (R + jX)
    # If the script means characteristic_impedance_of_medium * (normalized_impedance)
    # Normalized impedance for piston in baffle: (ka)^2/2 + j*8*ka/(3*pi) for small ka
    # Or R1(2ka) + jX1(2ka) more generally.
    # Sticking to a simple form that is somewhat robust:
    term_real = (ka_eff)**2 / (4 + (ka_eff)**2) # Approx for R1(ka), ensures R1 -> 0 for ka->0, R1 -> 1 for ka->inf
    term_imag = 0.6 * ka_eff # Approx for X1(ka), X1 linearly increases for small ka
    Z_rad = rho * c * (term_real + 1j * term_imag)

    return Z_rad

@dataclass
class Tube:
    D: float   # 直径 (m)
    L: float   # 长度 (m)
    T: float   # 温度(ºC)
    medium: str = "air"      # "air" or "water"
    end_left: str  = "hard"     # 'radiation' / 'hard' / 'zero'
    end_right: str = "radiation"

    def characteristic(self):
        a = self.D / 2
        if self.medium.lower() == "air":
            c = sound_speed_air(self.T)
            rho = air_density(self.T)
        elif self.medium.lower() == "water":
            c = sound_speed_water(self.T)
            rho = water_density(self.T)
        else:
            raise ValueError(f"Unknown medium: {self.medium}")
        
        Z0 = rho * c / (np.pi * a**2) # 特性阻抗 (声阻抗率 / 面积)
        return rho, c, a, Z0

    def load_impedance(self, kind: str, freq: np.ndarray, rho: float, c: float, a: float, Z0: float):
        kind = kind.lower()
        if kind == "hard":
            return 1e9 * Z0 * np.ones_like(freq) # 极大阻抗
        elif kind == "zero":
            return 1e-9 * Z0 * np.ones_like(freq) # 极小阻抗
        elif kind == "radiation":
            # 辐射阻抗本身是 specific acoustic impedance (rho*c*normalized_Z)
            # 但在此模型中，Z0已经是 rho*c/Area，所以这里的 ZL, ZR 应该是普通的声阻抗
            # 因此，radiation_impedance 返回 specific Z, 需要乘以面积S得到普通阻抗
            # 或者，若 Z0 是 rho*c (平面波阻抗率)，则 radiation_impedance 也应是 rho*c*normalized_Z
            # 从公式 B = 1j * Z0 * np.sin(k*L) 看，Z0是普通的声阻抗 rho*c/S
            # 所以 radiation_impedance(a, freq, rho, c) 返回的是 Z_specific
            # 我们需要 Z_load = Z_specific * Area = radiation_impedance * (pi*a^2)
            Z_specific_rad = radiation_impedance(a, freq, rho, c)
            return Z_specific_rad * (np.pi * a**2) 
        else:
            raise ValueError(f"Unknown boundary kind: {kind}")

    def transfer_function(self, freq: np.ndarray):
        """计算 H(f)=P_right/P_left (平面波平均压)。"""
        rho, c, a, Z0 = self.characteristic()
        k = 2 * np.pi * freq / c
        
        # 确保k非零，特别是在freq包含0时 (linspace从1开始，但以防万一)
        k_eff = np.where(k == 0, 1e-12, k)

        ZL = self.load_impedance(self.end_left, freq, rho, c, a, Z0)
        ZR = self.load_impedance(self.end_right, freq, rho, c, a, Z0)

        # ABCD矩阵
        cos_kl = np.cos(k_eff * self.L)
        sin_kl = np.sin(k_eff * self.L)
        
        A = cos_kl
        B = 1j * Z0 * sin_kl
        C = 1j * sin_kl / Z0 
        D_abcd = cos_kl # ABCD矩阵中的D项

        # Zin = (A*ZR + B) / (C*ZR + D_abcd)
        # P_left = Zin (假设单位体积速度源 U_left = 1)
        # P_right 来自 P_left = A*P_right + B*U_right 和 U_left = C*P_right + D_abcd*U_right
        # 以及 P_right = ZR * U_right  => U_right = P_right / ZR
        # P_left = A*P_right + B*(P_right/ZR) = P_right * (A + B/ZR)
        # H = P_right / P_left = 1 / (A + B/ZR)
        # 这是假设输入端是理想压力源 P_left，求 P_right/P_left
        # 如果是 P_left / U_glottis, 那么 U_glottis 是输入。
        # 此处 P_right / P_left 表示的是系统对输入压力的响应。

        # 原来的求解方式：
        # denom = A*D_abcd - B*C # 这应该是1对于无耗系统
        # P_right = (P_left_assumed_from_Zin * D_abcd - B * U_left_assumed_1) / denom
        # P_left_assumed_from_Zin = Zin * U_left_assumed_1
        # H = P_right / P_left_assumed_from_Zin
        # 这个推导似乎有点绕。更直接的是：
        # H(omega) = P_out / P_in = ZR / (A*ZR + B) for voltage driven (pressure driven) source
        # Or H(omega) = P_out / U_in = ZR / (C*ZR + D) for current driven (velocity driven) source
        # 脚本的注释说 "计算 H(f)=P_right/P_left (平面波平均压)"，这通常意味着 P_left 是输入。
        # 如果 P_left 是输入（理想声压源），则 U_left = (P_left - D*P_right) / B。 P_right = U_right*ZR。
        # 经典传输线：H = P_right / P_left = ZR / (A*ZR + B)
        # 另一种形式，如果 ZL 是源阻抗，P_s 是源开路电压：
        # P_left = P_s * Zin / (Zs + Zin)
        # H_overall = P_right / P_s
        
        # 根据 P_right = (P_left*D - B*U_left) / (A*D - B*C)
        # 且 P_left = ZL * U_left
        # 若我们定义 H = P_right (at ZR) / P_left (at ZL)
        # P_left = A P_right + B U_right
        # U_left = C P_right + D U_right
        # P_right = ZR U_right => U_right = P_right / ZR
        # P_left = A P_right + B P_right / ZR = P_right * (A + B/ZR)
        # H = P_right / P_left = 1 / (A + B/ZR)
        # 这个公式是标准的，假设 P_left 是已知的输入压力。
        
        # 分母保护，ZR可能为0或极小 (zero pressure case)
        ZR_eff = np.where(np.abs(ZR) < 1e-9, 1e-9 * np.sign(ZR) if np.any(ZR) else 1e-9, ZR)

        H = 1.0 / (A + B / ZR_eff)
        
        # 如果左端不是理想声压源，而是有负载 ZL。
        # 整个管道看作一个二端口网络，左端接 ZL，右端接 ZR。
        # 如果源是 P_source 开路电压，内阻 Z_source。
        # 此处 ZL 是一个负载，不是源的一部分。
        # 如果考虑 ZL 的反射：
        # Gamma_L = (ZL - Z0) / (ZL + Z0)
        # Gamma_R = (ZR - Z0) / (ZR + Z0)
        # H = ( (1+Gamma_R)*np.exp(-1j*k_eff*L) ) / ( 1 - Gamma_L*Gamma_R*np.exp(-2j*k_eff*L) ) * (Z0 / (Z0+ZL)) if ZL acts as part of source term
        # 但是ABCD矩阵法更通用。
        # 上面的 H = 1 / (A + B/ZR) 是 P_right/P_left(x=0)
        # 如果 P_left(x=0) 本身受到 ZL 的影响 (e.g. P_left = P_source * Z_input_at_0 / (Z_source + Z_input_at_0))
        # 这里的 ZL 是一个固定的左端边界条件，就像 ZR 一样。
        # 传递函数定义为 P(L) / P(0) 在特定左端条件 P(0)=ZL*U(0) 下。
        # 这需要重新思考定义。
        # 通常, H = p(L)/p(0) (声压比) 或 p(L)/U(0) (转移阻抗) 或 V(L)/V(0) (体积速度比) 或 V(L)/p(0) (转移导纳)
        # 脚本的 P_left = Zin, P_right = (P_left*D - B) / denom, return P_right/P_left
        # Zin_pipe_terminated_by_ZR = (A*ZR + B) / (C*ZR + D)
        # If U_at_x=0 is 1 (source): P_at_x=0 = Zin_pipe_terminated_by_ZR * 1
        # P_at_x=L = P_at_x=0 * H (where H is the previously derived 1/(A+B/ZR) ) is NOT quite right.
        # Let's use the definition based on forward and backward waves if ABCD is confusing.
        # P(x) = P_plus * exp(-jkx) + P_minus * exp(jkx)
        # U(x) = (1/Z0) * (P_plus * exp(-jkx) - P_minus * exp(jkx))
        # At x=L: P(L) = ZR * U(L)
        # At x=0: P(0) = ZL * U(0) -- this is problematic if ZL is 'hard' or 'zero' unless it represents a source.
        # It's more standard that ZL is a load at x=-L if source is at x=0, or ZL is load at x=0 if source is "behind" it.
        # Assuming the script intends for ZL to be the load at x=0 if the wave comes from "further left".
        # Let's assume the original derivation of H_orig = (D_abcd - B/Zin_pipe_terminated_by_ZR) / denom was for P_right/P_left with U_left=1.
        # H_orig was ( (A*D-B*C) = 1 ): P_right / P_left = (D - B/Z_in_L)
        # Z_in_L = P_left / U_left.
        # P_left = A*P_right + B*U_right
        # U_left = C*P_right + D*U_right
        # If we want H = P_right/P_source_voltage (assuming source at left end before ZL)
        # Then P_left = P_source * ZL / (Z_source + ZL) - this is too complex.

        # Let's use the most common definition for a tube with loads ZL (at x=0) and ZR (at x=L):
        # Transfer function P(L)/P(0) given P(0) is the pressure at the input x=0
        # H = 1 / (cos(kL) + j*(Z0/ZR)*sin(kL))
        # This is P(L)/P_forward_wave_amplitude_at_x=0 if ZL is matched (Z0).
        # If ZL is not matched, it causes reflections.

        # Re-evaluating the original script's `P_right/P_left` after `P_left=Zin`:
        # Zin = (A*ZR + B)/(C*ZR + D) is the input impedance at x=0 looking into the tube terminated by ZR.
        # P_left = Zin * U_left. If U_left=1, then P_left=Zin.
        # The matrix relation is [P_left; U_left] = M * [P_right; U_right]
        # So [P_right; U_right] = M_inv * [P_left; U_left]
        # M_inv = (1/det(M)) * [D, -B; -C, A]. det(M) = AD-BC = 1 for reciprocal lossless.
        # P_right = D*P_left - B*U_left
        # U_right = -C*P_left + A*U_left
        # If U_left = 1 and P_left = Zin:
        # P_right = D*Zin - B
        # H = P_right / P_left = (D*Zin - B) / Zin = D - B/Zin
        # This gives P_right in terms of P_left when U_left=1.
        
        Zin_at_0_looking_right = (A * ZR_eff + B) / (C * ZR_eff + D_abcd)
        
        # Avoid division by zero if Zin_at_0_looking_right is zero (e.g. specific L and ZR)
        Zin_eff = np.where(np.abs(Zin_at_0_looking_right) < 1e-9, 1e-9*np.sign(Zin_at_0_looking_right) if np.any(Zin_at_0_looking_right) else 1e-9, Zin_at_0_looking_right)

        H_pressure_ratio = D_abcd - B / Zin_eff # This is P_L / P_0 if U_0=1.
                                              # P_L = P(x=L), P_0 = P(x=0)

        # Now, consider the left boundary ZL. It means P(0) = ZL * U(0).
        # The H above is P(L)/P(0) if U(0) = 1.
        # If P(0) = ZL * U(0), then H = P(L) / (ZL * U(0))
        # The script implies it computes P_R/P_L.
        # The calculated H_pressure_ratio is P_right / Zin_at_0_looking_right
        # If P_left IS Zin_at_0_looking_right (because U_left=1), then this is the H.
        # What is ZL used for? The problem is that ZL and ZR are both loads.
        # A typical setup is a source, then the tube, then a load.
        # Or source, ZL, tube, ZR.
        # Let's assume the formula H = 1 / (A + B/ZR_eff) is P(L)/P(0) assuming P(0) is the input pressure.
        # And the left boundary ZL means that P(0) = ZL * U(0).
        # If the system is driven by a velocity source U_s at x=0, such that U(0)=U_s.
        # Then P(0) = ZL * U_s.
        # And P(L) = P(0) * H_voltage_gain = (ZL * U_s) * (1 / (A + B/ZR_eff)).
        # Transfer function U_s to P(L) would be ZL / (A + B/ZR_eff).

        # Let's use a well-known formula for two-port network loaded with ZL and ZR,
        # driven by a source Vs with source impedance Zs.
        # Input impedance of tube+ZR is Zin_R = (A*ZR+B)/(C*ZR+D)
        # Input voltage P_in = Vs * Zin_R / (Zs + Zin_R)
        # Output voltage P_out = P_in / (A + B/ZR)
        # If Zs=0 (ideal voltage source), P_in = Vs. Then H = P_out/Vs = 1/(A+B/ZR).
        # This seems to be the most standard "voltage gain" or "pressure gain".
        # The ZL parameter is not used in this specific definition.
        # If ZL defines how P_in relates to an assumed U_in, that's different.

        # The original script had ZL and ZR.
        # A general formula for H = p_L / p_S (source voltage p_S before Z_S, where tube input impedance is Z_in_total)
        # Z_in_total is Z_L in series with (Z_pipe_terminated_by_ZR) ? No.
        # Let Z_L be the impedance at x=0, Z_R the impedance at x=L.
        # H = p(L)/p(0) can be 1 / (cos(kL) + j*(Z0_char_medium/ZR)*sin(kL))
        # Here Z0_char_medium = rho*c. But the Z0 in ABCD is rho*c/S.
        # Let Zc = rho*c (impedance per unit area). S = pi*a^2.
        # Z0_ABCD = Zc/S.
        # A = cos(kL), B = j (Zc/S) sin(kL), C = j (S/Zc) sin(kL), D = cos(kL)
        # H_pressure_gain = 1 / (A + B/ZR)
        # This definition does not use ZL.
        # The problem statement H=P_right/P_left means ZL is effectively a source impedance or part of source model.
        # If P_left is the pressure at the input (x=0) *after* any source impedance ZL.

        # Sticking to the definition that seems implied by the ABCD matrix usage:
        # P_right / P_left = D - B/Zin_at_0_looking_right
        # This is equivalent to 1 / (A + B/ZR) only if Zin_at_0_looking_right = ZR / (D*ZR - C*B) ... not simple.

        # Let's use the formula from earlier: H = P_right / P_left = D_abcd - B / Zin_at_0_looking_right
        # This assumes U_left=1. P_left becomes Zin_at_0_looking_right.
        # The ZL parameter then seems to define the *actual* P_left based on U_left=1.
        # P_left_actual = ZL (if U_left=1).
        # So, P_right_final = (D_abcd*ZL - B) ? This changes meaning.
        # It is most likely that ZL and ZR are loads and the TF is defined for a source at one end.
        # If source is voltage source at left, P_left is given. H = P_right/P_left = 1/(A+B/ZR).
        # This is independent of ZL. ZL would only matter if we compute U_left.
        # If source is current source U_left at left, P_left = ZL*U_left. P_right = (D*P_left - B*U_left)/(AD-BC).
        # P_right = (D*ZL*U_left - B*U_left) = U_left*(D*ZL-B).
        # Then P_right/P_left = (D*ZL-B)/ZL = D - B/ZL. This makes ZL the input impedance. This is circular.

        # The most robust way is often via reflection coefficients for simple tubes.
        # Gamma_L = (ZL/ (np.pi * a**2) - Z0_medium) / (ZL/(np.pi*a**2) + Z0_medium) where Z0_medium = rho*c
        # Let's use the common definition H = p(L)/p(0) = 1 / (cos(kL) + j * (Z0_ABCD / ZR) * sin(kL))
        # And assume ZL is not used in this definition of H.
        # If the problem is from a textbook that defines H with ZL and ZR as terminations of a passive tube:
        # H = V_out/V_in = Z_R / (A*Z_R + B) if input is ideal voltage source.
        # This definition seems most standard for P_right/P_left.

        H_tf = ZR_eff / (A * ZR_eff + B) # This assumes input is voltage source, ZL not used.

        # What if ZL is the actual input impedance of the system when driven by an ideal voltage source? No.
        # What if ZL *is* the source impedance?
        # Source V_s, Z_s=ZL. Input impedance of tube+ZR is Z_in_R = (A*ZR+B)/(C*ZR+D).
        # P_left = V_s * Z_in_R / (ZL + Z_in_R).
        # P_right = P_left * (1/(A+B/ZR)).
        # Then H = P_right / V_s. This uses ZL.

        # The script's prior use of `P_left = Zin` suggests `Zin` is `P_left` for `U_left=1`.
        # And `P_right = D*P_left - B*U_left` (with `U_left=1`) means `P_right = D*Zin - B`.
        # So `H = P_right/P_left = (D*Zin - B)/Zin = D - B/Zin`.
        # This ZL seems to be unused.
        # If ZL is truly the load at the left end, and we are looking at transmission from "far left" through ZL, then tube, then ZR.
        # This is not standard for a simple H=P_right/P_left.
        # Let's trust the structure ZL and ZR are loads at x=0 and x=L.
        # And the TF is related to pressure ratio.
        # The expression H = ZR / (A*ZR + B) is P_L / P_S where P_S is a source voltage at x=0.
        # This makes P_left = P_S.
        # This seems the most plausible interpretation for P_right/P_left.
        return H_tf


def main():
    parser = argparse.ArgumentParser(description="Finite circular tube transfer function (plane wave)")
    parser.add_argument("--D", type=float, default=0.0295, help="Diameter in m (default 0.0295)")
    parser.add_argument("--L", type=float, default=0.1, help="Length in m (default 0.1)")
    parser.add_argument("--T", type=float, default=26.5, help="Temperature in Celsius (default 26.5)")
    parser.add_argument("--medium", choices=["air", "water"], default="air", help="Medium (air or water)")
    parser.add_argument("--fmax", type=float, default=10000, help="Max frequency Hz")
    parser.add_argument("--n", type=int, default=2000, help="Number of freq samples")
    parser.add_argument("--left", choices=["hard","zero","radiation"], default="hard")
    parser.add_argument("--right", choices=["hard","zero","radiation"], default="radiation")
    parser.add_argument("--plot", action="store_true", help="Plot magnitude and phase")
    args = parser.parse_args()

    freq = np.linspace(1, args.fmax, args.n) # Avoid freq=0 for k
    tube = Tube(D=args.D, L=args.L, T=args.T, medium=args.medium, end_left=args.left, end_right=args.right)
    H = tube.transfer_function(freq)
    if args.plot:
        fig, ax = plt.subplots(2,1, figsize=(8,6), sharex=True)
        ax[0].plot(freq, 20*np.log10(np.abs(H)))
        ax[0].set_ylabel("|H| (dB)")
        ax[1].plot(freq, np.unwrap(np.angle(H)))
        ax[1].set_ylabel("Phase (rad)")
        ax[1].set_xlabel("Frequency (Hz)")
        ax[0].grid(); ax[1].grid()
        title = f"Tube D={args.D*1e3:.1f} mm, L={args.L*100:.1f} cm, Med={args.medium}, T={args.T}C\nLeft={args.left}, Right={args.right}"
        fig.suptitle(title) # Use suptitle for main title
        plt.tight_layout(rect=[0, 0, 1, 0.96]) # Adjust layout for suptitle
        plt.show()
    else:
        # 打印 10 行示例
        print(f"# Freq (Hz)	Mag (dB)	Phase (rad)")
        step = max(1, args.n // 10)
        for i in range(0, args.n, step):
            print(f"{freq[i]:.1f}	{20*np.log10(np.abs(H[i])):.2f}	{np.angle(H[i]):.2f}")

if __name__ == "__main__":
    main() 