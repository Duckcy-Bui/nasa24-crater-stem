"""S2-02: phân biệt vành hố / ranh giới bóng / biên kết cấu và lọc có kiểm soát (cảnh giả lập có đáp án)."""
import unittest

import numpy as np

from src.postprocessing import REVIEW_DEFAULTS, apply_filter, classify_candidate, resolve_review_params, review_candidates
from src.preprocessing import preprocess
from tests.test_postprocessing import CRATERS, lit_scene

META = {"downsample_k": 1}


def circle(i, x, y, r):
    return {"crater_id": f"M{i}", "x": float(x), "y": float(y), "r": float(r), "confidence": None, "votes": 30}


class ReviewClasses(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        image = lit_scene(270, 70).astype(np.float64)
        yy, xx = np.mgrid[:512, :512]
        image[(xx > 380) & (yy > 300)] = 0.0                       # vùng bóng địa hình lớn, mép thẳng
        rng = np.random.default_rng(5)
        patch = (slice(20, 100), slice(220, 330))                    # vùng kết cấu: nhiễu trơn, không có hố
        noise = rng.normal(0, 1, (80, 110))
        image[patch] = np.clip(0.5 + 0.25 * noise, 0, 1)
        cls.pre = preprocess(image.astype(np.float32), META)
        cls.circles = [circle(1, *CRATERS[0]), circle(2, *CRATERS[1]),
                       circle(3, 380, 400, 12),                       # tâm trên mép bóng
                       circle(4, 275, 60, 10)]                        # giữa vùng kết cấu
        cls.out, cls.report = review_candidates(cls.circles, cls.pre)
        cls.cls = {c["crater_id"]: c["review"]["class"] for c in cls.out}

    def test_true_craters_are_rim(self):
        self.assertEqual(self.cls["M1"], "rim", self.out[0]["review"])
        self.assertEqual(self.cls["M2"], "rim", self.out[1]["review"])

    def test_circle_on_terrain_shadow_boundary_is_shadow_edge(self):
        self.assertEqual(self.cls["M3"], "shadow_edge", self.out[2]["review"])

    def test_circle_in_texture_is_texture(self):
        self.assertEqual(self.cls["M4"], "texture", self.out[3]["review"])

    def test_review_never_removes_and_keeps_fields(self):
        self.assertEqual(len(self.out), len(self.circles))
        self.assertEqual(self.report["removed"], 0)
        for before, after in zip(self.circles, self.out):
            self.assertEqual({k: after[k] for k in before}, before)
            self.assertIn(after["review"]["class"], ("rim", "shadow_edge", "texture", "unclear"))
            self.assertTrue(after["review"]["reason"])
        self.assertGreater(self.report["shadow_edge_px"], 0)


class Filter(unittest.TestCase):
    def setUp(self):
        self.circles = [{"crater_id": "A", "review": {"class": "rim"}, "shading": {"status": "consistent"}},
                        {"crater_id": "B", "review": {"class": "shadow_edge"}, "shading": {"status": "inverted"}},
                        {"crater_id": "C", "review": {"class": "texture"}, "shading": {"status": "not_checked"}}]

    def test_no_arguments_removes_nothing(self):
        kept, removed = apply_filter(self.circles)
        self.assertEqual((len(kept), len(removed)), (3, 0))

    def test_removes_only_requested_classes_with_reason(self):
        kept, removed = apply_filter(self.circles, ("shadow_edge",))
        self.assertEqual([c["crater_id"] for c in kept], ["A", "C"])
        self.assertEqual(removed[0]["filter_reason"], "review=shadow_edge")

    def test_shading_filter_never_removes_not_checked(self):
        kept, removed = apply_filter(self.circles, (), ("inverted",))
        self.assertEqual([c["crater_id"] for c in removed], ["B"])
        self.assertIn("C", [c["crater_id"] for c in kept])

    def test_unknown_class_and_param_rejected(self):
        with self.assertRaises(ValueError):
            apply_filter(self.circles, ("crater",))
        with self.assertRaises(ValueError):
            resolve_review_params({"threshold": 1})


class Classify(unittest.TestCase):
    def test_rules(self):
        p = dict(REVIEW_DEFAULTS)
        f = {"edge_px": 40, "radial_coverage": 0.7, "shadow_edge_fraction": 0.0, "rim_contrast": 2.0}
        self.assertEqual(classify_candidate(f, p)[0], "rim")
        self.assertEqual(classify_candidate({**f, "shadow_edge_fraction": 0.6}, p)[0], "shadow_edge")
        self.assertEqual(classify_candidate({**f, "radial_coverage": 0.3}, p)[0], "texture")
        self.assertEqual(classify_candidate({**f, "rim_contrast": 1.1}, p)[0], "texture")
        self.assertEqual(classify_candidate({**f, "edge_px": 0}, p)[0], "unclear")


if __name__ == "__main__":
    unittest.main()
