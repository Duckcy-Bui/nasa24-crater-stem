"""S1-13: chạy từ đầu đến cuối trên cảnh giả lập có đáp án biết trước (không phải ảnh NASA)."""
import json
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
import numpy as np

from src.contracts import ContractError, read_json, validate_crater_set
from src.pipeline import find_player_answer, run_end_to_end
from src.player_annotations import build_player_crater_set, save_player_answers

ROOT = Path(__file__).resolve().parents[1]
TRUTH = ((160, 180, 32), (350, 310, 20))  # synthetic layout check, not ground truth for NASA images


class TestEndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.processed, self.outputs, self.players = root / "processed", root / "outputs", root / "player_answers"
        self.processed.mkdir()
        self.metadata = read_json(ROOT / "data" / "examples" / "s105_synthetic_512.json")
        self.image_id = self.metadata["image_id"]
        (self.processed / f"{self.image_id}.json").write_text(json.dumps(self.metadata), encoding="utf-8")
        yy, xx = np.indices((512, 512))
        image = np.full((512, 512), 0.35, dtype=np.float32)
        for x, y, r in TRUTH:
            image[np.hypot(xx - x, yy - y) <= r] = 0.85
        np.save(self.processed / f"{self.image_id}.npy", image)

    def tearDown(self):
        self.tmp.cleanup()

    def run_pipeline(self, **kwargs):
        return run_end_to_end(self.image_id, processed_dir=self.processed, output_root=self.outputs,
                              code_version="test", hough_params={"r_max_limit_px": 40}, **kwargs)

    def test_machine_circles_saved_with_every_artifact(self):
        directory, summary = self.run_pipeline()
        for name in ("metadata.json", "params.json", "craters.json", "run.json", "summary.json", "arrays.npz", "overlay.png"):
            self.assertTrue((directory / name).exists(), name)
        machine = read_json(directory / "craters.json")
        validate_crater_set(machine, self.metadata)
        self.assertEqual(machine["source"], "machine")
        self.assertIsNone(machine["reference_source"])
        for x, y, r in TRUTH:
            self.assertTrue(any(abs(c["x"] - x) <= 2 and abs(c["y"] - y) <= 2 and abs(c["r"] - r) <= 2
                                for c in machine["circles"]), (x, y, r))
        self.assertEqual(summary["steps"]["hough"]["r_min_px"], 10)
        self.assertEqual(summary["steps"]["hough"]["r_max_px"], 40)

    def test_scoring_and_unimplemented_filtering_are_reported_as_skipped(self):
        _, summary = self.run_pipeline(render=False)
        self.assertEqual(summary["steps"]["postprocess"]["status"], "skipped")
        self.assertEqual(summary["steps"]["scoring"]["status"], "skipped")
        self.assertIn("không phải đáp án", summary["steps"]["scoring"]["reason"])

    def test_player_answer_is_drawn_beside_but_never_merged_into_machine(self):
        player = build_player_crater_set([{"crater_id": "U1", "x": 160.0, "y": 180.0, "r": 30.0}], self.metadata)
        older = save_player_answers(self.players, self.metadata, player["circles"], run_id="player_20261015T000000_a")
        newer = save_player_answers(self.players, self.metadata, player["circles"][:0], run_id="player_20261015T010000_b")
        self.assertEqual(find_player_answer(self.image_id, self.players), newer / "craters.json")
        directory, summary = self.run_pipeline(player_path=older / "craters.json", render=False)
        self.assertEqual(summary["steps"]["player"]["circles"], 1)
        self.assertEqual(read_json(directory / "player.json")["source"], "player")
        self.assertTrue(all(c["crater_id"].startswith("M") for c in read_json(directory / "craters.json")["circles"]))

    def test_player_search_ignores_other_images(self):
        other = dict(self.metadata, image_id="other_image")
        save_player_answers(self.players, other, [], run_id="player_20261015T020000_c")
        self.assertIsNone(find_player_answer(self.image_id, self.players))

    def test_overlay_file_with_wrong_source_is_rejected(self):
        player = build_player_crater_set([], self.metadata)
        path = Path(self.tmp.name) / "player.json"
        path.write_text(json.dumps(player), encoding="utf-8")
        with self.assertRaises(ContractError):
            self.run_pipeline(reference_path=path, render=False)
        self.assertFalse(self.outputs.exists())

    def test_valid_mask_is_loaded_and_used(self):
        mask = np.ones((512, 512), dtype=bool)
        mask[:, :256] = False  # left half is nodata: the left disk must disappear
        np.save(self.processed / f"{self.image_id}_valid_mask.npy", mask)
        directory, summary = self.run_pipeline(render=False)
        self.assertTrue(summary["steps"]["load"]["valid_mask"])
        self.assertLess(summary["steps"]["preprocess"]["valid_ratio"], 0.6)
        circles = read_json(directory / "craters.json")["circles"]
        self.assertFalse(any(c["x"] < 250 for c in circles))
        self.assertTrue(any(abs(c["x"] - 350) <= 2 and abs(c["y"] - 310) <= 2 for c in circles))

    def test_reference_labels_are_drawn_with_their_review_status(self):
        reference = {"schema_version": "1.0", "data_kind": self.metadata["data_kind"], "image_id": self.image_id,
                     "source": "catalogue", "reference_source": "manual_label_s110; sparse manual labels, unreviewed",
                     "circles": [{"crater_id": "C1", "x": 160.0, "y": 180.0, "r": 32.0, "confidence": None, "votes": None}]}
        path = Path(self.tmp.name) / "reference.json"
        path.write_text(json.dumps(reference), encoding="utf-8")
        directory, summary = self.run_pipeline(reference_path=path, render=False)
        self.assertEqual(summary["steps"]["reference"]["circles"], 1)
        self.assertFalse(summary["steps"]["reference"]["reviewed"])
        self.assertEqual(read_json(directory / "reference.json")["source"], "catalogue")
        self.assertEqual(read_json(directory / "craters.json")["source"], "machine")

    def test_failure_after_saving_removes_the_half_written_run(self):
        from unittest import mock
        with mock.patch("src.pipeline.render_overlay", side_effect=RuntimeError("matplotlib failed")):
            with self.assertRaises(RuntimeError):
                self.run_pipeline()
        self.assertEqual(list(self.outputs.iterdir()), [])

    def test_latest_player_answer_uses_run_time_not_folder_name(self):
        player = build_player_crater_set([{"crater_id": "U1", "x": 160.0, "y": 180.0, "r": 30.0}], self.metadata)
        late = save_player_answers(self.players, self.metadata, player["circles"], run_id="player_20261015T000000_a")
        early = save_player_answers(self.players, self.metadata, [], run_id="player_20261015T000000_b")
        for directory, stamp in ((late, "2026-10-15T00:00:00.900000+00:00"), (early, "2026-10-15T00:00:00.100000+00:00")):
            run = read_json(directory / "run.json")
            run["created_at_utc"] = stamp
            (directory / "run.json").write_text(json.dumps(run), encoding="utf-8")
        (self.players / "broken").mkdir()
        (self.players / "broken" / "craters.json").write_text("[1, 2]", encoding="utf-8")
        self.assertEqual(find_player_answer(self.image_id, self.players), late / "craters.json")


class TestEndToEndCli(unittest.TestCase):
    def test_player_file_is_rejected_with_all_or_no_player(self):
        from scripts.run_end_to_end import main
        for argv in (["--all", "--player", "x.json"], ["some_image", "--player", "x.json", "--no-player"]):
            with self.assertRaises(SystemExit) as raised, mock_stderr():
                main(argv)
            self.assertEqual(raised.exception.code, 2, argv)


def mock_stderr():
    import contextlib
    import io
    return contextlib.redirect_stderr(io.StringIO())


if __name__ == "__main__":
    unittest.main()
