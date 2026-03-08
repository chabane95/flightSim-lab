from pathlib import Path
import sys

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import main


def run_metrics(dt):
    t_max = main.max_iter * main.dt
    max_iter = int(t_max / dt)
    t, z, v, m = main.solver(main.z0, main.v0, main.m0, dt, max_iter)
    return {
        "apogee": float(np.max(z)),
        "vmax": float(np.max(np.abs(v))),
        "flight": float(t[-1]),
    }


def test_dt_refinement_improves_agreement_with_reference():
    ref = run_metrics(0.001)
    coarse = run_metrics(0.02)
    mid = run_metrics(0.005)

    err_coarse_ap = abs(coarse["apogee"] - ref["apogee"])
    err_mid_ap = abs(mid["apogee"] - ref["apogee"])

    err_coarse_v = abs(coarse["vmax"] - ref["vmax"])
    err_mid_v = abs(mid["vmax"] - ref["vmax"])

    err_coarse_t = abs(coarse["flight"] - ref["flight"])
    err_mid_t = abs(mid["flight"] - ref["flight"])

    assert err_mid_ap < err_coarse_ap
    assert err_mid_v < err_coarse_v
    assert err_mid_t <= err_coarse_t


def test_dt_scan_is_numerically_stable():
    dts = [0.02, 0.01, 0.005, 0.0025]
    results = [run_metrics(dt) for dt in dts]

    apogees = np.array([r["apogee"] for r in results], dtype=float)
    vmaxs = np.array([r["vmax"] for r in results], dtype=float)
    flights = np.array([r["flight"] for r in results], dtype=float)

    assert np.all(np.isfinite(apogees))
    assert np.all(np.isfinite(vmaxs))
    assert np.all(np.isfinite(flights))

    assert (np.max(apogees) - np.min(apogees)) < 5.0
    assert (np.max(vmaxs) - np.min(vmaxs)) < 1.0
    assert (np.max(flights) - np.min(flights)) < 0.1


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
