from pathlib import Path
import sys

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import main


def test_mdot_boundaries_and_profile():
    m_wet = main.m0
    m_dry = main.m_dry

    assert main.mdot(-0.1, m_wet) == 0.0
    assert main.mdot(main.t_b + 1e-6, m_wet) == 0.0
    assert main.mdot(1.0, m_dry) == 0.0

    mdot_start = main.mdot(0.0, m_wet)
    mdot_rise = main.mdot(0.15, m_wet)
    mdot_plateau = main.mdot(1.0, m_wet)
    mdot_fall = main.mdot(main.t_b - 0.25, m_wet)

    assert mdot_start == 0.0
    assert -main.beta < mdot_rise < 0.0
    assert np.isclose(mdot_plateau, -main.beta)
    assert -main.beta < mdot_fall < 0.0


def test_atmosphere_models_are_monotonic():
    assert np.isclose(main.rho_atm(0.0), main.rho0)
    assert np.isclose(main.p_atm(0.0), main.p0)

    z1 = 1000.0
    z2 = 5000.0
    assert main.rho_atm(z2) < main.rho_atm(z1) < main.rho_atm(0.0)
    assert main.p_atm(z2) < main.p_atm(z1) < main.p_atm(0.0)


def test_thrust_is_positive_in_burn_and_zero_outside():
    m_wet = main.m0

    t_mid_burn = 1.0
    t_after_burn = main.t_b + 0.1

    assert main.thrust(t_mid_burn, m_wet, 0.0) > 0.0
    assert main.thrust(t_after_burn, m_wet, 0.0) == 0.0
    assert main.thrust(t_mid_burn, main.m_dry, 0.0) == 0.0


def test_solver_outputs_are_finite_and_time_monotonic():
    t, z, v, m = main.solver(main.z0, main.v0, main.m0, main.dt, main.max_iter)

    assert len(t) > 10
    assert len(t) == len(z) == len(v) == len(m)
    assert np.all(np.isfinite(t))
    assert np.all(np.isfinite(z))
    assert np.all(np.isfinite(v))
    assert np.all(np.isfinite(m))
    assert np.all(np.diff(t) > 0.0)


def test_solver_enforces_dry_mass_and_ground_stop():
    t, z, v, m = main.solver(main.z0, main.v0, main.m0, main.dt, main.max_iter)

    assert np.all(m >= main.m_dry - 1e-12)
    # The solver stops after detecting ground crossing, but stores states
    # before the final integration step.
    assert z[-1] + main.dt * v[-1] <= 0.0
    assert t[-1] >= 0.5


def test_regression_ranges_for_current_parameter_set():
    t, z, v, m = main.solver(main.z0, main.v0, main.m0, main.dt, main.max_iter)

    apogee = float(np.max(z))
    max_speed = float(np.max(np.abs(v)))
    flight_time = float(t[-1])

    assert 300.0 < apogee < 900.0
    assert 40.0 < max_speed < 150.0
    assert 10.0 < flight_time < 60.0


if __name__ == "__main__":
    try:
        import pytest
    except ModuleNotFoundError:
        tests = [
            obj
            for name, obj in globals().items()
            if name.startswith("test_") and callable(obj)
        ]
        for test_fn in tests:
            test_fn()
        print(f"{len(tests)} tests passed (direct mode, without pytest).")
    else:
        raise SystemExit(pytest.main([__file__]))
