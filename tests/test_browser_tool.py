"""CLI của công cụ browser tùy chọn không cần Playwright cho --help hoặc từ chối --out cũ."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_s213_app.py"


class TestBrowserToolCLI(unittest.TestCase):
    def test_help_works_without_launching_a_browser(self):
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), "--help"], cwd=ROOT,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--out", result.stdout)

    def test_existing_output_is_rejected_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "existing"
            out.mkdir()
            sentinel = out / "browser_results.json"
            sentinel.write_bytes(b"keep previous evidence\n")
            before = {p.name: p.read_bytes() for p in out.iterdir()}
            result = subprocess.run([sys.executable, "-B", str(SCRIPT), "--out", str(out)], cwd=ROOT,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("không ghi đè minh chứng", result.stderr)
            self.assertEqual({p.name: p.read_bytes() for p in out.iterdir()}, before)


if __name__ == "__main__":
    unittest.main()
