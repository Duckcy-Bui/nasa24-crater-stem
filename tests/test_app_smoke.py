"""S1-09 app startup, offline installation and corrupt-input integration checks."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image
from streamlit.testing.v1 import AppTest

from scripts.install_s106_dataset import install_dataset

ROOT = Path(__file__).resolve().parents[1]


class AppStartupTests(unittest.TestCase):
    def app_at(self, directory: Path):
        code = (
            "from pathlib import Path\n"
            "import app\n"
            f"app.DATA_DIR = Path({str(directory)!r})\n"
            "app.main()\n"
        )
        return AppTest.from_string(code, default_timeout=15)

    def test_missing_dataset_can_be_prepared_through_the_app(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "images"
            app = self.app_at(directory).run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(len(app.selectbox), 0)
            self.assertEqual(app.button[0].label, "Chuẩn bị bộ ảnh ngoại tuyến")
            app.button[0].click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(len(app.error), 0)
            self.assertEqual(len(app.selectbox), 1)
            self.assertEqual(len(app.selectbox[0].options), 26)
            self.assertEqual(len(list(directory.glob("*.png"))), 26)
            self.assertIn("player_drafts", app.session_state)

    def test_wrong_png_dimensions_show_error_instead_of_editable_canvas(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "images"
            install_dataset(directory)
            Image.new("L", (8, 8), 128).save(directory / "moon_ap15_hia_c01.png")
            app = self.app_at(directory).run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(len(app.error), 1)
            self.assertIn("PNG 512", app.error[0].value)
            self.assertFalse(any(b.label == "Lưu câu trả lời trên máy" for b in app.button))


if __name__ == "__main__":
    unittest.main()
