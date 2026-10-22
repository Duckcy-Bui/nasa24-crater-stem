"""S2-04: ghép một–một và chấm người chơi theo hai nguồn riêng (dữ liệu giả lập)."""
import itertools
import random
import unittest
from pathlib import Path

from src.contracts import ContractError, read_json
from src.matching import match_one_to_one
from src.scoring import score_player

ROOT = Path(__file__).resolve().parents[1]
METADATA = read_json(ROOT / "data" / "examples" / "s105_synthetic_512.json")


def circle(ident, x, y, r, votes=None):
    return {"crater_id": ident, "x": float(x), "y": float(y), "r": float(r), "confidence": None, "votes": votes}


def crater_set(source, circles, reference_source=None):
    return {"schema_version": "1.0", "data_kind": METADATA["data_kind"], "image_id": METADATA["image_id"],
            "source": source, "reference_source": reference_source, "circles": circles}


def brute_force(predictions, references, tolerance=0.5):
    """Most pairs first, then smallest total normalized distance."""
    def norm(p, q):
        return ((p["x"] - q["x"]) ** 2 + (p["y"] - q["y"]) ** 2) ** 0.5 / q["r"]

    for k in range(min(len(predictions), len(references)), 0, -1):
        costs = []
        for rows in itertools.combinations(range(len(predictions)), k):
            for cols in itertools.permutations(range(len(references)), k):
                distances = [norm(predictions[i], references[j]) for i, j in zip(rows, cols)]
                if all(d <= tolerance for d in distances):
                    costs.append(sum(distances))
        if costs:
            return k, min(costs)
    return 0, 0.0


class TestMatching(unittest.TestCase):
    def test_center_tolerance_is_half_the_reference_radius(self):
        ref = [circle("R", 100, 100, 20)]
        self.assertEqual(len(match_one_to_one([circle("P", 110, 100, 5)], ref)), 1)  # 10 px = 0.5 r
        self.assertEqual(match_one_to_one([circle("P", 110.5, 100, 5)], ref), [])

    def test_one_reference_is_never_counted_twice(self):
        ref = [circle("R", 100, 100, 20)]
        pairs = match_one_to_one([circle("P1", 101, 100, 20), circle("P2", 99, 100, 20)], ref)
        self.assertEqual(len(pairs), 1)

    def test_maximum_pairs_beats_greedy_nearest(self):
        # Greedy would give P1 to R1 (nearest) and leave P2 without a reference.
        refs = [circle("R1", 100, 100, 20), circle("R2", 112, 100, 4)]
        preds = [circle("P1", 110, 100, 10), circle("P2", 90, 100, 10)]
        pairs = {(p["prediction_id"], p["reference_id"]) for p in match_one_to_one(preds, refs)}
        self.assertEqual(pairs, {("P1", "R2"), ("P2", "R1")})

    def test_matches_brute_force_on_random_scenes(self):
        rng = random.Random(7)
        for _ in range(150):
            preds = [circle(f"P{i}", rng.uniform(0, 60), rng.uniform(0, 60), rng.uniform(5, 15)) for i in range(rng.randint(0, 4))]
            refs = [circle(f"R{i}", rng.uniform(0, 60), rng.uniform(0, 60), rng.uniform(5, 20)) for i in range(rng.randint(0, 4))]
            pairs = match_one_to_one(preds, refs)
            count, cost = brute_force(preds, refs)
            self.assertEqual(len(pairs), count)
            self.assertAlmostEqual(sum(p["normalized_center_distance"] for p in pairs), cost, places=3)
            self.assertEqual(len({p["reference_id"] for p in pairs}), len(pairs))
            self.assertEqual(len({p["prediction_id"] for p in pairs}), len(pairs))

    def test_result_does_not_depend_on_input_order(self):
        rng = random.Random(3)
        preds = [circle(f"P{i}", rng.uniform(0, 80), rng.uniform(0, 80), 8) for i in range(12)]
        refs = [circle(f"R{i}", rng.uniform(0, 80), rng.uniform(0, 80), 12) for i in range(9)]
        first = {(p["prediction_id"], p["reference_id"]) for p in match_one_to_one(preds, refs)}
        second = {(p["prediction_id"], p["reference_id"]) for p in match_one_to_one(preds[::-1], refs[::-1])}
        self.assertEqual(len(first), len(second))

    def test_large_sets_run_quickly(self):
        rng = random.Random(1)
        preds = [circle(f"P{i}", rng.uniform(0, 511), rng.uniform(0, 511), 10) for i in range(500)]
        refs = [circle(f"R{i}", rng.uniform(0, 511), rng.uniform(0, 511), rng.uniform(5, 40)) for i in range(100)]
        self.assertTrue(match_one_to_one(preds, refs))


class TestScorePlayer(unittest.TestCase):
    def setUp(self):
        self.player = crater_set("player", [circle("U1", 101, 100, 19), circle("U2", 300, 300, 10), circle("U3", 400, 50, 8)])
        self.machine = crater_set("machine", [circle("M1", 100, 100, 20, votes=50), circle("M2", 200, 200, 15, votes=30)])
        self.labels = [circle("C1", 100, 100, 20), circle("C2", 400, 52, 9), circle("C3", 50, 450, 12),
                       circle("C4_uncertain", 300, 300, 10)]

    def score(self, reference_source=None, **params):
        catalogue = crater_set("catalogue", self.labels, reference_source) if reference_source else None
        return score_player(self.player, self.machine, catalogue, params, metadata=METADATA)

    def test_machine_comparison_is_agreement_only(self):
        result = self.score()
        self.assertEqual(result["vs_machine"]["matched"], 1)
        self.assertEqual(result["vs_machine"]["player_only_ids"], ["U2", "U3"])
        self.assertEqual(result["vs_machine"]["machine_only_ids"], ["M2"])
        self.assertIn("không phải đáp án", result["vs_machine"]["note"])
        self.assertIsNone(result["score"])
        self.assertEqual(result["vs_catalogue"]["status"], "unavailable")

    def test_unreviewed_labels_are_not_scored(self):
        result = self.score("manual_label_s110; sparse manual labels, unreviewed")
        self.assertEqual(result["vs_catalogue"]["status"], "unavailable")
        self.assertIsNone(result["score"])
        self.assertIn("kiểm chéo", result["vs_catalogue"]["reason"])

    def test_sparse_reviewed_labels_give_recall_without_false_positives(self):
        result = self.score("manual_label_s110; sparse manual labels, reviewed by Tiến")
        catalogue = result["vs_catalogue"]
        self.assertEqual(catalogue["status"], "scored")
        self.assertEqual(catalogue["excluded_ids"], ["C4_uncertain"])  # U2 sits on it but is not rewarded
        self.assertEqual(catalogue["correct"], 2)
        self.assertEqual(catalogue["missed_ids"], ["C3"])
        self.assertIsNone(catalogue["wrong_ids"])
        self.assertIsNone(catalogue["precision"])
        self.assertEqual(catalogue["unmatched_player_ids"], ["U2"])
        self.assertAlmostEqual(result["score"], 66.7)

    def test_complete_labels_count_wrong_circles(self):
        result = self.score("full manual labels, reviewed by Tiến", catalogue_coverage="complete")
        catalogue = result["vs_catalogue"]
        self.assertEqual(catalogue["wrong_ids"], ["U2"])
        self.assertAlmostEqual(catalogue["precision"], 0.6667)
        self.assertAlmostEqual(result["score"], 66.7)  # F1 = 2·2/(3+3)

    def test_wrong_sources_and_images_are_rejected(self):
        with self.assertRaises(ContractError):
            score_player(self.machine, self.machine, None, {}, metadata=METADATA)
        other = dict(self.player, image_id="other_image")
        with self.assertRaises(ContractError):
            score_player(other, self.machine, None, {}, metadata=METADATA)
        with self.assertRaises(ContractError):
            self.score(catalogue_coverage="all")
        with self.assertRaises(ContractError):
            self.score(matching="greedy")

    def test_empty_answer_scores_zero_on_reviewed_labels(self):
        self.player["circles"] = []
        result = self.score("reviewed by Tiến")
        self.assertEqual(result["score"], 0.0)
        self.assertEqual(result["vs_machine"]["matched"], 0)


if __name__ == "__main__":
    unittest.main()
