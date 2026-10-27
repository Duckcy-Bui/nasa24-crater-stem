"""Kiểm tra quy tắc đo của S2-07, không cần bộ ảnh đã giải nén."""
from __future__ import annotations

import unittest
from pathlib import Path

from scripts.s207_experiments import e1_status, known_references, recall_summary, validate_run_selection


class TestS207Experiments(unittest.TestCase):
    def test_uncertain_label_is_excluded_from_recall(self):
        reference = {"circles": [
            {"crater_id": "C1", "x": 10.0, "y": 10.0, "r": 10.0},
            {"crater_id": "C2_uncertain", "x": 50.0, "y": 50.0, "r": 10.0},
        ]}
        self.assertEqual([c["crater_id"] for c in known_references(reference)], ["C1"])
        result = recall_summary([], reference, radius_bounds=(5, 20), max_circles=100)
        self.assertEqual(result["known_labels"], 1)
        self.assertEqual(result["recall_known"], 0.0)
        self.assertIsNone(result["precision"])
        self.assertIsNone(result["f1"])
        self.assertEqual(result["reference_radius_in_search"], 1)
        self.assertEqual(result["reference_radius_outside_search"], 0)
        self.assertFalse(result["hit_max_circles"])

    def test_recall_reports_search_and_machine_diagnostics(self):
        reference = {"circles": [{"crater_id": "C1", "x": 10.0, "y": 10.0, "r": 8.0},
                                 {"crater_id": "C2", "x": 30.0, "y": 30.0, "r": 30.0}]}
        circles = [{"crater_id": f"M{i}", "x": 100.0 + i, "y": 100.0, "r": 5.0} for i in range(3)]
        result = recall_summary(circles, reference, radius_bounds=(5, 20), max_circles=3)
        self.assertEqual(result["reference_radius_in_search"], 1)
        self.assertEqual(result["reference_radius_outside_search"], 1)
        self.assertTrue(result["hit_max_circles"])
        self.assertEqual(result["machine_radius_px"], [5.0, 5.0])

    def test_holdout_requires_explicit_mode_and_chosen_config(self):
        splits = {"tuning": "tuning", "holdout": "holdout"}
        with self.assertRaisesRegex(ValueError, "Holdout chỉ chạy"):
            validate_run_selection(["holdout"], splits, holdout=False, chosen_config=None)
        with self.assertRaisesRegex(ValueError, "--chosen-config"):
            validate_run_selection(["holdout"], splits, holdout=True, chosen_config=None)
        validate_run_selection(["holdout"], splits, holdout=True, chosen_config=Path("chosen.json"))

    def test_holdout_mode_rejects_tuning_only_images(self):
        with self.assertRaisesRegex(ValueError, "yêu cầu ít nhất"):
            validate_run_selection(["tuning"], {"tuning": "tuning"}, holdout=True, chosen_config=Path("chosen.json"))

    def test_e1_holdout_is_never_evaluable(self):
        self.assertEqual(e1_status("holdout", True), "not_evaluable_on_holdout")
        self.assertEqual(e1_status("holdout", False), "not_evaluable_on_holdout")
        self.assertEqual(e1_status("tuning", True), "diagnostic_tuning_only")


if __name__ == "__main__":
    unittest.main()
