import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from replay import export_replay


class ReplayTest(unittest.TestCase):
    def test_subsampling_keeps_events_and_interpolated_last_frame(self):
        t = np.array([0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.057])
        z = np.array([0, 3, 9, 11, 10, 5, 0])
        flight = (t, t * 10, z, t + 1, t + 2, t + 3)
        with TemporaryDirectory() as temp:
            destination = Path(temp) / "viewer" / "flight-data.js"
            export_replay(destination, flight, burnout=0.02, dt=0.01)
            script = destination.read_text(encoding="utf-8")
            payload = json.loads(script.split("window.FLIGHT_DATA = ")[1].rstrip(";\n"))

        self.assertEqual(payload["burnout"], 0.02)
        self.assertEqual(payload["dt"], 0.01)
        expected = np.column_stack(flight)[[0, 2, 3, 5, 6]]
        np.testing.assert_allclose(payload["samples"], expected, rtol=0, atol=1e-6)
