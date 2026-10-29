"""S2-15 guards prevent holdout selection and silent configuration drift."""
import unittest
from copy import deepcopy
from scripts.freeze_s215 import validate_config, validate_selection
from src.contracts import read_json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class FreezeGuards(unittest.TestCase):
    def test_holdout_unknown_and_duplicates_rejected(self):
        manifest = {"images": [{"image_id": "t", "split": "tuning"}, {"image_id": "h", "split": "holdout"}]}
        self.assertEqual(validate_selection(manifest), ["t"])
        for ids in (["h"], ["t", "h"], ["unknown"], ["t", "t"], []):
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                validate_selection(manifest, ids)

    def test_active_config_matches_snapshot_and_drift_rejected(self):
        frozen = read_json(ROOT / "configs/s215_frozen.json")
        validate_config(frozen, read_json(ROOT / "configs/default.json"))
        changed = deepcopy(frozen)
        changed["hough"]["min_votes"] += 1
        with self.assertRaises(ValueError):
            validate_config(frozen, changed)
        del changed["hough"]["min_votes"]
        with self.assertRaises(ValueError):
            validate_config(changed, changed)
