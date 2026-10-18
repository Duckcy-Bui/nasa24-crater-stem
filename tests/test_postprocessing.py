"""S1-11: kiểm tra chấm sáng–tối trên cảnh giả lập có đáp án biết trước (không phải ảnh NASA)."""
import copy
import math
import unittest
from pathlib import Path

import numpy as np

from src.contracts import read_json, validate_crater_set
from src.postprocessing import (classify, filter_candidates, resolve_params, resolve_sun, score_candidates,
                                score_one, shading_score, sun_vector)

ROOT = Path(__file__).resolve().parents[1]
CRATERS = ((150, 150, 30), (360, 380, 20), (400, 120, 14))  # hố lõm: đúng
DOMES = ((140, 380, 25),)                                    # gò nổi: sáng–tối ngược
FLAT = ((300, 260, 22),)                                     # vòng đặt vào chỗ phẳng


def lit_scene(azimuth_deg: float, incidence_deg: float, seed: int = 0) -> np.ndarray:
    """Bản đồ độ cao (hố lõm parabol, gò nổi) tô bóng Lambert theo quy ước S1-04 mục 6.1."""
    yy, xx = np.mgrid[:512, :512].astype(np.float64)
    dem = np.zeros((512, 512))
    for x, y, r in CRATERS:
        d = np.hypot(xx - x, yy - y) / r
        dem += np.where(d < 1, 0.25 * r * (d ** 2 - 1), 0)
    for x, y, r in DOMES:
        d = np.hypot(xx - x, yy - y) / r
        dem += np.where(d < 1, 0.25 * r * (1 - d ** 2), 0)
    ux, uy = sun_vector(azimuth_deg, 0.0)
    inc = math.radians(incidence_deg)
    fy, fx = np.gradient(dem)
    shade = (-fx * ux * math.sin(inc) - fy * uy * math.sin(inc) + math.cos(inc)) / np.sqrt(fx ** 2 + fy ** 2 + 1)
    image = np.clip(shade, 0, None) * 0.6 + 0.2 + np.random.default_rng(seed).normal(0, 0.02, dem.shape)
    return np.clip(image, 0, 1).astype(np.float32)


def circles(groups):
    return [{"crater_id": f"M{i}", "x": float(x), "y": float(y), "r": float(r), "confidence": None, "votes": 50}
            for i, (x, y, r) in enumerate(groups, 1)]


class SunVector(unittest.TestCase):
    def test_s104_convention(self):
        for az, expected in ((0, (0, -1)), (90, (1, 0)), (180, (0, 1)), (270, (-1, 0))):
            np.testing.assert_allclose(sun_vector(az, 0), expected, atol=1e-12)

    def test_north_angle_rotates_clockwise(self):
        np.testing.assert_allclose(sun_vector(0, 90), (1, 0), atol=1e-12)


class ShadingScore(unittest.TestCase):
    """Nắng từ phía Tây (270°), góc tới 70°: hố có thành Tây tối, thành Đông sáng."""

    def setUp(self):
        self.image = lit_scene(270, 70)
        self.valid = np.ones((512, 512), dtype=bool)
        self.p = resolve_params({})
        self.u = sun_vector(270, 0)

    def score(self, x, y, r, u=None):
        return shading_score(self.image, self.valid, x, y, r, u or self.u, self.p)[0]

    def test_true_craters_are_consistent(self):
        for c in CRATERS:
            s = self.score(*c)
            self.assertGreater(s, 0.5, c)
            self.assertEqual(classify(s, "side_only", self.p), "consistent")

    def test_dome_is_inverted(self):
        s = self.score(*DOMES[0])
        self.assertLess(s, -0.5)
        self.assertEqual(classify(s, "side_only", self.p), "inverted")

    def test_circle_on_flat_ground_is_unclear(self):
        s = self.score(*FLAT[0])
        self.assertLess(abs(s), 0.15)
        self.assertEqual(classify(s, "side_only", self.p), "unclear")

    def test_wrong_sun_side_flips_every_verdict(self):
        """Lý do bắt buộc kiểm tra hướng nắng: ghi nhầm Đông/Tây thì hố thật bị chấm là ngược."""
        for c in CRATERS:
            self.assertLess(self.score(*c, u=sun_vector(90, 0)), -0.5)

    def test_score_ignores_brightness_and_contrast_scale(self):
        a = self.score(*CRATERS[0])
        self.image = self.image * 0.3 + 0.1
        self.assertAlmostEqual(self.score(*CRATERS[0]), a, places=5)

    def test_circle_mostly_outside_image_is_not_scored(self):
        score, reason = shading_score(self.image, self.valid, 2.0, 2.0, 30.0, self.u, self.p)
        self.assertIsNone(score)
        self.assertIn("pixel", reason)

    def test_invalid_pixels_are_excluded(self):
        self.valid[:, :160] = False
        score, reason = shading_score(self.image, self.valid, 150, 150, 30, self.u, self.p)
        self.assertIsNone(score)


class TerrainSlope(unittest.TestCase):
    """Độ dốc sáng của địa hình không được biến một vòng chỗ phẳng thành 'hợp' hay 'ngược'."""

    def setUp(self):
        self.valid = np.ones((512, 512), dtype=bool)
        self.u = sun_vector(270, 0)
        self.xx = np.mgrid[:512, :512][1]

    def status(self, image, c, **params):
        return score_one(image, self.valid, dict(zip("xyr", c)), self.u, "side_only", resolve_params(params))

    def test_slope_alone_fools_raw_score(self):
        """Tái hiện lỗi: không trừ dốc thì vòng chỗ phẳng bị chấm theo độ dốc."""
        for slope, expected in ((0.001, "consistent"), (-0.001, "inverted")):
            image = lit_scene(270, 70) + slope * (self.xx - 256)
            self.assertEqual(self.status(image, FLAT[0], detrend=False)["status"], expected)

    def test_detrend_keeps_flat_circle_unclear_and_craters_correct(self):
        for slope in (0.001, -0.001, 0.003):
            image = np.clip(lit_scene(270, 70) + slope * (self.xx - 256), 0, 1)
            self.assertEqual(self.status(image, FLAT[0])["status"], "unclear", slope)
            for c in CRATERS:
                self.assertEqual(self.status(image, c)["status"], "consistent", (slope, c))
            self.assertEqual(self.status(image, DOMES[0])["status"], "inverted", slope)

    def test_shadow_edge_next_to_circle_is_unclear_not_consistent(self):
        """Mép bóng sắc sát vòng: mặt phẳng trừ dốc tự tạo dấu giả; quy tắc 'hai cách phải cùng nhãn' chặn lại."""
        x, y, r = FLAT[0]
        image = lit_scene(270, 70)
        image[self.xx > x + r] *= 0.3
        s = self.status(image, FLAT[0])
        self.assertGreater(s["score"], 0.25)          # trừ dốc một mình sẽ chấm nhầm "hợp"
        self.assertEqual(s["status"], "unclear")
        self.assertIn("không ổn định", s["reason"])

    def test_annulus_in_nodata_is_not_checked(self):
        x, y, r = CRATERS[0]
        yy, xx = np.mgrid[:512, :512]
        self.valid = np.hypot(xx - x, yy - y) <= 1.2 * r  # chỉ còn đĩa hợp lệ, vành ngoài là nodata
        s = self.status(lit_scene(270, 70), CRATERS[0])
        self.assertEqual(s["status"], "not_checked")
        self.assertIn("vành ngoài", s["reason"])


class SunReliability(unittest.TestCase):
    def setUp(self):
        self.p = resolve_params({})
        self.meta = {"image_id": "x", "north_angle_deg": 0.0,
                     "sun": {"azimuth_deg": 270.0, "incidence_deg": 80.0, "quality": "side_only",
                             "side": "west", "side_candidate": None, "source": "LROC PHO: nắng phía Tây"}}
        self.ok = {"verdict": "consistent", "checked_by": "Hưng", "checked_on": "2026-10-16"}

    def sun(self, meta=None, check=None):
        return resolve_sun(meta or self.meta, check, self.p)

    def test_documented_side_plus_visual_check_is_usable(self):
        s = self.sun(check=self.ok)
        self.assertTrue(s["usable"])
        self.assertEqual(s["azimuth_deg"], 270.0)
        self.assertEqual(len(s["basis"]), 2)

    def test_missing_visual_check_is_reported(self):
        s = self.sun()
        self.assertFalse(s["usable"])
        self.assertIn("bằng mắt", s["reason"])
        self.assertFalse(self.sun(check={"verdict": "pending"})["usable"])

    def test_visual_check_contradiction_blocks_image(self):
        s = self.sun(check={"verdict": "inverted"})
        self.assertFalse(s["usable"])
        self.assertIn("inverted", s["reason"])

    def test_no_sun_metadata(self):
        meta = copy.deepcopy(self.meta)
        meta["sun"].update(azimuth_deg=None, quality="none", side=None)
        s = self.sun(meta, self.ok)
        self.assertFalse(s["usable"])
        self.assertIn("không có hướng nắng", s["reason"])

    def test_east_candidate_needs_visual_confirmation(self):
        meta = copy.deepcopy(self.meta)
        meta["sun"].update(azimuth_deg=None, quality="none", side=None, side_candidate="east")
        self.assertIn("chưa xác minh", self.sun(meta)["reason"])
        s = self.sun(meta, self.ok)
        self.assertTrue(s["usable"])
        self.assertEqual((s["azimuth_deg"], s["quality"]), (90.0, "side_only"))

    def test_near_overhead_sun_is_skipped(self):
        meta = copy.deepcopy(self.meta)
        meta["sun"]["incidence_deg"] = 7.64
        s = self.sun(meta, self.ok)
        self.assertFalse(s["usable"])
        self.assertIn("gần đứng", s["reason"])

    def test_mosaic_without_window_incidence(self):
        meta = copy.deepcopy(self.meta)
        meta["sun"]["incidence_deg"] = None
        self.assertIn("góc tới", self.sun(meta, self.ok)["reason"])


class FilterCandidates(unittest.TestCase):
    def setUp(self):
        self.meta = read_json(ROOT / "data/examples/s105_synthetic_512.json")
        self.meta["sun"] = {"azimuth_deg": 270.0, "incidence_deg": 70.0, "quality": "side_only",
                            "source": "cảnh giả lập test"}
        self.meta["north_up"], self.meta["north_angle_deg"] = True, 0.0
        self.checks = {self.meta["image_id"]: {"verdict": "consistent", "checked_by": "test", "checked_on": "2026-10-16"}}
        self.image = lit_scene(270, 70)
        self.circles = circles(CRATERS + DOMES + FLAT)

    def test_scores_without_removing_and_keeps_contract(self):
        out, report = score_candidates(self.circles, self.image, self.meta, {"sun_checks": self.checks})
        self.assertEqual(len(out), len(self.circles))
        self.assertEqual(report["removed"], 0)
        self.assertEqual([c["shading"]["status"] for c in out],
                         ["consistent"] * 3 + ["inverted", "unclear"])
        for before, after in zip(self.circles, out):
            self.assertEqual({k: after[k] for k in before}, before)
        validate_crater_set({"schema_version": "1.0", "data_kind": "synthetic", "image_id": self.meta["image_id"],
                             "source": "machine", "reference_source": None, "circles": out}, self.meta)
        self.assertNotIn("shading", self.circles[0])  # không sửa danh sách gốc

    def test_unreliable_image_marks_all_not_checked_and_logs(self):
        self.meta["sun"].update(azimuth_deg=None, quality="none")
        with self.assertLogs("src.postprocessing", level="WARNING") as logs:
            out = filter_candidates(self.circles, self.image, self.meta, {"sun_checks": self.checks})
        self.assertEqual({c["shading"]["status"] for c in out}, {"not_checked"})
        self.assertTrue(all(c["shading"]["reason"] for c in out))
        self.assertIn(self.meta["image_id"], logs.output[0])

    def test_unknown_parameter_rejected(self):
        with self.assertRaises(ValueError):
            score_candidates(self.circles, self.image, self.meta, {"threshold": 1})


if __name__ == "__main__":
    unittest.main()
