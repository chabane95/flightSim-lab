import numpy as np
import wind

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
p0 = 101325.0      # Pa
T0 = 288.15        # K
R_air = 287.05     # J/(kg K)
gamma_air = 1.4
lapse_rate = 0.0065
troposphere_top = 11000.0
T_tropopause = T0 - lapse_rate * troposphere_top
P_tropopause = p0 * (T_tropopause / T0) ** (g / (R_air * lapse_rate))

Ae = 0.003         # m^2, Beispiel
pe = 120000.0      # Pa, Beispielwert

theta = 10.0  # degrees from vertical, positive toward +x
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


def atmosphere_state(z):
    z_eff = max(0.0, z)

    if z_eff <= troposphere_top:
        temperature = T0 - lapse_rate * z_eff
        pressure = p0 * (temperature / T0) ** (g / (R_air * lapse_rate))
    else:
        temperature = T_tropopause
        pressure = P_tropopause * np.exp(
            -g * (z_eff - troposphere_top) / (R_air * temperature)
        )

    density = pressure / (R_air * temperature)
    sound_speed = np.sqrt(gamma_air * R_air * temperature)
    return {
        "temperature": temperature,
        "pressure": pressure,
        "density": density,
        "sound_speed": sound_speed,
    }


def temperature_atm(z):
    return atmosphere_state(z)["temperature"]


def rho_atm(z):
    return atmosphere_state(z)["density"]


def p_atm(z):
    return atmosphere_state(z)["pressure"]


def sound_speed_atm(z):
    return atmosphere_state(z)["sound_speed"]


def drag_coefficient(mach):
    if mach < 0.8:
        return Cd
    if mach < 1.05:
        alpha = (mach - 0.8) / 0.25
        return Cd + alpha * (0.9 - Cd)
    if mach < 1.3:
        alpha = (mach - 1.05) / 0.25
        return 0.9 + alpha * (0.75 - 0.9)
    if mach < 2.0:
        alpha = (mach - 1.3) / 0.7
        return 0.75 + alpha * (0.6 - 0.75)
    return 0.6

# better model for the thrust=Schub.
 
def thrust_from_mdot(m_dot, z, pressure=None):
    if m_dot == 0.0:
        return 0.0
    if pressure is None:
        pressure = p_atm(z)
    momentum_thrust = -u_e * m_dot
    pressure_thrust = (pe - pressure) * Ae
    return momentum_thrust + pressure_thrust


def diagnostics_snapshot(t, y):
    _, z, vx, vz, m = y

    m_eff = max(m_dry, m)
    m_dot = mdot(t, m_eff)
    atmosphere = atmosphere_state(z)
    temperature = atmosphere["temperature"]
    pressure = atmosphere["pressure"]
    rho_loc = atmosphere["density"]
    sound_speed = atmosphere["sound_speed"]
    thrust = thrust_from_mdot(m_dot, z, pressure=pressure)

    wind_x = wind.wind_x(z, t)
    wind_z = wind.wind_z(z, t)
    vx_air, vz_air = wind.relative_velocity(z, vx, vz, t)
    v_air = np.sqrt(vx_air * vx_air + vz_air * vz_air)
    q = 0.5 * rho_loc * v_air * v_air
    v_abs = np.sqrt(vx * vx + vz * vz)
    mach = 0.0 if sound_speed <= 0.0 else v_air / sound_speed
    cd_local = drag_coefficient(mach)

    return {
        "m_eff": m_eff,
        "m_dot": m_dot,
        "thrust": thrust,
        "temperature": temperature,
        "pressure": pressure,
        "rho": rho_loc,
        "sound_speed": sound_speed,
        "wind_x": wind_x,
        "wind_z": wind_z,
        "vx_air": vx_air,
        "vz_air": vz_air,
        "v_rel": v_air,
        "q": q,
        "v_abs": v_abs,
        "mach": mach,
        "Cd": cd_local,
    }


def record_diagnostics(diagnostics, t, y):
    if diagnostics is None:
        return

    state = diagnostics_snapshot(t, y)
    diagnostics["v_rel"].append(state["v_rel"])
    diagnostics["q"].append(state["q"])
    diagnostics["wind_x"].append(state["wind_x"])
    diagnostics["wind_z"].append(state["wind_z"])
    diagnostics["thrust"].append(state["thrust"])
    diagnostics["v_abs"].append(state["v_abs"])
    diagnostics["temperature"].append(state["temperature"])
    diagnostics["pressure"].append(state["pressure"])
    diagnostics["rho"].append(state["rho"])
    diagnostics["sound_speed"].append(state["sound_speed"])
    diagnostics["m_dot"].append(state["m_dot"])
    diagnostics["mach"].append(state["mach"])
    diagnostics["Cd"].append(state["Cd"])

def rhs(t, y):
    # This function dy/dt = f(t,y) where y = (x, z, vx, vz, m)
    x, z, vx, vz, m = y

    state = diagnostics_snapshot(t, y)
    m_eff = state["m_eff"]
    m_dot = state["m_dot"]
    T = state["thrust"]
    rho_loc = state["rho"]
    vx_air = state["vx_air"]
    vz_air = state["vz_air"]
    v_air = state["v_rel"]
    cd_local = state["Cd"]

    Fdx = -0.5 * cd_local * rho_loc * A * vx_air * v_air
    Fdz = -0.5 * cd_local * rho_loc * A * vz_air * v_air

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


def solver(x0, z0, vx0, vz0, m0, dt, max_iter, return_diagnostics=False):
    t = 0.0
    y = np.array([x0, z0, vx0, vz0, m0], dtype=float)

    t_values = []
    x_values = []
    z_values = []
    vx_values = []
    vz_values = []
    m_values = []
    diagnostics = None

    if return_diagnostics:
        diagnostics = {
            "v_rel": [],
            "q": [],
            "wind_x": [],
            "wind_z": [],
            "thrust": [],
            "v_abs": [],
            "temperature": [],
            "pressure": [],
            "rho": [],
            "sound_speed": [],
            "m_dot": [],
            "mach": [],
            "Cd": [],
        }

    for _ in range(max_iter):
        x, z, vx, vz, m = y

        t_values.append(t)
        x_values.append(x)
        z_values.append(z)
        vx_values.append(vx)
        vz_values.append(vz)
        m_values.append(m)
        record_diagnostics(diagnostics, t, y)

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
            record_diagnostics(diagnostics, t_impact, y_impact)
            break

        y = y_new
        t = t_new

    result = (
        np.array(t_values),
        np.array(x_values),
        np.array(z_values),
        np.array(vx_values),
        np.array(vz_values),
        np.array(m_values),
    )

    if diagnostics is None:
        return result

    diagnostics = {
        key: np.array(values, dtype=float)
        for key, values in diagnostics.items()
    }
    return result + (diagnostics,)




def main():
    import animation
    # solving vector. 
    t, x, z, vx, vz, m, diagnostics = solver(
        x0,
        z0,
        vx0,
        vz0,
        m0,
        dt,
        max_iter,
        return_diagnostics=True,
    )
    _ani = animation.animate_rocket(dt, t, x, z, vx, vz, m)
    return diagnostics

if __name__ == "__main__":
    main()
