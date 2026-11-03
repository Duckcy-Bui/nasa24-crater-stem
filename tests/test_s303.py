"""S3-03: kiểm tra bản đếm lại và quy tắc vùng đếm (dữ liệu trong repo, không cần ảnh)."""

import unittest
from pathlib import Path

import numpy as np

from scripts.s303_kiem_tra import CORNER, THRESHOLDS, impact, shifted
from src.contracts import read_json
from src.statistics import binomial_two_sided_p, count_mask

ROOT = Path(__file__).resolve().parents[1]
COUNTS = ROOT / "data/s303_counts"
REGIONS = read_json(COUNTS / "regions.json")
CROPS = {iid: cfg for reg in REGIONS["regions"].values() for iid, cfg in reg["crops"].items()}


class Counts(unittest.TestCase):
    def test_ids_unique_and_centres_inside_crop(self):
        for iid in CROPS:
            circles = read_json(COUNTS / f"{iid}_count.json")["circles"]
            ids = [c["crater_id"] for c in circles]
            self.assertEqual(len(ids), len(set(ids)), iid)
            for c in circles:
                self.assertTrue(0 <= c["x"] <= 511 and 0 <= c["y"] <= 511 and c["r"] > 0, (iid, c))

    def test_no_two_counted_circles_are_the_same_crater(self):
        """Tâm vòng nhỏ nằm sát tâm vòng lớn cùng cỡ thì là một hố bị đếm hai lần."""
        for iid in CROPS:
            circles = read_json(COUNTS / f"{iid}_count.json")["circles"]
            for i, a in enumerate(circles):
                for b in circles[i + 1 :]:
                    big, small = max(a["r"], b["r"]), min(a["r"], b["r"])
                    d = np.hypot(a["x"] - b["x"], a["y"] - b["y"])
                    self.assertFalse(
                        d <= 0.5 * big and small / big >= 0.7,
                        (iid, a["crater_id"], b["crater_id"]),
                    )

    def test_same_rule_no_cluster_corner_removed_from_mare_frigoris_only(self):
        """Nhận xét PR #30: góc có cụm hố lớn phải được xử lý như nhau ở hai vùng."""
        c01 = count_mask(
            CROPS["moon_lunokhod1_loc_c01"]["keep"], CROPS["moon_lunokhod1_loc_c01"]["exclude"]
        )
        c03 = count_mask(
            CROPS["moon_marefrig_loc_c03"]["keep"], CROPS["moon_marefrig_loc_c03"]["exclude"]
        )
        x0, y0, x1, y1 = CORNER
        self.assertTrue(c01[y0:y1, x0:x1].all())
        self.assertTrue(
            c03[100:y1, 64:x1].all()
        )  # cụm hố lớn của Mare Frigoris nay nằm trong vùng đếm

    def test_rule_is_recorded_and_range_is_physical(self):
        self.assertIn("Quy tắc chung", REGIONS["rule"])
        self.assertEqual(REGIONS["d_range_m"], [300.0, 2000.0])


class Analysis(unittest.TestCase):
    def test_four_thresholds_are_sqrt2_steps(self):
        self.assertEqual([round(t) for t in THRESHOLDS], [300, 424, 600, 849])

    def test_shifted_radius_does_not_touch_input(self):
        crops = {"a": [{"crater_set": {"circles": [{"r": 5.0}]}}]}
        out = shifted(crops, 1.0)
        self.assertEqual(out["a"][0]["crater_set"]["circles"][0]["r"], 6.0)
        self.assertEqual(crops["a"][0]["crater_set"]["circles"][0]["r"], 5.0)

    def test_impact_finds_smallest_change_that_crosses_005(self):
        a = {"n_a": 73, "n_b": 43, "area_a": 184.7, "area_b": 123.0, "ratio": 1.13}
        b = {"n_a": 31, "n_b": 10, "area_a": 184.7, "area_b": 123.0, "ratio": 2.06}
        out = impact(a, b)
        add = out["tong"]["them_vao_L_de_p_nho_hon_0_05"]
        frac = 184.7 / 307.7
        self.assertLess(binomial_two_sided_p(73 + add, 73 + add + 43, frac), 0.05)
        self.assertGreaterEqual(binomial_two_sided_p(73 + add - 1, 73 + add - 1 + 43, frac), 0.05)

    def test_completeness_scales_ratio(self):
        a = {"n_a": 10, "n_b": 10, "area_a": 1.0, "area_b": 1.0, "ratio": 1.0}
        grid = impact(a, a)["luoi_do_day_du"]
        row = next(r for r in grid if r["do_day_du_L"] == 0.8 and r["do_day_du_M"] == 1.0)
        self.assertEqual(row["ty_so_tong_suy_ra"], 1.25)


if __name__ == "__main__":
    unittest.main()
