import numpy as np

def wind_x(z):
    return 0.0

def wind_z(z):
    return 0.0

def relative_velocity(z, vx, vz):
    vx_rel = vx - wind_x(z)
    vz_rel = vz - wind_z(z)
    return vx_rel, vz_rel

def rel_speed(z, vx, vz):
    vx_rel, vz_rel = relative_velocity(z, vx, vz)
    return np.sqrt(vx_rel**2 + vz_rel**2)