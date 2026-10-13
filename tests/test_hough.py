import json
import unittest

import numpy as np

from src.hough import detect_circles, resolve_hough_params


class TestHough(unittest.TestCase):
    @staticmethod
    def make_circle(x, y, radius):
        """Tạo đường biên tròn trên ảnh bool 512×512."""
        yy, xx = np.indices((512, 512))
        distance = np.hypot(xx - x, yy - y)
        return np.abs(distance - radius) <= 0.5

    def assert_circle_found(self, circles, x, y, radius):
        found = any(
            abs(circle["x"] - x) <= 1
            and abs(circle["y"] - y) <= 1
            and abs(circle["r"] - radius) <= 1
            for circle in circles
        )
        self.assertTrue(
            found,
            f"Không tìm thấy vòng tròn ({x}, {y}, {radius}): {circles}",
        )

    def test_empty_edges(self):
        edges = np.zeros((512, 512), dtype=bool)

        circles = detect_circles(edges, 5, 128, {})

        self.assertEqual(circles, [])

    def test_single_circle(self):
        edges = self.make_circle(160, 180, 32)

        circles = detect_circles(edges, 28, 36, {})

        self.assert_circle_found(circles, 160, 180, 32)

    def test_two_circles(self):
        edges = (
            self.make_circle(160, 180, 32)
            | self.make_circle(350, 310, 20)
        )

        circles = detect_circles(edges, 18, 34, {})

        self.assert_circle_found(circles, 160, 180, 32)
        self.assert_circle_found(circles, 350, 310, 20)

    def test_circle_at_border(self):
        edges = self.make_circle(8, 250, 24)

        circles = detect_circles(edges, 22, 26, {})

        self.assert_circle_found(circles, 8, 250, 24)

    def test_output_format(self):
        edges = self.make_circle(160, 180, 32)
        circles = detect_circles(edges, 32, 32, {})

        self.assertTrue(circles)
        expected_keys = {
            "crater_id", "x", "y", "r", "confidence", "votes",
        }
        identifiers = []

        for circle in circles:
            self.assertEqual(set(circle), expected_keys)
            self.assertIsInstance(circle["crater_id"], str)
            self.assertIsInstance(circle["x"], float)
            self.assertIsInstance(circle["y"], float)
            self.assertIsInstance(circle["r"], float)
            self.assertIsInstance(circle["votes"], int)
            self.assertGreaterEqual(circle["votes"], 0)
            self.assertIsNone(circle["confidence"])
            self.assertTrue(0 <= circle["x"] <= 511)
            self.assertTrue(0 <= circle["y"] <= 511)
            self.assertGreater(circle["r"], 0)
            identifiers.append(circle["crater_id"])

        self.assertEqual(len(identifiers), len(set(identifiers)))

        # Bảo đảm kết quả có thể lưu JSON, không chứa NaN/Infinity.
        json.dumps(circles, allow_nan=False)

    def test_invalid_inputs(self):
        edges = self.make_circle(160, 180, 32)

        cases = [
            (edges.astype(np.uint8), 28, 36, {}),
            (np.zeros((5, 5), dtype=bool), 5, 10, {}),
            (edges, 36, 28, {}),
            (edges, 28, 36, {"radius_step_px": 0}),
            (edges, 28, 36, {"min_vote_ratio": float("nan")}),
        ]

        for image, r_min, r_max, params in cases:
            with self.subTest(r_min=r_min, r_max=r_max, params=params):
                with self.assertRaises(ValueError):
                    detect_circles(image, r_min, r_max, params)

    def test_nested_config(self):
        config = {
            "schema_version": "1.0",
            "hough": {
                "radius_step_px": 1,
                "r_min_limit_px": 5,
                "r_max_limit_px": 128,
            },
        }

        params = resolve_hough_params(config)

        self.assertEqual(params["radius_step_px"], 1)
        self.assertIn("min_votes", params)

        edges = self.make_circle(160, 180, 32)
        circles = detect_circles(edges, 28, 36, config)

        self.assert_circle_found(circles, 160, 180, 32)


if __name__ == "__main__":
    unittest.main()