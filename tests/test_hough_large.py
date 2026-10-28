import unittest
from pathlib import Path

import numpy as np
from src.hough import detect_circles, _circle_offsets, resolve_hough_params


class LargeCraterTests(unittest.TestCase):
    def test_default_game_selection_is_score_and_balanced_is_explicit(self):
        from src.contracts import read_json

        root = Path(__file__).resolve().parents[1]
        self.assertEqual(resolve_hough_params({})["candidate_selection"], "score")
        self.assertEqual(
            resolve_hough_params(read_json(root / "configs/default.json"))[
                "candidate_selection"
            ],
            "score",
        )
        self.assertEqual(
            resolve_hough_params(read_json(root / "configs/s201_large_craters.json"))[
                "candidate_selection"
            ],
            "radius_balanced",
        )

    def test_large_partial_rim_survives_small_circle_output_saturation(self):
        edges = np.zeros((512, 512), dtype=bool)
        angles = np.deg2rad(np.arange(360.0))
        for x in range(40, 480, 70):
            for y in (40, 470):
                offsets = _circle_offsets(5, angles)
                edges[y + offsets[:, 1], x + offsets[:, 0]] = True
        offsets = _circle_offsets(80, angles[:210])
        edges[256 + offsets[:, 1], 256 + offsets[:, 0]] = True
        settings = dict(radius_step_px=25, max_circles=10)
        old = detect_circles(edges, 5, 80, dict(settings, candidate_selection="score"))
        self.assertEqual(old, detect_circles(edges, 5, 80, settings))
        new = detect_circles(
            edges, 5, 80, dict(settings, candidate_selection="radius_balanced")
        )

        def found(circles):
            return any(
                abs(c["x"] - 256) <= 1
                and abs(c["y"] - 256) <= 1
                and abs(c["r"] - 80) <= 1
                for c in circles
            )

        self.assertFalse(found(old))
        self.assertTrue(found(new))
        self.assertLessEqual(len(new), 10)
        self.assertEqual(
            new,
            detect_circles(
                edges, 5, 80, dict(settings, candidate_selection="radius_balanced")
            ),
        )

    def test_selection_validation(self):
        for value in ("unknown", None, [], True):
            with self.assertRaises(ValueError):
                resolve_hough_params(dict(candidate_selection=value))
