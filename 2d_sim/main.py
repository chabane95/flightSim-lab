import numpy as np

g = 9.81
A = 0.02
Cd = 0.6
u_e = 250.0

beta = 0.5
t_b = 8.0

dt = 0.005
max_iter = 24000

x0 = 0.0
z0 = 0.0
vx0 = 0.0
vz0 = 0.0
m0 = 10.0

m_dry = 6.0
rho0 = 1.225      # kg/m^3 am Boden
H = 8500.0        # scale height [m]

p0 = 101325.0      # Pa
Ae = 0.003         # m^2, Beispiel
pe = 120000.0      # Pa, Beispielwert

theta = 10 # grad from vertical
theta_rad = np.deg2rad(theta)

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


def rho_atm(z):
    # realistic atmospheric. 
    z_eff = max(0.0, z) # effektive height
    return rho0*np.exp(-z_eff/H) 


def p_atm(z):
    z_eff = max(0.0, z)
    return p0 * np.exp(-z_eff / H)

# better model for the thrust=Schub.
 
def thrust_from_mdot(m_dot, z):
    if m_dot == 0.0:
        return 0.0
    momentum_thrust = -u_e * m_dot
    pressure_thrust = (pe - p_atm(z)) * Ae
    return momentum_thrust + pressure_thrust

def rhs(t, y):
    # This function dy/dt = f(t,y) where y = (x, z, vx, vz, m)
    x, z, vx, vz, m = y

    m_eff = max(m_dry, m)
    m_dot = mdot(t, m_eff)
    T = thrust_from_mdot(m_dot, z)

    v = np.sqrt(vx**2 + vz**2)
    rho_loc = rho_atm(z)

    Fdx = -0.5 * Cd * rho_loc * A * vx * v
    Fdz = -0.5 * Cd * rho_loc * A * vz * v

    dxdt = vx
    dzdt = vz
    dvxdt = (T * np.sin(theta_rad) + Fdx) / m_eff
    dvzdt = (T * np.cos(theta_rad) + Fdz) / m_eff - g
    dmdt = m_dot

    return np.array([dxdt, dzdt, dvxdt, dvzdt, dmdt], dtype=float)

def rk4_step(t, y, dt):
    k1 = rhs(t, y)
    k2 = rhs(t + 0.5 * dt, y + 0.5 * dt * k1)
    k3 = rhs(t + 0.5 * dt, y + 0.5 * dt * k2)
    k4 = rhs(t + dt, y + dt * k3)
    return y + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)


def solver(x0, z0, vx0, vz0, m0, dt, max_iter):
    t = 0.0
    y = np.array([x0, z0, vx0, vz0, m0], dtype=float)

    t_values = []
    x_values = []
    z_values = []
    vx_values = []
    vz_values = []
    m_values = []

    for _ in range(max_iter):
        x, z, vx, vz, m = y

        t_values.append(t)
        x_values.append(x)
        z_values.append(z)
        vx_values.append(vx)
        vz_values.append(vz)
        m_values.append(m)

        y_new = rk4_step(t, y, dt)
        y_new[4] = max(m_dry, y_new[4])
        t_new = t + dt

        # Stop once it returns to ground.
        if y[1] > 0.0 and y_new[1] <= 0.0 and t_new > 0.5 and y_new[3] < 0.0:
            alpha = y[1] / (y[1] - y_new[1])
            alpha = float(np.clip(alpha, 0.0, 1.0))
            y_impact = y + alpha * (y_new - y)
            y_impact[1] = 0.0
            y_impact[4] = max(m_dry, y_impact[4])
            t_impact = t + alpha * dt

            t_values.append(t_impact)
            x_values.append(y_impact[0])
            z_values.append(y_impact[1])
            vx_values.append(y_impact[2])
            vz_values.append(y_impact[3])
            m_values.append(y_impact[4])
            break

        y = y_new
        t = t_new

    return (
        np.array(t_values),
        np.array(x_values),
        np.array(z_values),
        np.array(vx_values),
        np.array(vz_values),
        np.array(m_values),
    )




def main():
    import animation
    # solving vector. 
    t, x, z, vx, vz, m = solver(x0, z0, vx0, vz0, m0, dt, max_iter)
    _ani = animation.animate_rocket(dt, t, x, z, vx, vz, m)

if __name__ == "__main__":
    main()
