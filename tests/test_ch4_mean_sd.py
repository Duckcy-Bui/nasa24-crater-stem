import csv
import tempfile
import unittest
from pathlib import Path

from scripts.ch4_mean_sd import build, mean_sd


class MeanSdTests(unittest.TestCase):
    def test_mean_sd_sample(self):
        mean, sd = mean_sd([0.0, 0.5, 1.0])
        self.assertAlmostEqual(mean, 0.5)
        self.assertAlmostEqual(sd, 0.5)

    def test_single_value_has_zero_sd(self):
        self.assertEqual(mean_sd([0.25]), (0.25, 0.0))

    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            mean_sd([])

    def test_build_matches_saved_evidence(self):
        rows = build()
        saved = Path(__file__).resolve().parents[1] / "docs/evidence/s3-12/ch4_mean_sd.csv"
        with saved.open(encoding="utf-8", newline="") as f:
            expected = list(csv.DictReader(f))
        self.assertEqual([{k: str(v) for k, v in r.items()} for r in rows], expected)

    def test_pooled_recall_matches_known_totals(self):
        by_key = {(r["source"], r["split"], r["method"]): r for r in build()}
        s215 = by_key[("s2-15", "tuning", "numpy_score")]
        self.assertEqual((s215["n_images"], s215["tp"], s215["labels"]), (18, 10, 174))
        holdout = by_key[("s2-06-s3-02", "holdout", "numpy_score")]
        self.assertEqual((holdout["n_images"], holdout["tp"], holdout["labels"]), (8, 4, 66))


if __name__ == "__main__":
    unittest.main()
