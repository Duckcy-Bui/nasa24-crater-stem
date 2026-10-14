import json
import unittest

import numpy as np

from src.hough import _accumulate, detect_circles, resolve_hough_params


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

    def test_accumulator_counts_duplicates_and_clips_centers(self):
        # Hai diem bien co the bo phieu vao cung mot tam. Phieu ngoai anh
        # phai bi loai, khong duoc quay vong sang cot/hang cuoi.
        ys = np.array([0, 0, 1], dtype=np.int32)
        xs = np.array([0, 1, 0], dtype=np.int32)
        offsets = np.array([[0, 0], [1, 0], [0, 1]], dtype=np.int32)
        expected = np.array([[3, 1, 0], [1, 0, 0]], dtype=np.int32)
        for batch_size in (1, 2, 256):
            with self.subTest(batch_size=batch_size):
                actual = _accumulate(ys, xs, (2, 3), offsets, batch_size)
                np.testing.assert_array_equal(actual, expected)

    def test_gradient_two_circles_and_border(self):
        yy, xx = np.indices((512, 512))
        edges = np.zeros((512, 512), dtype=bool)
        theta = np.full((512, 512), np.nan, dtype=np.float32)
        truth = [(160, 180, 32), (350, 310, 20), (8, 420, 24)]
        for x, y, radius in truth:
            contour = self.make_circle(x, y, radius)
            edges |= contour
            theta[contour] = np.arctan2(yy[contour] - y, xx[contour] - x)
        params = {"voting_method": "gradient"}
        circles = detect_circles(edges, 18, 34, params, theta=theta)
        # Dao gradient sang/toi khong duoc lam doi ket qua.
        reversed_circles = detect_circles(
            edges, 18, 34, params, theta=theta + np.pi,
        )
        for x, y, radius in truth:
            self.assert_circle_found(circles, x, y, radius)
            self.assert_circle_found(reversed_circles, x, y, radius)
        self.assertTrue(all(0 <= c["x"] <= 511 and 0 <= c["y"] <= 511
                            for c in circles))
        self.assertTrue(all(c["confidence"] is None for c in circles))

    def test_gradient_requires_valid_theta_even_on_empty_edges(self):
        edges = self.make_circle(160, 180, 32)
        params = {"voting_method": "gradient"}
        for image, theta in (
            (edges, None),
            (np.zeros_like(edges), None),
            (edges, np.zeros((1, 1))),
            (edges, np.full(edges.shape, np.nan)),
        ):
            with self.subTest(theta_shape=getattr(theta, "shape", None)):
                with self.assertRaises(ValueError):
                    detect_circles(image, 28, 36, params, theta=theta)

    def test_gradient_straight_edge_is_not_circle(self):
        edges = np.zeros((512, 512), dtype=bool)
        edges[40:470, 250] = True
        theta = np.zeros(edges.shape, dtype=np.float32)
        self.assertEqual(detect_circles(
            edges, 5, 128, {"voting_method": "gradient"}, theta=theta,
        ), [])

    def test_default_method_remains_full_circle(self):
        params = resolve_hough_params({})
        self.assertEqual(params["voting_method"], "full_circle")
        self.assertEqual(params["radius_step_px"], 1)
        for value in ("unknown", None, 42, {"method": "gradient"}):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    resolve_hough_params({"voting_method": value})

    def test_radius_limits_and_max_circles(self):
        edges = self.make_circle(160, 180, 32)
        for lo, hi in ((4, 32), (32, 129), (True, 32), (5.0, 32)):
            with self.subTest(lo=lo, hi=hi):
                with self.assertRaises(ValueError):
                    detect_circles(edges, lo, hi, {})
        circles = detect_circles(edges, 28, 36, {"max_circles": 1})
        self.assertEqual(len(circles), 1)
        self.assert_circle_found(circles, 160, 180, 32)

    def test_gradient_recovers_circle_with_sparse_noise(self):
        yy, xx = np.indices((512, 512))
        circle_edges = self.make_circle(160, 180, 32)
        rng = np.random.default_rng(4)
        noise = rng.random(circle_edges.shape) < 0.01
        theta = rng.uniform(-np.pi, np.pi, circle_edges.shape)
        theta[circle_edges] = np.arctan2(
            yy[circle_edges] - 180, xx[circle_edges] - 160,
        )
        circles = detect_circles(
            circle_edges | noise, 28, 36,
            {"voting_method": "gradient"}, theta=theta,
        )
        self.assert_circle_found(circles, 160, 180, 32)

    def test_gradient_at_supported_radius_boundaries(self):
        yy, xx = np.indices((512, 512))
        theta = np.arctan2(yy - 256, xx - 256)
        for radius in (5, 128):
            with self.subTest(radius=radius):
                circles = detect_circles(
                    self.make_circle(256, 256, radius), radius, radius,
                    {"voting_method": "gradient"}, theta=theta,
                )
                self.assert_circle_found(circles, 256, 256, radius)


if __name__ == "__main__":
    unittest.main()
