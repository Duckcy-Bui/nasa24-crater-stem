"""S2-09: đếm hố, mật độ trên diện tích, so hai vùng (dữ liệu dựng tay, không phải ảnh NASA)."""
import copy
import math
import unittest
from pathlib import Path

import numpy as np

from src.contracts import read_json
from src.statistics import (binomial_two_sided_p, compare_regions, count_mask, poisson_interval, region_count,
                            size_frequency, sqrt2_bins, summarize)

ROOT = Path(__file__).resolve().parents[1]


def meta(image_id="a", x0=0, y0=0, scale=20.0, product="P1"):
    m = read_json(ROOT / "data/examples/s105_synthetic_512.json")
    m.update(image_id=image_id, crop_x0=x0, crop_y0=y0, scale_m_per_px=scale, product_id=product)
    m["radius"].update(d_min_m=200.0, d_max_m=4000.0, r_min_px=max(5, math.ceil(200 / (2 * scale))),
                       r_max_px=min(128, math.floor(4000 / (2 * scale))))
    return m


def craters(image_id, xyr):
    return {"schema_version": "1.0", "data_kind": "synthetic", "image_id": image_id, "source": "catalogue",
            "reference_source": "test", "circles": [{"crater_id": f"K{i}", "x": float(x), "y": float(y), "r": float(r),
                                                     "confidence": None, "votes": None} for i, (x, y, r) in enumerate(xyr)]}


def crop(image_id, xyr, x0=0, y0=0, rects=((0, 0, 512, 512),), scale=20.0, product="P1"):
    return {"metadata": meta(image_id, x0, y0, scale, product), "crater_set": craters(image_id, xyr),
            "mask": count_mask([list(r) for r in rects]), "valid": None}


class Stats(unittest.TestCase):
    def test_poisson_interval_matches_tables(self):
        # Bảng Garwood 95 %: n=0 → [0, 3,689]; n=10 → [4,795, 18,390]
        lo, hi = poisson_interval(0); self.assertEqual(lo, 0.0); self.assertAlmostEqual(hi, 3.689, places=3)
        lo, hi = poisson_interval(10); self.assertAlmostEqual(lo, 4.795, places=3); self.assertAlmostEqual(hi, 18.390, places=2)

    def test_binomial_p(self):
        self.assertAlmostEqual(binomial_two_sided_p(25, 50, 0.5), 1.0)
        self.assertLess(binomial_two_sided_p(45, 50, 0.5), 1e-6)

    def test_sqrt2_bins_start_at_dmin(self):
        e = sqrt2_bins(300, 2000)
        self.assertEqual(e[0], 300); self.assertEqual(e[-1], 2000)
        self.assertAlmostEqual(e[1] / e[0], math.sqrt(2))


class RegionCount(unittest.TestCase):
    def test_density_is_count_over_area_in_km2(self):
        r = region_count([crop("a", [(100, 100, 10), (300, 300, 20)])], 300, 2000)
        self.assertEqual(r["n"], 2)
        self.assertAlmostEqual(r["area_km2"], 512 * 512 * 400 / 1e6)
        self.assertAlmostEqual(r["density_per_km2"], 2 / r["area_km2"])

    def test_diameter_range_uses_physical_metres(self):
        # r = 7 px ở 20 m/px → D = 280 m < 300 m: không đếm; r = 50 → D = 2000 m: biên trên không đếm.
        r = region_count([crop("a", [(100, 100, 7), (200, 200, 7.5), (300, 300, 50)])], 300, 2000)
        self.assertEqual(r["n"], 1)

    def test_only_centres_inside_count_mask(self):
        r = region_count([crop("a", [(100, 100, 10), (400, 100, 10)], rects=((0, 0, 256, 512),))], 300, 2000)
        self.assertEqual(r["n"], 1)
        self.assertAlmostEqual(r["area_km2"], 256 * 512 * 400 / 1e6)

    def test_overlapping_crops_counted_once(self):
        a = crop("a", [(100, 400, 10)], x0=0, y0=0)
        b = crop("b", [(100, 10, 10)], x0=0, y0=390)          # cùng hố trên ảnh nguồn (y nguồn 400)
        r = region_count([a, b], 300, 2000)
        self.assertEqual(r["n"], 1)
        self.assertEqual(r["merged_across_crops"], 1)
        self.assertEqual(r["area_px"], 512 * (390 + 512))      # diện tích theo hợp, không cộng hai lần

    def test_mixed_scale_or_source_rejected(self):
        with self.assertRaises(ValueError):
            region_count([crop("a", []), crop("b", [], scale=2.0)], 300, 2000)
        with self.assertRaises(ValueError):
            region_count([crop("a", []), crop("b", [], product="P2")], 300, 2000)


class Compare(unittest.TestCase):
    def test_compare_requires_same_scale_and_range(self):
        a = region_count([crop("a", [(100, 100, 10)])], 300, 2000)
        b = region_count([crop("b", [(100, 100, 10)], product="P2")], 300, 2000)
        self.assertAlmostEqual(compare_regions(a, b)["ratio_a_over_b"], 1.0)
        c = region_count([crop("c", [(100, 100, 10)], product="P3")], 200, 2000)
        with self.assertRaises(ValueError):
            compare_regions(a, c)

    def test_size_frequency_counts_sum_to_n(self):
        r = region_count([crop("a", [(50, 50, 8), (150, 150, 12), (250, 250, 20), (350, 350, 40)])], 300, 2000)
        s = size_frequency(r)
        self.assertEqual(sum(s["counts"]), r["n"])
        self.assertEqual(s["cumulative"][0]["n"], r["n"])

    def test_summarize_follows_s213_contract(self):
        from src.integration import _check_statistics
        m = meta("a")
        s = summarize(craters("a", [(100, 100, 10), (200, 200, 6), (300, 300, 5)]), m, 512 * 512)
        self.assertIsNone(_check_statistics(s))            # đúng hợp đồng giao diện
        self.assertEqual(s["count"], 3)
        self.assertAlmostEqual(s["valid_area_km2"], 512 * 512 * 400 / 1e6)
        self.assertEqual(sum(s["histogram"]["counts"]), 3)
        self.assertEqual(s["histogram"]["bin_edges_m"][0], 200.0)   # bắt đầu tại d_min của metadata

    def test_summarize_zero_area_gives_null_density(self):
        s = summarize(craters("a", []), meta("a"), 0)
        self.assertEqual(s["count"], 0)
        self.assertIsNone(s["density_per_km2"])
        with self.assertRaises(ValueError):
            summarize(craters("a", []), meta("a"), -1)

if __name__ == "__main__":
    unittest.main()
