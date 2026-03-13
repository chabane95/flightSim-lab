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

def v_abs(vx, vz):
    return np.sqrt(vx**2 + vz**2)

def Fd_x(z ,vx, vz):
    rho_loc = rho_atm(z)
    return  (-0.5 * Cd * rho_loc * A * vx * v_abs(vx, vz))
 
def Fd_z(z,vx,vz):
    rho_loc = rho_atm(z)
    return (-0.5 * Cd * rho_loc * A * vz * v_abs(vx, vz))
    

def vxdot(vx, vz, m, t, z, theta):
    T = thrust(t, m, z) # thrust. 
    theta_rad = np.deg2rad(theta)
    return (T * np.sin(theta_rad) + Fd_x(z, vx, vz)) / m 

def vzdot(vx, vz, m, t, z, theta):
    T = thrust(t, m, z)
    theta_rad = np.deg2rad(theta)
    return (T * np.cos(theta_rad) - m * g + Fd_z(z, vx, vz)) / m

def euler_step(x, x_dot, dt):
    return x + dt * x_dot


def solver(x0, z0, vx0, vz0, m0, dt, max_iter):
    t = 0.0
    x = x0
    z = z0
    vx = vx0
    vz = vz0
    m = m0

    t_values = []
    x_values = []
    z_values = []
    vx_values = []
    vz_values = []
    m_values = []

    for _ in range(max_iter):
        x_dot = xdot(vx)
        z_dot = zdot(vz)
        m_dot = mdot(t, m)
        vx_dot = vxdot(vx, vz, m, t, z, theta)
        vz_dot = vzdot(vx, vz, m, t, z, theta)

        t_values.append(t)
        x_values.append(x)
        z_values.append(z)
        vx_values.append(vx)
        vz_values.append(vz)
        m_values.append(m)

        x_new = euler_step(x, x_dot, dt)
        z_new = euler_step(z, z_dot, dt)
        vx_new = euler_step(vx, vx_dot, dt)
        vz_new = euler_step(vz, vz_dot, dt)
        m_new = euler_step(m, m_dot, dt)

        x = x_new
        z = z_new
        vx = vx_new
        vz = vz_new
        m = max(m_dry, m_new)
        t = t + dt

        # Stop once it returns to ground.
        if z <= 0.0 and t > 0.5 and vz < 0.0:
            break

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
