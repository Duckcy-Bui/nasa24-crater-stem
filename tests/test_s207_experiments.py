"""Kiểm tra quy tắc đo của S2-07, không cần bộ ảnh đã giải nén."""
from __future__ import annotations

import unittest

from scripts.s207_experiments import known_references, recall_summary


class TestS207Experiments(unittest.TestCase):
    def test_uncertain_label_is_excluded_from_recall(self):
        reference = {"circles": [
            {"crater_id": "C1", "x": 10.0, "y": 10.0, "r": 10.0},
            {"crater_id": "C2_uncertain", "x": 50.0, "y": 50.0, "r": 10.0},
        ]}
        self.assertEqual([c["crater_id"] for c in known_references(reference)], ["C1"])
        result = recall_summary([], reference)
        self.assertEqual(result["known_labels"], 1)
        self.assertEqual(result["recall_known"], 0.0)
        self.assertIsNone(result["precision"])
        self.assertIsNone(result["f1"])


if __name__ == "__main__":
    unittest.main()
