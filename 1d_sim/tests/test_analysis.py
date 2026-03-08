from pathlib import Path
import sys

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import main


def analyze_flight(t, z, v, m):
    burnout_idx = int(np.searchsorted(t, main.t_b, side="right") - 1)
    burnout_idx = max(0, min(burnout_idx, len(t) - 1))

    thrust_series = np.array(
        [main.thrust(ti, mi, zi) for ti, zi, mi in zip(t, z, m)], dtype=float
    )
    accel_series = np.array(
        [main.vdot(vi, mi, ti, zi) for ti, zi, vi, mi in zip(t, z, v, m)], dtype=float
    )
    rho_series = np.array([main.rho_atm(zi) for zi in z], dtype=float)
    q_series = 0.5 * rho_series * v * v

    return {
        "z_max": float(np.max(z)),
        "v_max": float(np.max(np.abs(v))),
        "t_burnout": float(t[burnout_idx]),
        "z_burnout": float(z[burnout_idx]),
        "v_burnout": float(v[burnout_idx]),
        "t_impact": float(t[-1]),
        "a_max": float(np.max(np.abs(accel_series))),
        "q_max": float(np.max(q_series)),
        "thrust_series": thrust_series,
        "q_series": q_series,
    }


def test_analyze_flight_extracts_core_metrics():
    t, z, v, m = main.solver(main.z0, main.v0, main.m0, main.dt, main.max_iter)
    out = analyze_flight(t, z, v, m)

    assert np.isfinite(out["z_max"])
    assert np.isfinite(out["v_max"])
    assert np.isfinite(out["t_impact"])
    assert np.isfinite(out["a_max"])
    assert np.isfinite(out["q_max"])

    assert np.isclose(out["z_max"], np.max(z))
    assert np.isclose(out["v_max"], np.max(np.abs(v)))
    assert out["t_burnout"] <= main.t_b + main.dt
    assert out["t_impact"] == t[-1]
    assert out["z_burnout"] > 0.0
    assert out["v_burnout"] > 0.0
    assert out["q_max"] > 0.0


def test_initial_acceleration_matches_force_balance():
    a_model = main.vdot(main.v0, main.m0, 0.0, main.z0)

    rho0 = main.rho_atm(main.z0)
    drag0 = -0.5 * main.Cd * rho0 * main.A * main.v0 * abs(main.v0)
    thrust0 = main.thrust(0.0, main.m0, main.z0)
    a_expected = (thrust0 + drag0 - main.m0 * main.g) / main.m0

    assert np.isclose(a_model, a_expected, rtol=0.0, atol=1e-12)


def test_post_burnout_state_is_physically_consistent():
    t, z, v, m = main.solver(main.z0, main.v0, main.m0, main.dt, main.max_iter)
    out = analyze_flight(t, z, v, m)

    post_mask = t >= (main.t_b + main.dt)
    assert np.any(post_mask)

    thrust_post = out["thrust_series"][post_mask]
    mass_post = m[post_mask]

    assert np.allclose(thrust_post, 0.0, atol=1e-12)
    assert np.allclose(np.diff(mass_post), 0.0, atol=1e-12)

    apogee_idx = int(np.argmax(z))
    assert abs(v[apogee_idx]) < 1.0
    assert np.any(v[apogee_idx:] <= 0.0)


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
