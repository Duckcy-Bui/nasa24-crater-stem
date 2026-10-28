import copy
import unittest
from pathlib import Path
from src.contracts import read_json, ContractError
from src.evaluation import evaluate

ROOT = Path(__file__).resolve().parents[1]


def circle(ident, x=100.0, y=100.0, radius=20.0):
    return dict(crater_id=ident, x=x, y=y, r=radius, confidence=None, votes=None)


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.meta = read_json(ROOT / "data/examples/s105_synthetic_512.json")
        common = dict(
            schema_version="1.0",
            data_kind=self.meta["data_kind"],
            image_id=self.meta["image_id"],
        )
        self.machine = dict(common, source="machine", reference_source=None, circles=[])
        self.catalogue = dict(
            common,
            source="catalogue",
            reference_source="manual; reviewed by reviewer",
            circles=[],
        )
        self.params = dict(metadata=self.meta)

    def run_eval(self, predictions, references, complete=False):
        self.machine["circles"] = predictions
        self.catalogue["circles"] = references
        if complete:
            self.catalogue["catalogue_coverage"] = "complete"
        return evaluate(self.machine, self.catalogue, self.params)

    def test_sparse_never_counts_unknown_regions_as_false_positives(self):
        out = self.run_eval([circle("M1"), circle("M2", 400.0)], [circle("C1")])
        self.assertEqual((out["tp"], out["fn"], out["recall"]), (1, 0, 1.0))
        self.assertIsNone(out["fp"])
        self.assertIsNone(out["precision"])
        self.assertIsNone(out["f1"])

    def test_complete_duplicates_and_boundary(self):
        out = self.run_eval(
            [circle("M1", 110.0), circle("M2", 100.0)], [circle("C1")], True
        )
        self.assertEqual((out["tp"], out["fp"], out["fn"]), (1, 1, 0))
        self.assertAlmostEqual(out["f1"], 2 / 3)
        out = self.run_eval([circle("M1", 110.0)], [circle("C1")], True)
        self.assertEqual(out["tp"], 1)
        out = self.run_eval([circle("M1", 110.01)], [circle("C1")], True)
        self.assertEqual(out["tp"], 0)

    def test_uncertain_region_ignores_all_remaining_predictions(self):
        out = self.run_eval(
            [circle("M1"), circle("M2", 101.0), circle("M3", 300.0)],
            [circle("C_uncertain")],
            True,
        )
        self.assertEqual(out["ignored_prediction_ids"], ["M1", "M2"])
        self.assertEqual((out["tp"], out["fp"], out["fn"]), (0, 1, 0))
        out = self.run_eval([circle("M1")], [circle("C1"), circle("C_uncertain")], True)
        self.assertEqual(out["tp"], 1)

    def test_empty_and_unreviewed(self):
        out = self.run_eval([], [], True)
        self.assertEqual((out["tp"], out["fp"], out["fn"]), (0, 0, 0))
        self.assertIsNone(out["recall"])
        self.assertIsNone(out["precision"])
        self.catalogue["reference_source"] = "unreviewed"
        self.assertEqual(
            evaluate(self.machine, self.catalogue, self.params)["status"], "unavailable"
        )

    def test_invalid_inputs(self):
        for params in (
            {},
            dict(metadata=self.meta, center_tolerance_fraction=float("nan")),
        ):
            with self.assertRaises(ContractError):
                evaluate(self.machine, self.catalogue, params)
        self.machine["image_id"] = "other"
        with self.assertRaises(ContractError):
            evaluate(self.machine, self.catalogue, self.params)

    def test_maximum_cardinality_matching_and_permutation(self):
        predictions = [circle("M1", 109.0), circle("M2", 99.0)]
        refs = [circle("C1", 100.0), circle("C2", 118.0)]
        out = self.run_eval(predictions, refs, True)
        self.assertEqual(out["tp"], 2)
        other = self.run_eval(predictions[::-1], refs[::-1], True)
        self.assertEqual(
            sorted((p["prediction_id"], p["reference_id"]) for p in out["pairs"]),
            sorted((p["prediction_id"], p["reference_id"]) for p in other["pairs"]),
        )
