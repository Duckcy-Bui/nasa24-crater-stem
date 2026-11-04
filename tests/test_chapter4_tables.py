"""Chapter 4 exports use saved fixtures; no Hough or processed data needed."""
import contextlib
import hashlib
import io
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from scripts import export_chapter4_tables as tables
from scripts import reproduce_s310 as runner

ROOT = Path(__file__).resolve().parents[1]


class Chapter4TablesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.run_dir = Path(self.temp.name) / "run"
        self.run_dir.mkdir()
        tables.save_json(self.run_dir / "manifest.json", {
            "mode": "full", "base_commit": "fixture", "seed": 0,
        })
        for split in ("tuning", "holdout"):
            dest = self.run_dir / f"evaluation_{split}"
            dest.mkdir()
            shutil.copyfile(
                ROOT / "docs/evidence/s3-10/full" /
                f"evaluation_{split}/summary.json",
                dest / "summary.json")
        (self.run_dir / "s305").mkdir()
        for name in ("report.json", "E1.csv", "E2.csv", "E3.csv"):
            shutil.copyfile(ROOT / "docs/evidence/s3-05" / name,
                            self.run_dir / "s305" / name)
        (self.run_dir / "density").mkdir()
        shutil.copyfile(ROOT / "docs/evidence/s3-03/mat_do/so_sanh.json",
                        self.run_dir / "density/so_sanh.json")
        tables.snapshot_blind_labels(ROOT, self.run_dir / "blind_filter")

    def export(self, name):
        tables.export_tables(self.run_dir)
        return tables.read_csv(self.run_dir / f"chapter4_tables/{name}.csv")

    def test_registry_has_five_tables_and_authenticates_inputs_outputs(self):
        index = tables.export_tables(self.run_dir)
        self.assertEqual(index["status"], "complete")
        self.assertEqual(
            [(r["table_id"], r["file"], r["rows"]) for r in index["tables"]],
            [("4.4", "table_4_4.csv", 11), ("4.5", "table_4_5.csv", 8),
             ("4.6", "table_4_6.csv", 6), ("4.7", "table_4_7.csv", 9),
             ("4.8", "table_4_8.csv", 2)])
        self.assertEqual(index["tables"][1]["mode"], "historical_blind_labels")
        for row in index["tables"]:
            self.assertEqual(tables.sha(self.run_dir / "chapter4_tables" /
                                        row["file"]), row["sha256"])
            for path, digest in row["inputs_sha256"].items():
                self.assertFalse(Path(path).is_absolute())
                self.assertEqual(tables.sha(self.run_dir / path), digest)

    def test_s305_pools_identical_images_and_keeps_unknown_metrics_blank(self):
        rows = self.export("table_4_4")
        actual = {(r["experiment"], r["scope"], r["variant"]):
                  (int(r["n_images"]), int(r["candidates"]),
                   int(r["tp_known"]), int(r["known_labels"])) for r in rows}
        expected = {
            ("E1", "tuning", "raw"): (2, 200, 1, 20),
            ("E1", "tuning", "shading_annotation"): (2, 200, 1, 20),
            ("E1", "tuning", "remove_inverted"): (2, 151, 0, 20),
            ("E2", "tuning", "baseline"): (3, 300, 1, 30),
            ("E2", "tuning", "min_vote_ratio_030"): (3, 300, 1, 30),
            ("E2", "tuning", "min_vote_ratio_040"): (3, 300, 1, 30),
            ("E2", "tuning", "radius_step_2"): (3, 300, 1, 30),
            ("E3", "tuning", "baseline"): (3, 300, 1, 30),
            ("E3", "tuning", "remove_texture"): (3, 155, 1, 30),
            ("E3", "tuning", "dedupe"): (3, 284, 1, 30),
            ("E3", "holdout_descriptive", "baseline"): (1, 100, 0, 6),
        }
        self.assertEqual(actual, expected)
        self.assertTrue(all(r["precision"] == r["f1"] == "" for r in rows))

    def test_hough_sample_sd_and_separate_datasets(self):
        rows = self.export("table_4_6")
        actual = [(r["split"], r["method"], int(r["known_labels"]),
                   float(r["recall_pooled_pct"]), float(r["recall_mean_pct"]),
                   float(r["recall_sd_pct"])) for r in rows]
        self.assertEqual(actual, [
            ("tuning", "numpy_score", 28, 0.0, 0.0, 0.0),
            ("tuning", "numpy_balanced", 28, 7.14, 7.41, 6.42),
            ("tuning", "opencv", 28, 96.43, 96.67, 5.77),
            ("holdout", "numpy_score", 66, 6.06, 5.95, 8.77),
            ("holdout", "numpy_balanced", 66, 7.58, 7.64, 8.88),
            ("holdout", "opencv", 66, 98.48, 98.21, 5.05),
        ])

    def test_export_rejects_inconsistent_recall_probe(self):
        """Recall 0,9 với TP=0/FN=9 phải bị chặn trước summarize và xuất CSV."""
        path = self.run_dir / "evaluation_tuning/summary.json"
        report = tables.read_json(path)
        row = report["images"][0]["methods"]["numpy_score"]
        self.assertEqual((row["tp"], row["fn"]), (0, 9))
        row["recall"] = 0.9
        tables.save_json(path, report)
        with patch.object(tables, "summarize", wraps=tables.summarize) as summarize:
            with self.assertRaisesRegex(ValueError, "Recall_known.*TP/FN"):
                tables.export_tables(self.run_dir)
            summarize.assert_not_called()
        self.assertFalse((self.run_dir / "chapter4_tables").exists())

    def test_hough_counts_and_finite_recall_are_required(self):
        """Dữ liệu sai kiểu/miền hoặc recall không hữu hạn phải bị từ chối."""
        invalid = [
            {"tp": -1, "fn": 9, "recall": 0.0},
            {"tp": 0, "fn": -1, "recall": 0.0},
            {"tp": True, "fn": 9, "recall": 0.1},
            {"tp": 0, "fn": 9.0, "recall": 0.0},
            {"tp": "0", "fn": 9, "recall": 0.0},
            {"tp": 0, "fn": 9, "recall": None},
            {"tp": 0, "fn": 9, "recall": float("nan")},
            {"tp": 0, "fn": 9, "recall": float("inf")},
            {"tp": 0, "fn": 9, "recall": False},
        ]
        for row in invalid:
            with self.subTest(row=row), self.assertRaises(ValueError):
                tables.validate_hough_recall([row])

    def test_hough_recall_tolerance(self):
        """Chấp nhận sai số trong 1e-9, chặn sai số vượt dung sai."""
        self.assertIsNone(tables.validate_hough_recall([
            {"tp": 1, "fn": 1, "recall": 0.5 + 5e-10},
        ]))
        with self.assertRaisesRegex(ValueError, "inconsistent"):
            tables.validate_hough_recall([
                {"tp": 1, "fn": 1, "recall": 0.5 + 2e-9},
            ])

    def test_hough_zero_labels_are_rejected(self):
        """TP+FN=0 không có Recall_known, không đưa vào mean/SD."""
        for recall in (None, 0.0, float("nan")):
            with self.subTest(recall=recall):
                with self.assertRaisesRegex(ValueError, "TP\\+FN=0"):
                    tables.validate_hough_recall([{"tp": 0, "fn": 0, "recall": recall}])

    def test_holdout_pivots_json_candidate_counts_and_has_total_row(self):
        rows = self.export("table_4_7")
        self.assertEqual([int(r["opencv_candidates"]) for r in rows[:-1]],
                         [8195, 8323, 8438, 9040, 9086, 8259, 8521, 8866])
        total = rows[-1]
        self.assertEqual(total["image_id"], "TOTAL")
        self.assertEqual(total["known_labels"], "66")
        self.assertEqual([(total[m + "_tp"], total[m + "_fn"])
                          for m in tables.METHODS],
                         [("4", "62"), ("5", "61"), ("65", "1")])
        self.assertEqual(total["opencv_candidates"], "")

    def test_blind_label_copies_and_unavailable_shading(self):
        rows = self.export("table_4_5")
        manifest = tables.read_json(
            self.run_dir / "blind_filter/manifest.json")
        for image_id in tables.BLIND_IMAGES:
            source = ROOT / f"docs/evidence/s2-02/{image_id}/report.json"
            copy = self.run_dir / f"blind_filter/{image_id}.json"
            self.assertEqual(copy.read_bytes(), source.read_bytes())
            self.assertEqual(manifest["reports"][copy.name]["sha256"],
                             hashlib.sha256(source.read_bytes()).hexdigest())
        self.assertEqual((rows[2]["removed"], rows[2]["rim_removed"],
                          rows[2]["rim_fraction_pct"]), ("61", "1", "21.2"))
        self.assertEqual(rows[-1]["status"], "not_evaluable_no_sun")
        self.assertEqual(rows[-1]["removed"], "")
        self.assertEqual(rows[-1]["rim_removed"], "")
        self.assertEqual(rows[-1]["rim_fraction_pct"], "20.5")

    def test_density_rounds_precise_json_and_preserves_manual_counts(self):
        rows = self.export("table_4_8")
        self.assertEqual([(r["area_km2"], r["n"], r["density_per_km2"],
                           r["ci95_low"], r["ci95_high"]) for r in rows],
                         [("184.7", "73", "0.395", "0.310", "0.497"),
                          ("123.0", "43", "0.350", "0.253", "0.471")])

    def test_duplicate_and_holdout_filter_rows_are_rejected(self):
        path = self.run_dir / "s305/E3.csv"
        rows = tables.read_csv(path)
        tables.write_csv(path, [*rows, rows[0]])
        with self.assertRaisesRegex(ValueError, "scope"):
            tables.export_tables(self.run_dir)
        rows[-1]["variant"] = "dedupe"
        tables.write_csv(path, rows)
        with self.assertRaisesRegex(ValueError, "scope"):
            tables.export_tables(self.run_dir)
        self.assertFalse((self.run_dir / "chapter4_tables").exists())

    def test_precision_zero_is_not_allowed_for_sparse_labels(self):
        path = self.run_dir / "s305/E2.csv"
        rows = tables.read_csv(path)
        rows[0]["precision"] = "0"
        tables.write_csv(path, rows)
        with self.assertRaisesRegex(ValueError, "sparse-label"):
            tables.export_tables(self.run_dir)

    def test_missing_evaluation_image_and_quick_mode_do_not_export(self):
        path = self.run_dir / "evaluation_holdout/summary.json"
        report = tables.read_json(path)
        report["images"].pop()
        tables.save_json(path, report)
        with self.assertRaisesRegex(ValueError, "Incomplete evaluation"):
            tables.export_tables(self.run_dir)
        tables.save_json(self.run_dir / "manifest.json", {"mode": "quick"})
        with self.assertRaisesRegex(ValueError, "full run"):
            tables.export_tables(self.run_dir)
        self.assertFalse((self.run_dir / "chapter4_tables").exists())

    def test_tampered_blind_snapshot_and_existing_output_are_rejected(self):
        with self.assertRaises(FileExistsError):
            tables.snapshot_blind_labels(ROOT, self.run_dir / "blind_filter")
        path = self.run_dir / f"blind_filter/{tables.BLIND_IMAGES[0]}.json"
        path.write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "hash differs"):
            tables.export_tables(self.run_dir)


class RunnerCoverageTests(unittest.TestCase):
    def check_stages(self, quick):
        """Fake children to test orchestration without images or Hough."""
        original_read = runner.read

        def stage_data(path):
            if path.name.startswith("experiments_"):
                return {"results": []}
            if (path.parent.name == "frozen_tuning"
                    and path.name == "report.json"):
                return {"status": "complete", "images": [{
                    "image_id": "fixture", "metrics":
                    {"tp": 1, "fn": 1, "recall": 0.5}}]}
            if path.name == "index.json":
                return {"status": "complete", "tables": []}
            return original_read(path)

        process = Mock(return_value=subprocess.CompletedProcess([], 0))
        fake = SimpleNamespace(run=process, STDOUT=subprocess.STDOUT)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "run"
            with patch.object(runner, "identities", return_value={}), \
                    patch.object(runner, "subprocess", fake), \
                    patch.object(runner, "git", return_value="fixture"), \
                    patch.object(runner, "read", side_effect=stage_data), \
                    patch.object(runner, "export_experiments"), \
                    contextlib.redirect_stdout(io.StringIO()):
                args = ["--output", str(out)] + (["--quick"] if quick else [])
                runner.main(args)
            manifest = original_read(out / "manifest.json")
            self.assertEqual(manifest["status"], "complete")
            self.assertTrue(all(c.kwargs["env"]["PYTHONHASHSEED"] == "0"
                                for c in process.call_args_list))
            return [s["name"] for s in manifest["stages"]]

    def test_full_keeps_old_eight_stages_and_adds_three(self):
        self.assertEqual(self.check_stages(False), [
            "dataset", "synthetic", "frozen_tuning", "evaluation_tuning",
            "experiments_tuning", "evaluation_holdout", "experiments_holdout",
            "density", "s305", "blind_filter", "chapter4_tables"])

    def test_quick_keeps_old_scope_without_new_full_tables(self):
        self.assertEqual(self.check_stages(True), [
            "dataset", "synthetic", "frozen_tuning", "evaluation_tuning",
            "experiments_tuning", "density"])


if __name__ == "__main__":
    unittest.main()
