"""S2-13: giới hạn ứng viên và bằng chứng đếm tay, không đổi hợp đồng summarize."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from streamlit.testing.v1 import AppTest

from src import integration
from src.contracts import read_json

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = read_json(ROOT / "docs/evidence/s2-09/so_sanh.json")
REGIONS = read_json(ROOT / "data/s209_counts/regions.json")
META = read_json(ROOT / "data/processed/moon_lunokhod1_loc_c01.json")


class TestDensityLimit(unittest.TestCase):
    def test_raw_count_at_or_above_cap_is_limited(self):
        for count in (100, 101):
            view = integration.density_limit_view(count, 100)
            self.assertTrue(view["limited"])
            for text in ("max_circles = 100", "không dùng để so tuổi hay so vùng", "đếm tay"):
                self.assertIn(text, view["reason"])

    def test_under_cap_does_not_hide_density(self):
        self.assertEqual(integration.density_limit_view(99, 100), {"limited": False, "reason": None})


class TestDensityComparison(unittest.TestCase):
    def test_counted_crops_and_uncounted_same_source_crop(self):
        for key, region in EVIDENCE["regions"].items():
            for image_id in region["crops"]:
                meta = read_json(ROOT / "data/processed" / f"{image_id}.json")
                view = integration.density_comparison_view(meta)
                self.assertEqual(view["status"], "ok")
                self.assertEqual(view["region"], key)
                self.assertTrue(view["counted_crop"])
                self.assertEqual(view["data"], EVIDENCE)
        meta = read_json(ROOT / "data/processed/moon_marefrig_loc_c01.json")
        view = integration.density_comparison_view(meta)
        self.assertEqual(view["status"], "ok")
        self.assertEqual(view["region"], "marefrig")
        self.assertFalse(view["counted_crop"])

    def test_all_images_are_resolved_by_metadata_not_filename(self):
        manifest = read_json(ROOT / "data/s106_bundle/manifest.json")
        for image_id in manifest["image_ids"]:
            meta = read_json(ROOT / "data/processed" / f"{image_id}.json")
            products = {r["product_id"] for r in EVIDENCE["regions"].values()}
            view = integration.density_comparison_view(meta)
            self.assertEqual(view["status"], "ok" if meta["product_id"] in products else "hidden", image_id)
        renamed = dict(META, image_id="no_region_in_this_name")
        self.assertEqual(integration.density_comparison_view(renamed)["region"], "lunokhod1")
        spoofed = dict(META, product_id="unrelated_product")
        self.assertEqual(integration.density_comparison_view(spoofed)["status"], "error")
        for fields in ({"scale_m_per_px": 2}, {"body": "mars"}):
            self.assertEqual(integration.density_comparison_view(dict(META, **fields))["status"], "error")

    def test_missing_corrupt_and_inconsistent_files_are_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            evidence = Path(tmp) / "comparison.json"
            regions = Path(tmp) / "regions.json"
            regions.write_text(json.dumps(REGIONS), encoding="utf-8")
            def view():
                return integration.density_comparison_view(META, comparison_path=evidence, regions_path=regions)
            self.assertEqual(view()["status"], "error")
            for value in ("{broken", "null", "[]", '{"d_range_m": []}'):
                evidence.write_text(value, encoding="utf-8")
                self.assertEqual(view()["status"], "error", value)
            mutations = [
                ("n", -1), ("n", True), ("area_km2", 0), ("area_km2", float("nan")),
                ("density_per_km2", float("inf")), ("density_per_km2", 9),
                ("density_ci95_per_km2", [1, 0]), ("crops", []), ("d_range_m", [1, 2]),
            ]
            for field, value in mutations:
                bad = copy.deepcopy(EVIDENCE)
                bad["regions"]["lunokhod1"][field] = value
                evidence.write_text(json.dumps(bad), encoding="utf-8")
                self.assertEqual(view()["status"], "error", field)
            for field, value in (("binomial_p_two_sided", -0.1), ("binomial_p_two_sided", True),
                                 ("ratio_a_over_b", 2)):
                bad = copy.deepcopy(EVIDENCE)
                bad["comparison_lunokhod1_over_marefrig"][field] = value
                evidence.write_text(json.dumps(bad), encoding="utf-8")
                self.assertEqual(view()["status"], "error", field)
            evidence.write_text(json.dumps(EVIDENCE), encoding="utf-8")
            regions.write_text("{}", encoding="utf-8")
            self.assertEqual(view()["status"], "error")
            regions.unlink()
            self.assertEqual(view()["status"], "error")

    def test_file_is_read_again_at_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "comparison.json"
            path.write_text(json.dumps(EVIDENCE), encoding="utf-8")
            self.assertEqual(integration.density_comparison_view(META, comparison_path=path)["status"], "ok")
            path.write_text("broken", encoding="utf-8")
            self.assertEqual(integration.density_comparison_view(META, comparison_path=path)["status"], "error")


class TestDensityScreen(unittest.TestCase):
    def test_capped_density_is_hidden_even_after_filtering(self):
        # Interaction fixture: postprocessing retained three of one hundred raw candidates.
        code = """
import app
result = {'scored': {'machine': {}}, 'detected': {
    'valid_pixels': 512 * 512, 'raw_count': 100, 'hough': {'max_circles': 100}}}
app.show_statistics(result, {})
"""
        stats = {"count": 3, "valid_area_km2": 104.8576, "density_per_km2": 3 / 104.8576}
        with mock.patch("src.statistics.summarize", return_value=stats):
            at = AppTest.from_string(code).run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual({m.label: m.value for m in at.metric}["Mật độ"], "—")
        self.assertEqual(len(at.warning), 1)
        self.assertIn("không dùng để so tuổi hay so vùng", at.warning[0].value)

    def test_manual_comparison_is_rendered_without_scoring(self):
        code = f"import app\napp.show_density_comparison({META!r})\n"
        at = AppTest.from_string(code).run()
        self.assertEqual(len(at.exception), 0)
        rows = at.table[0].value.to_dict(orient="records")
        for row, region in zip(rows, EVIDENCE["regions"].values()):
            self.assertEqual(row["Số hố"], region["n"])
            self.assertEqual(row["Diện tích (km²)"], f"{region['area_km2']:.1f}")
            self.assertEqual(row["Mật độ (hố/km²)"], f"{region['density_per_km2']:.3f}")
        text = " ".join(m.value for m in at.markdown)
        comparison = EVIDENCE["comparison_lunokhod1_over_marefrig"]
        self.assertIn(f"{comparison['ratio_a_over_b']:.2f}", text)
        self.assertIn(f"{comparison['binomial_p_two_sided']:.2f}", text)
        self.assertIn("Không kết luận được vùng nào cổ hơn", at.info[0].value)

    def test_bad_file_is_a_gentle_message(self):
        with mock.patch("src.integration.Path.read_text", side_effect=OSError("test missing evidence")):
            at = AppTest.from_string(f"import app\napp.show_density_comparison({META!r})\n").run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(len(at.error), 0)
        self.assertIn("Chưa đọc được so sánh đếm tay", at.info[0].value)


if __name__ == "__main__":
    unittest.main()
