"""S2-08: lượt chấm bài, ảnh đối chiếu, lưu lượt và màn hình kết quả (không chạy Hough thật)."""
import io
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image
from streamlit.testing.v1 import AppTest

from scripts.install_s106_dataset import install_dataset
from src.contracts import ContractError, read_json
from src.game_results import radius_scope, render_overlay, save_round, score_round
from src.hough import resolve_hough_params

ROOT = Path(__file__).resolve().parents[1]
METADATA = read_json(ROOT / "data" / "examples" / "s105_synthetic_512.json")
HOUGH = resolve_hough_params({})


def machine_set(metadata, circles):
    return {"schema_version": "1.0", "data_kind": metadata["data_kind"], "image_id": metadata["image_id"],
            "source": "machine", "reference_source": None,
            "circles": [{"crater_id": f"M{i}", "x": x, "y": y, "r": r, "confidence": None, "votes": 20}
                        for i, (x, y, r) in enumerate(circles, 1)]}


class TestScoreRound(unittest.TestCase):
    def setUp(self):
        self.machine = machine_set(METADATA, [(100.0, 100.0, 20.0), (300.0, 300.0, 12.0)])
        self.player = [{"crater_id": "U1", "x": 102.0, "y": 99.0, "r": 18.0}]

    def test_radius_scope_reports_clamped_range_and_grid(self):
        scope = radius_scope(METADATA, HOUGH)
        lo, hi = scope["searched_px"]
        self.assertEqual(scope["radii"], hi - lo + 1)
        self.assertFalse(scope["sparse"])
        sparse = radius_scope(METADATA, {**HOUGH, "radius_step_px": 10})
        self.assertTrue(sparse["sparse"])
        self.assertEqual(sparse["radii"], len(range(lo, hi + 1, 10)))
        self.assertLessEqual(sparse["last_radius_px"], hi)

    def test_round_scores_player_and_keeps_machine_unchanged(self):
        before = json.dumps(self.machine)
        scored = score_round(self.player, METADATA, self.machine, HOUGH, None, {})
        self.assertEqual(json.dumps(self.machine), before)
        self.assertEqual(scored["score"]["vs_machine"]["matched"], 1)
        self.assertIsNone(scored["score"]["score"])
        self.assertEqual(scored["player"]["source"], "player")

    def test_invalid_player_circle_is_rejected(self):
        with self.assertRaises(ContractError):
            score_round([{"crater_id": "U1", "x": 900.0, "y": 1.0, "r": 5.0}], METADATA, self.machine, HOUGH, None, {})

    def test_save_round_writes_a_new_complete_directory_each_time(self):
        scored = score_round(self.player, METADATA, self.machine, HOUGH, None, {})
        with tempfile.TemporaryDirectory() as tmp:
            first = save_round(tmp, METADATA, scored, config={"hough": HOUGH}, code_version="test")
            second = save_round(tmp, METADATA, scored, config={"hough": HOUGH}, code_version="test")
            self.assertNotEqual(first, second)
            for name in ("metadata.json", "params.json", "craters.json", "run.json", "machine.json", "score.json"):
                self.assertTrue((first / name).is_file(), name)
            self.assertFalse((first / "reference.json").exists())
            params = read_json(first / "params.json")
            self.assertEqual(params["radius_scope"], scored["scope"])
            self.assertEqual(read_json(first / "run.json")["image_id"], METADATA["image_id"])
            self.assertEqual(read_json(first / "score.json")["vs_machine"]["matched"], 1)

    def test_overlay_is_a_larger_png_with_drawn_circles(self):
        buffer = io.BytesIO()
        Image.new("L", (512, 512), 40).save(buffer, format="PNG")
        scored = score_round(self.player, METADATA, self.machine, HOUGH, None, {})
        with Image.open(io.BytesIO(render_overlay(buffer.getvalue(), scored))) as picture:
            self.assertEqual(picture.size, (1024, 1024))
            self.assertNotEqual(picture.getpixel((2 * 100 + 2 * 20, 2 * 100)), (40, 40, 40))  # machine ring
            self.assertEqual(picture.getpixel((10, 10)), (40, 40, 40))


class TestResultsScreen(unittest.TestCase):
    """Màn hình kết quả trong app, thay Hough bằng ứng viên cố định cho nhanh."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.images = Path(cls.tmp.name) / "images"
        install_dataset(cls.images)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def app(self, scores: Path):
        code = (
            "from pathlib import Path\n"
            "import app\n"
            "from src.contracts import read_json\n"
            "from src.hough import resolve_hough_params\n"
            f"app.DATA_DIR = Path({str(self.images)!r})\n"
            f"app.SCORE_OUTPUT_DIR = Path({str(scores)!r})\n"
            "def fake_machine(image_id, data_dir, stamp):\n"
            "    meta = read_json(Path(data_dir) / f'{image_id}.json')\n"
            "    circles = [{'crater_id': 'M1', 'x': 100.0, 'y': 100.0, 'r': 20.0, 'confidence': None, 'votes': 30}]\n"
            "    machine = {'schema_version': '1.0', 'data_kind': meta['data_kind'], 'image_id': image_id,\n"
            "               'source': 'machine', 'reference_source': None, 'circles': circles}\n"
            "    return {'machine': machine, 'hough': resolve_hough_params({}), 'postprocess': {'status': 'applied'},\n"
            "            'raw_count': 1, 'valid_pixels': 512 * 512, 'seconds': 0.1}\n"
            "app.machine_for_image = fake_machine\n"
            "app.code_version = lambda: 'test'\n"
            "app.main()\n"
        )
        return AppTest.from_string(code, default_timeout=30)

    def test_scoring_shows_machine_agreement_and_saves_a_round(self):
        with tempfile.TemporaryDirectory() as tmp:
            scores = Path(tmp) / "scores"
            at = self.app(scores).run()
            self.assertEqual(len(at.exception), 0)
            image_id = at.selectbox[0].value
            at.session_state["player_drafts"] = {image_id: {"revision": 1, "circles": [
                {"crater_id": "U1", "x": 101.0, "y": 100.0, "r": 19.0, "confidence": None, "votes": None}]}}
            button = next(b for b in at.button if b.label == "Chấm bài")
            button.click().run()
            self.assertEqual(len(at.exception), 0)
            self.assertEqual(len(at.error), 0)
            metrics = {m.label: m.value for m in at.metric}
            self.assertEqual(metrics["Trùng máy"], "1")
            self.assertEqual(metrics["Chỉ bạn khoanh"], "0")
            self.assertTrue(any("Chưa có điểm" in i.value for i in at.info))
            saved = list(scores.iterdir())
            self.assertEqual(len(saved), 1)
            self.assertEqual(read_json(saved[0] / "craters.json")["circles"][0]["crater_id"], "U1")
            self.assertEqual(read_json(saved[0] / "score.json")["image_id"], image_id)

    def test_editing_after_scoring_warns_that_the_result_is_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            at = self.app(Path(tmp) / "scores").run()
            image_id = at.selectbox[0].value
            next(b for b in at.button if b.label == "Chấm bài").click().run()
            at.session_state["player_drafts"][image_id]["revision"] = 5
            at.run()
            self.assertTrue(any("chấm lại" in w.value for w in at.warning))


if __name__ == "__main__":
    unittest.main()
