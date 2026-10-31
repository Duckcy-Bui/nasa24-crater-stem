"""Failure handling and scientific/configuration contracts of the S3-10 entry point."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, patch

from scripts import reproduce_s310 as runner
from scripts import s207_experiments as experiments


class ReproductionTests(unittest.TestCase):
    def test_failed_stage_is_recorded_and_stops_pipeline(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "run"
            process = Mock(return_value=subprocess.CompletedProcess([], 9))
            # Replace only the runner's reference; platform's Linux uname probe
            # and other standard-library subprocess users must keep working.
            stage_subprocess = SimpleNamespace(run=process, STDOUT=subprocess.STDOUT)
            with patch.object(runner, "identities", return_value={}), patch.object(
                runner, "subprocess", stage_subprocess
            ), patch.object(runner, "git", return_value="test"), contextlib.redirect_stdout(io.StringIO()):
                probe = subprocess.check_output(
                    [sys.executable, "-c", "print('platform-probe')"], text=True
                )
                self.assertEqual(probe.strip(), "platform-probe")
                with self.assertRaisesRegex(RuntimeError, "dataset failed"):
                    runner.main(["--quick", "--output", str(out)])
            report = runner.read(out / "manifest.json")
            self.assertEqual(report["status"], "failed")
            self.assertEqual(report["stages"][0]["returncode"], 9)
            self.assertEqual(process.call_count, 1)
            self.assertEqual(process.call_args.kwargs["cwd"], runner.ROOT)
            self.assertEqual(process.call_args.kwargs["env"]["PYTHONHASHSEED"], "0")

    def test_existing_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "manifest.json"
            marker.write_text("original", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                runner.main(["--output", tmp])
            self.assertEqual(marker.read_text(encoding="utf-8"), "original")

    def test_experiment_csv_retains_unavailable_metrics(self):
        metrics = {"known_labels": 2, "true_positive_known": 1, "recall_known": 0.5, "hit_max_circles": True}
        branch = {"recall": metrics, "candidates_kept": 3, "candidates_removed": 1}
        report = {"results": [{"image_id": "image", "split": "tuning",
            "experiment_1_s111": {"baseline": metrics, "with_s111_annotation": metrics,
                "remove_inverted_experiment": branch, "status": "diagnostic_tuning_only"},
            "experiment_2_parameters": [{"variant": "baseline", "candidates": 4, "seconds_hough": 0.1, "recall": metrics}],
            "experiment_3_hard_cases": {"remove_texture": branch, "dedupe": branch}}]}
        with tempfile.TemporaryDirectory() as tmp:
            runner.export_experiments(report, Path(tmp))
            import csv
            for name, expected in (("E1.csv", 3), ("E2.csv", 1), ("E3.csv", 2)):
                with (Path(tmp) / name).open(encoding="utf-8", newline="") as stream:
                    rows = list(csv.DictReader(stream))
                self.assertEqual(len(rows), expected)
                self.assertEqual(rows[0]["recall_known"], "0.5")
                self.assertEqual(rows[0]["precision"], "")
                self.assertEqual(rows[0]["f1"], "")

    def test_experiment_output_can_be_outside_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "results.json"
            with patch.object(experiments, "run_one", return_value={}), contextlib.redirect_stdout(io.StringIO()):
                code = experiments.main(["--images", experiments.DEFAULT_IMAGES[0], "--output", str(output), "--write"])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["results"], [{}])

    def test_chosen_holdout_config_applies_to_all_experiments(self):
        config = {"hough": {"min_votes": 23}, "preprocess": {"gauss_sigma": 2.0}}
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            with patch.object(experiments, "run_one", return_value={}) as run, contextlib.redirect_stdout(io.StringIO()):
                experiments.main(["--holdout", "--chosen-config", str(config_path), "--config", str(config_path)])
            self.assertEqual(run.call_count, len(experiments.DEFAULT_HOLDOUT_IMAGES))
            for call in run.call_args_list:
                effective = call.kwargs["config"]
                self.assertEqual(effective["hough"]["min_votes"], 23)
                self.assertEqual(effective["preprocess"], config["preprocess"])
                self.assertEqual(list(call.kwargs["parameter_variants"]), ["chosen_on_tuning"])


if __name__ == "__main__":
    unittest.main()
