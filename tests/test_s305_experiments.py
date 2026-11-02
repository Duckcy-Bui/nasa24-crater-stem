"""S3-05 protocol guards: frozen baseline and no parameter search on holdout."""
import copy
import unittest

from scripts.s305_experiments import MARE, TUNING, parameter_variants, validate_scope
from src.contracts import read_json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestS305Protocol(unittest.TestCase):
    def setUp(self):
        self.config = read_json(ROOT / "configs/s215_frozen.json")
        self.splits = {**dict.fromkeys(TUNING, "tuning"), MARE: "holdout"}

    def test_reject_changed_production_configuration(self):
        changed = copy.deepcopy(self.config)
        changed["hough"]["min_vote_ratio"] = .4
        with self.assertRaisesRegex(ValueError, "differs"):
            validate_scope(self.splits, self.config, changed)

    def test_reject_reclassified_experimental_image(self):
        self.splits[TUNING[0]] = "holdout"
        with self.assertRaisesRegex(ValueError, "scope changed"):
            validate_scope(self.splits, self.config, self.config)

    def test_holdout_cannot_be_parameter_sweep(self):
        with self.assertRaisesRegex(ValueError, "forbidden"):
            parameter_variants(MARE, self.splits)

    def test_each_sweep_changes_one_factor_from_frozen_baseline(self):
        validate_scope(self.splits, self.config, self.config)
        variants = parameter_variants(TUNING[0], self.splits)
        self.assertEqual(len(variants), 4)
        for name, override in variants.items():
            changed = [k for k, v in override.items() if self.config["hough"][k] != v]
            self.assertEqual(len(changed), 0 if name == "baseline" else 1)


if __name__ == "__main__":
    unittest.main()
