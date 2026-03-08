from contextlib import contextmanager
from pathlib import Path
import sys

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import main


@contextmanager
def override_globals(**kwargs):
    old = {name: getattr(main, name) for name in kwargs}
    try:
        for name, value in kwargs.items():
            setattr(main, name, value)
        yield
    finally:
        for name, value in old.items():
            setattr(main, name, value)


def run_apogee_and_vmax():
    t, z, v, m = main.solver(main.z0, main.v0, main.m0, main.dt, main.max_iter)
    return float(np.max(z)), float(np.max(np.abs(v)))


def test_higher_dry_mass_reduces_performance():
    with override_globals(m_dry=6.0):
        z_low, v_low = run_apogee_and_vmax()
    with override_globals(m_dry=7.0):
        z_high, v_high = run_apogee_and_vmax()

    assert z_high < z_low
    assert v_high < v_low


def test_higher_beta_increases_performance_in_current_range():
    with override_globals(beta=0.4):
        z_low, v_low = run_apogee_and_vmax()
    with override_globals(beta=0.6):
        z_high, v_high = run_apogee_and_vmax()

    assert z_high > z_low
    assert v_high > v_low


def test_higher_exhaust_velocity_increases_performance():
    with override_globals(u_e=200.0):
        z_low, v_low = run_apogee_and_vmax()
    with override_globals(u_e=300.0):
        z_high, v_high = run_apogee_and_vmax()

    assert z_high > z_low
    assert v_high > v_low


def test_larger_reference_area_reduces_apogee():
    with override_globals(A=0.01):
        z_low_drag, _ = run_apogee_and_vmax()
    with override_globals(A=0.03):
        z_high_drag, _ = run_apogee_and_vmax()

    assert z_high_drag < z_low_drag


def test_larger_drag_coefficient_reduces_apogee():
    with override_globals(Cd=0.4):
        z_low_drag, _ = run_apogee_and_vmax()
    with override_globals(Cd=0.8):
        z_high_drag, _ = run_apogee_and_vmax()

    assert z_high_drag < z_low_drag


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
