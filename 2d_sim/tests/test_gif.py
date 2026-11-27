from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from PIL import Image, ImageChops


class FlightGifTest(unittest.TestCase):
    def test_cli_writes_animated_gif_from_another_directory(self):
        script = Path(__file__).resolve().parents[1] / "main.py"
        with TemporaryDirectory() as workdir:
            output = Path("Flug 2D") / "flug.gif"
            subprocess.run(
                [sys.executable, "-B", str(script), "--output", str(output)],
                cwd=workdir, check=True, stdout=subprocess.DEVNULL,
            )
            with Image.open(Path(workdir) / output) as gif:
                self.assertEqual(gif.format, "GIF")
                self.assertGreater(gif.n_frames, 1)
                start = gif.convert("RGB")
                gif.seek(gif.n_frames - 1)
                self.assertIsNotNone(ImageChops.difference(start, gif.convert("RGB")).getbbox())
