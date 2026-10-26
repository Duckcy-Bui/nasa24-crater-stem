"""S2-05: lọc vòng trùng trên bộ ví dụ data/examples/s205_dedupe_cases.json."""
import copy
import json
import unittest
from pathlib import Path

from src.contracts import read_json, validate_crater_set
from src.postprocessing import dedupe_circles, duplicate_pair, resolve_dedupe_params, vote_ratio

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "data/examples/s205_dedupe_cases.json").read_text(encoding="utf-8"))["cases"]


class DedupeCases(unittest.TestCase):
    def test_every_example_case(self):
        for case in CASES:
            with self.subTest(case=case["name"]):
                kept, removed, report = dedupe_circles(copy.deepcopy(case["circles"]))
                ids = [c["crater_id"] for c in kept]
                if "expect_kept" in case:
                    self.assertEqual(sorted(ids), sorted(case["expect_kept"]), report["pairs"])
                else:
                    self.assertEqual(len(ids), case["expect_kept_count"])
                self.assertEqual(len(kept) + len(removed), len(case["circles"]))
                for c in removed:
                    self.assertIn(c["duplicate_of"], ids)
                    self.assertTrue(c["dedupe_reason"])

    def test_no_case_that_must_keep_all_loses_a_circle(self):
        """Chống xóa quá mức: hố chạm mép, chồng mép, lồng nhỏ, cụm gần nhau."""
        for case in CASES:
            if case["kind"].startswith("không trùng"):
                kept, removed, _ = dedupe_circles(copy.deepcopy(case["circles"]))
                self.assertEqual(removed, [], case["name"])


class Rules(unittest.TestCase):
    def test_pair_geometry_thresholds(self):
        p = resolve_dedupe_params({})
        a = {"x": 0.0, "y": 0.0, "r": 10.0}
        self.assertTrue(duplicate_pair(a, {"x": 7.5, "y": 0.0, "r": 5.0}, p)[0])     # d = 0,75R, r/R = 0,5
        self.assertFalse(duplicate_pair(a, {"x": 7.6, "y": 0.0, "r": 6.0}, p)[0])    # d > 0,75R
        self.assertFalse(duplicate_pair(a, {"x": 1.0, "y": 0.0, "r": 4.9}, p)[0])    # r/R < 0,5

    def test_order_of_input_does_not_change_result(self):
        for case in CASES:
            fwd = dedupe_circles(copy.deepcopy(case["circles"]))[0]
            rev = dedupe_circles(copy.deepcopy(case["circles"][::-1]))[0]
            self.assertEqual(sorted(c["crater_id"] for c in fwd), sorted(c["crater_id"] for c in rev), case["name"])

    def test_vote_ratio_uses_hough_perimeter_count(self):
        self.assertAlmostEqual(vote_ratio({"r": 10.0, "votes": 40}), 0.5)   # 80 điểm chu vi ở r = 10
        self.assertIsNone(vote_ratio({"r": 10.0, "votes": None}))

    def test_kept_circles_unchanged_and_contract_valid(self):
        meta = read_json(ROOT / "data/examples/s105_synthetic_512.json")
        circles = [{"crater_id": f"M{i}", "x": x, "y": 200.0, "r": r, "confidence": None, "votes": v}
                   for i, (x, r, v) in enumerate(((200.0, 12.0, 60), (203.0, 9.0, 45), (300.0, 10.0, 50)), 1)]
        kept, removed, _ = dedupe_circles(copy.deepcopy(circles))
        self.assertEqual([c["crater_id"] for c in kept], ["M1", "M3"])
        self.assertEqual(kept[0], circles[0])
        validate_crater_set({"schema_version": "1.0", "data_kind": "synthetic", "image_id": meta["image_id"],
                             "source": "machine", "reference_source": None, "circles": kept}, meta)

    def test_bad_params_rejected(self):
        for bad in ({"radius": 1}, {"max_center_frac": 0}, {"min_radius_ratio": 1.5}, {"unreliable_classes": "texture"}):
            with self.assertRaises(ValueError):
                resolve_dedupe_params(bad)

    def test_empty_input(self):
        kept, removed, report = dedupe_circles([])
        self.assertEqual((kept, removed, report["n_removed"]), ([], [], 0))


if __name__ == "__main__":
    unittest.main()
