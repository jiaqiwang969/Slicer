#ifndef VTL_SOUNDSPEED_H
#define VTL_SOUNDSPEED_H

#include <cmath>

namespace vtl3d {

enum class Medium { Air, Sea, Helium };

// 空气声速 (m/s) – 改写理想气体近似公式 (T 摄氏)
inline double soundSpeedAir(double T)
{
    return 331.3 * std::sqrt(1.0 + T / 273.15);
}

// Mackenzie (1981) 海水声速 (m/s)
inline double soundSpeedSea(double T, double S = 35.0, double Z = 0.0)
{
    return 1448.96 + 4.591 * T - 5.304e-2 * T * T + 2.374e-4 * T * T * T +
           1.340 * (S - 35.0) + 1.630e-2 * Z + 1.675e-7 * Z * Z -
           1.025e-2 * T * (S - 35.0) - 7.139e-13 * T * Z * Z * Z;
}

// Helium声速 (m/s) – 理想气体公式 (γ=1.66, M=4.0026 g/mol)
inline double soundSpeedHelium(double T)
{
    constexpr double gamma = 1.66;
    constexpr double R_specific = 2077.0; // J/(kg·K)  = 8.314 / 0.0040026
    return std::sqrt(gamma * R_specific * (T + 273.15));
}

// 根据介质返回声速 (m/s)
inline double soundSpeed(double T, Medium m, double S = 35.0, double Z = 0.0)
{
    switch (m)
    {
    case Medium::Air:
        return soundSpeedAir(T);
    case Medium::Sea:
        return soundSpeedSea(T, S, Z);
    case Medium::Helium:
        return soundSpeedHelium(T);
    }
    return soundSpeedAir(T);
}

} // namespace vtl3d

#endif // VTL_SOUNDSPEED_H 