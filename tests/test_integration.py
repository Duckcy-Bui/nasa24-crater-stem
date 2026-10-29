"""S2-13: thống kê và thẻ khoa học được ghép vào app qua API đã thống nhất."""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from streamlit.testing.v1 import AppTest

from scripts.install_s106_dataset import install_dataset
from src.contracts import read_json
from src.integration import cards_view, statistics_view

ROOT = Path(__file__).resolve().parents[1]
METADATA = read_json(ROOT / "data" / "examples" / "s105_synthetic_512.json")
MACHINE = {"schema_version": "1.0", "data_kind": METADATA["data_kind"], "image_id": METADATA["image_id"],
           "source": "machine", "reference_source": None, "circles": []}
STATS = {"image_id": METADATA["image_id"], "count": 3, "valid_area_km2": 1.05, "density_per_km2": 2.86,
         "histogram": {"bin_edges_m": [20, 40, 80], "counts": [2, 1]}, "limitations": ["Ứng viên chưa kiểm chứng."]}
CARD = {"card_id": "A16-1", "title": "Apollo 16", "body": "Tàu đổ bộ năm 1972.", "source_title": "NASA",
        "source_url": "https://www.nasa.gov/mission/apollo-16/", "position": {"x": 200.0, "y": 300.0}}


class TestStatisticsView(unittest.TestCase):
    def test_real_statistics_follow_the_contract(self):
        """S2-09 đã cài: summarize thật phải qua kiểm tra hợp đồng của giao diện."""
        view = statistics_view(MACHINE, METADATA, 512 * 512)
        self.assertEqual(view["status"], "ok")
        self.assertEqual(view["data"]["count"], 0)
        self.assertGreater(view["data"]["valid_area_km2"], 0)

    def test_unimplemented_statistics_are_pending(self):
        with mock.patch("src.statistics.summarize", side_effect=NotImplementedError("chưa cài")):
            view = statistics_view(MACHINE, METADATA, 512 * 512)
        self.assertEqual(view["status"], "pending")
        self.assertIn("S2-09", view["reason"])

    def test_valid_statistics_pass_through_unchanged(self):
        with mock.patch("src.statistics.summarize", return_value=STATS) as summarize:
            view = statistics_view(MACHINE, METADATA, 1000)
        summarize.assert_called_once_with(MACHINE, METADATA, 1000)
        self.assertEqual(view, {"status": "ok", "data": STATS})

    def test_statistics_breaking_the_contract_are_reported(self):
        for bad in ({"count": -1}, {"count": 2, "density_per_km2": float("nan")},
                    {"count": 2, "histogram": {"bin_edges_m": [10, 5], "counts": [1]}},
                    {"count": 2, "histogram": {"bin_edges_m": [1, 2, 3], "counts": [1]}}, [1, 2]):
            with mock.patch("src.statistics.summarize", return_value=bad):
                self.assertEqual(statistics_view(MACHINE, METADATA, 1)["status"], "error", bad)
        with mock.patch("src.statistics.summarize", side_effect=ValueError("diện tích bằng 0")):
            view = statistics_view(MACHINE, METADATA, 0)
        self.assertEqual(view["status"], "error")
        self.assertIn("diện tích bằng 0", view["reason"])


class TestCardsView(unittest.TestCase):
    def test_cards_are_available_for_verified_regions(self):
        view = cards_view("moon_ap16_m102064759r_c01")
        self.assertEqual(view["status"], "ok")
        self.assertEqual(view["cards"][0]["card_id"], "apollo16-descartes-region")
        self.assertIsNone(view["cards"][0]["position"])

    def test_cards_without_source_or_outside_the_image_are_hidden(self):
        no_source = dict(CARD, card_id="B", source_url="")
        outside = dict(CARD, card_id="C", position={"x": 600, "y": 1})
        no_position = dict(CARD, card_id="D", position=None)
        with mock.patch("src.science_cards.cards_for_image", return_value=[CARD, no_source, outside, no_position]):
            view = cards_view("img")
        self.assertEqual([c["card_id"] for c in view["cards"]], ["A16-1", "D"])
        self.assertEqual(len(view["rejected"]), 2)
        self.assertTrue(view["rejected"][0].startswith("B:"))

    def test_non_list_result_is_an_error(self):
        with mock.patch("src.science_cards.cards_for_image", return_value={"cards": []}):
            self.assertEqual(cards_view("img")["status"], "error")


class TestIntegratedScreen(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.images = Path(cls.tmp.name) / "images"
        install_dataset(cls.images)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def app(self):
        code = (
            "from pathlib import Path\n"
            "import app\n"
            "from src.contracts import read_json\n"
            "from src.hough import resolve_hough_params\n"
            f"app.DATA_DIR = Path({str(self.images)!r})\n"
            f"app.SCORE_OUTPUT_DIR = Path({str(Path(self.tmp.name) / 'scores')!r})\n"
            f"app.REFERENCE_DIR = Path({str(Path(self.tmp.name) / 'no_labels')!r})\n"
            "def fake_machine(image_id, data_dir, stamp):\n"
            "    meta = read_json(Path(data_dir) / f'{image_id}.json')\n"
            "    machine = {'schema_version': '1.0', 'data_kind': meta['data_kind'], 'image_id': image_id,\n"
            "               'source': 'machine', 'reference_source': None, 'circles': []}\n"
            "    return {'machine': machine, 'hough': resolve_hough_params({}), 'postprocess': {'status': 'applied'},\n"
            "            'raw_count': 0, 'valid_pixels': 512 * 512, 'seconds': 0.1}\n"
            "app.machine_for_image = fake_machine\n"
            "app.code_version = lambda: 'test'\n"
            "app.main()\n"
        )
        return AppTest.from_string(code, default_timeout=30)

    def test_real_statistics_and_implemented_cards_are_shown(self):
        at = self.app().run()
        self.assertEqual(len(at.exception), 0)
        text = " ".join(m.value for m in at.markdown) + " ".join(c.value for c in at.caption)
        self.assertIn("Apollo 15", text)
        next(b for b in at.button if b.label == "Chấm bài").click().run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(len(at.error), 0)
        metrics = {m.label: m.value for m in at.metric}
        self.assertEqual(metrics["Số ứng viên"], "0")   # máy giả không trả vòng nào

    def test_pending_statistics_are_labelled(self):
        with mock.patch("src.statistics.summarize", side_effect=NotImplementedError("chưa cài")):
            at = self.app().run()
            next(b for b in at.button if b.label == "Chấm bài").click().run()
        self.assertEqual(len(at.exception), 0)
        self.assertTrue(any("S2-09" in i.value for i in at.info))

    def test_implemented_parts_are_shown(self):
        with mock.patch("src.statistics.summarize", return_value=STATS), \
                mock.patch("src.science_cards.cards_for_image", return_value=[CARD]):
            at = self.app().run()
            next(b for b in at.button if b.label == "Chấm bài").click().run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(len(at.error), 0)
        metrics = {m.label: m.value for m in at.metric}
        self.assertEqual(metrics["Số ứng viên"], "3")
        self.assertEqual(metrics["Mật độ"], "2.86 /km²")
        text = " ".join(m.value for m in at.markdown) + " ".join(c.value for c in at.caption)
        self.assertIn("Apollo 16", text)
        self.assertIn("https://www.nasa.gov/mission/apollo-16/", text)


if __name__ == "__main__":
    unittest.main()
