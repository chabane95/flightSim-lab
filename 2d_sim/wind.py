import numpy as np

# Referenzwerte
V_REF = 5.0      # m/s
Z_REF = 10.0     # m
Z0 = 0.5         # m  Rauigkeitslaenge
GUST_START = 1.5
GUST_DURATION = 2.5
GUST_AMPLITUDE = 1.5

def wind_mean_x(z):
    z_eff = max(0.0, z)
    numerator = np.log((z_eff + Z0) / Z0)
    denominator = np.log((Z_REF + Z0) / Z0)
    return V_REF * numerator / denominator

def wind_gust_x(t):
    if t < GUST_START or t > GUST_START + GUST_DURATION:
        return 0.0
    tau = (t - GUST_START) / GUST_DURATION
    return GUST_AMPLITUDE * np.sin(np.pi * tau)

def wind_x(z, t):
    return wind_mean_x(z) + wind_gust_x(t)

def wind_z(z, t):
    return 0.0

def relative_velocity(z, vx, vz, t):
    vx_rel = vx - wind_x(z, t)
    vz_rel = vz - wind_z(z, t)
    return vx_rel, vz_rel

def relative_speed(z, vx, vz, t):
    vx_rel, vz_rel = relative_velocity(z, vx, vz, t)
    return np.sqrt(vx_rel**2 + vz_rel**2)
