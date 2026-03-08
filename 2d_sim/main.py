import numpy as np

g = 9.81
A = 0.02
rho = 1.225
Cd = 0.6
u_e = 250.0

beta = 0.5
t_b = 8.0

dt = 0.005
max_iter = 24000

z0 = 0.0
v0 = 0.0
m0 = 10.0

m_dry = 6.0
rho0 = 1.225      # kg/m^3 am Boden
H = 8500.0        # scale height [m]

p0 = 101325.0      # Pa
Ae = 0.003         # m^2, Beispiel
pe = 120000.0      # Pa, Beispielwert


def mdot(t, m):
    if m <= m_dry:
        return 0.0
    t_rise = 0.3
    t_fall = 0.5

    if t < 0.0 or t >= t_b:
        return 0.0
    elif t < t_rise:
        return -beta * (t / t_rise)
    elif t < t_b - t_fall:
        return -beta
    else:
        return -beta * ((t_b - t) / t_fall)


def xdot(vx):
    return vx
def zdot(vz):
    return vz

def rho_atm(z):
    # realistic atmospheric. 
    z_eff = max(0.0, z) # effektive height
    return rho0*np.exp(-z_eff/H) 


def p_atm(z):
    z_eff = max(0.0, z)
    return p0 * np.exp(-z_eff / H)
# better model for the thrust=Schub. 
def thrust(t, m, z):
    m_dot = mdot(t, m)
    if m_dot == 0.0:
        return 0.0
    momentum_thrust = -u_e * m_dot
    pressure_thrust = (pe - p_atm(z)) * Ae
    return momentum_thrust + pressure_thrust

def vxdot(v, m, t, z):
    T = thrust(t, m, z) # thrust. 
    rho_loc = rho_atm(z)
    drag = -0.5 * Cd * rho_loc * A * v * abs(v)
    return (T + drag - m * g) / m


def euler_step(x, x_dot, dt):
    return x + dt * x_dot


def solver(z0, v0, m0, dt, max_iter):
    t = 0.0
    z = z0
    v = v0
    m = m0

    t_values = []
    z_values = []
    v_values = []
    m_values = []

    for _ in range(max_iter):
        z_dot = zdot(v)
        m_dot = mdot(t, m)
        v_dot = vdot(v, m, t, z)

        t_values.append(t)
        z_values.append(z)
        v_values.append(v)
        m_values.append(m)

        z_new = euler_step(z, z_dot, dt)
        v_new = euler_step(v, v_dot, dt)
        m_new = euler_step(m, m_dot, dt)

        z = z_new
        v = v_new
        m = max(m_dry, m_new)
        t = t + dt

        # Stop once it returns to ground.
        if z <= 0.0 and t > 0.5 and v < 0.0:
            break

    return np.array(t_values), np.array(z_values), np.array(v_values), np.array(m_values)




def main():
    t, z, v, m = solver(z0, v0, m0, dt, max_iter)

if __name__ == "__main__":
    main()
