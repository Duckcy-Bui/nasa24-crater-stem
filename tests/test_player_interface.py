"""Independent acceptance checks for S1-09 player drafts and image coordinates."""

from __future__ import annotations

import copy
import json
import math
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

from src.contracts import ContractError, read_json, validate_crater_set
from src.player_annotations import (
    apply_canvas_event,
    build_player_crater_set,
    save_player_answers,
)


ROOT = Path(__file__).resolve().parents[1]


class PlayerAnnotationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with zipfile.ZipFile(ROOT / "data/s106_bundle/s106_lroc_browse_v2.zip") as bundle:
            cls.real_metadata = json.loads(bundle.read("moon_ap15_hia_c01.json"))

    def setUp(self):
        self.metadata = copy.deepcopy(self.real_metadata)
        self.circle = {"crater_id": "U1", "x": 128.0, "y": 300.0, "r": 25.0}
        self.draft = {"revision": 0, "circles": []}
        self.token = "isolated-image-session"

    def event(self, **changes):
        return {
            "image_id": self.metadata["image_id"],
            "session_token": self.token,
            "revision": 1,
            "circles": [copy.deepcopy(self.circle)],
            **changes,
        }

    def test_export_preserves_real_image_provenance_and_player_schema(self):
        result = build_player_crater_set([self.circle], self.metadata)
        self.assertEqual(result["image_id"], "moon_ap15_hia_c01")
        self.assertEqual(result["data_kind"], "real")
        self.assertEqual(result["schema_version"], "1.0")
        self.assertEqual(result["source"], "player")
        self.assertIsNone(result["reference_source"])
        self.assertEqual(result["circles"][0], {**self.circle, "confidence": None, "votes": None})
        validate_crater_set(result, self.metadata)
        self.assertEqual(json.loads(json.dumps(result, allow_nan=False)), result)

    def test_empty_answer_is_a_valid_player_answer_without_catalogue_claim(self):
        result = build_player_crater_set([], self.metadata)
        self.assertEqual(result["circles"], [])
        self.assertEqual(result["source"], "player")
        self.assertIsNone(result["reference_source"])
        self.assertEqual(self.metadata["reference_status"], "unavailable")
        validate_crater_set(result, self.metadata)

    def test_synthetic_fixture_keeps_its_declared_data_kind(self):
        metadata = read_json(ROOT / "data/examples/s105_synthetic_512.json")
        result = build_player_crater_set([self.circle], metadata)
        self.assertEqual(result["data_kind"], "synthetic")
        validate_crater_set(result, metadata)

    def test_circle_ids_do_not_change_when_circle_is_deleted_or_edited(self):
        circles = [self.circle, {"crater_id": "U7", "x": 450.0, "y": 200.0, "r": 40.0}]
        original = build_player_crater_set(circles, self.metadata)
        surviving = copy.deepcopy(original["circles"][1])
        surviving["x"] = 451.5
        result = build_player_crater_set([surviving], self.metadata)
        self.assertEqual(result["circles"][0]["crater_id"], "U7")
        self.assertEqual(result["circles"][0]["x"], 451.5)

    def test_geometry_rejects_nonfinite_bool_and_outside_centres(self):
        cases = [
            ("x", -0.001), ("x", 512), ("y", -1), ("y", 511.001),
            ("x", math.nan), ("y", math.inf), ("r", -math.inf),
            ("x", True), ("r", False), ("x", "128"),
            ("r", 0), ("r", -1),
        ]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                circle = {**self.circle, field: value}
                with self.assertRaises(ContractError):
                    build_player_crater_set([circle], self.metadata)

    def test_rim_can_cross_image_edge_when_centre_is_inside(self):
        circle = {**self.circle, "x": 0.0, "y": 511.0, "r": 150.0}
        result = build_player_crater_set([circle], self.metadata)
        self.assertEqual(result["circles"][0]["r"], 150.0)
        validate_crater_set(result, self.metadata)

    def test_ids_must_exist_be_strings_and_be_unique(self):
        cases = [
            [{k: v for k, v in self.circle.items() if k != "crater_id"}],
            [{**self.circle, "crater_id": ""}],
            [{**self.circle, "crater_id": 1}],
            [self.circle, copy.deepcopy(self.circle)],
        ]
        for circles in cases:
            with self.subTest(circles=circles), self.assertRaises(ContractError):
                build_player_crater_set(circles, self.metadata)

    def test_answer_requires_circle_objects_in_a_list(self):
        for circles in (None, "circles", {}, (self.circle,), [None], ["U1"]):
            with self.subTest(circles=circles), self.assertRaises(ContractError):
                build_player_crater_set(circles, self.metadata)

    def test_player_cannot_claim_machine_confidence_or_votes(self):
        for field, value in (("confidence", 0.9), ("votes", 12), ("votes", 0)):
            with self.subTest(field=field), self.assertRaises(ContractError):
                build_player_crater_set([{**self.circle, field: value}], self.metadata)

    def test_export_does_not_mutate_or_share_mutable_input(self):
        circles = [copy.deepcopy(self.circle)]
        original = copy.deepcopy(circles)
        result = build_player_crater_set(circles, self.metadata)
        self.assertEqual(circles, original)
        result["circles"][0]["x"] = 99
        self.assertEqual(circles, original)
        circles[0]["y"] = 77
        self.assertEqual(result["circles"][0]["y"], 300)

    def test_invalid_metadata_is_rejected_before_export(self):
        self.metadata["image_id"] = "../another-image"
        with self.assertRaises(ContractError):
            build_player_crater_set([self.circle], self.metadata)

    def test_valid_event_updates_revision_without_mutating_prior_draft(self):
        event = self.event()
        old = copy.deepcopy(self.draft)
        updated = apply_canvas_event(self.draft, event, self.metadata, self.token)
        self.assertEqual(self.draft, old)
        self.assertEqual(updated["revision"], 1)
        self.assertEqual(updated["circles"][0]["crater_id"], "U1")
        self.assertEqual(updated["circles"][0]["x"], 128)
        event["circles"][0]["x"] = 500
        self.assertEqual(updated["circles"][0]["x"], 128)

    def test_none_and_replayed_events_cannot_reset_existing_answers(self):
        draft = apply_canvas_event(self.draft, self.event(), self.metadata, self.token)
        for event in (None, self.event(circles=[]), self.event(revision=0, circles=[])):
            with self.subTest(event=event):
                self.assertEqual(apply_canvas_event(draft, event, self.metadata, self.token), draft)

    def test_cross_image_and_old_session_events_cannot_contaminate_draft(self):
        for event in (
            self.event(image_id="moon_ap15_hia_c02", revision=100, circles=[]),
            self.event(session_token="previous-component-instance", revision=100, circles=[]),
        ):
            with self.subTest(event=event):
                before = copy.deepcopy(self.draft)
                self.assertEqual(apply_canvas_event(self.draft, event, self.metadata, self.token), before)
                self.assertEqual(self.draft, before)

    def test_malformed_new_events_are_rejected_without_partial_updates(self):
        cases = [
            self.event(revision=True), self.event(revision=1.5),
            self.event(revision="1"), self.event(circles={}),
            self.event(circles=[{**self.circle, "r": 0}]),
            self.event(circles=[self.circle, copy.deepcopy(self.circle)]),
        ]
        for event in cases:
            with self.subTest(event=event):
                before = copy.deepcopy(self.draft)
                with self.assertRaises(ContractError):
                    apply_canvas_event(self.draft, event, self.metadata, self.token)
                self.assertEqual(self.draft, before)

    def test_delete_and_edit_events_keep_original_coordinate_units(self):
        first = apply_canvas_event(self.draft, self.event(), self.metadata, self.token)
        moved = {**self.circle, "x": 255.5, "y": 511.0, "r": 12.25}
        edited = apply_canvas_event(first, self.event(revision=2, circles=[moved]), self.metadata, self.token)
        self.assertEqual(edited["revision"], 2)
        self.assertEqual(edited["circles"][0]["crater_id"], "U1")
        self.assertEqual(tuple(edited["circles"][0][f] for f in ("x", "y", "r")), (255.5, 511.0, 12.25))
        deleted = apply_canvas_event(edited, self.event(revision=3, circles=[]), self.metadata, self.token)
        self.assertEqual(deleted, {"revision": 3, "circles": []})
        self.assertEqual(first["circles"][0]["x"], 128.0)

    def test_saved_answer_can_be_read_by_the_shared_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = save_player_answers(tmp, self.metadata, [self.circle], run_id="player_test_01")
            self.assertEqual(directory.parent, Path(tmp))
            self.assertEqual(directory.name, "player_test_01")
            result = read_json(directory / "craters.json")
            validate_crater_set(result, read_json(directory / "metadata.json"))
            self.assertEqual(result["source"], "player")
            self.assertEqual(result["image_id"], self.metadata["image_id"])
            self.assertEqual(read_json(directory / "run.json")["image_id"], self.metadata["image_id"])

    def test_repeated_manual_save_cannot_overwrite_an_existing_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = save_player_answers(tmp, self.metadata, [self.circle], run_id="player_repeat")
            saved = {p.name: p.read_bytes() for p in directory.iterdir()}
            with self.assertRaises(FileExistsError):
                save_player_answers(tmp, self.metadata, [], run_id="player_repeat")
            self.assertEqual(saved, {p.name: p.read_bytes() for p in directory.iterdir()})

    def test_automatic_saves_produce_separate_recoverable_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = save_player_answers(tmp, self.metadata, [self.circle])
            second = save_player_answers(tmp, self.metadata, [])
            self.assertNotEqual(first, second)
            self.assertEqual(len(read_json(first / "craters.json")["circles"]), 1)
            self.assertEqual(read_json(second / "craters.json")["circles"], [])

    def test_invalid_save_leaves_no_partial_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ContractError):
                save_player_answers(tmp, self.metadata, [{**self.circle, "r": math.nan}], run_id="invalid")
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_save_run_id_cannot_escape_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ContractError):
                save_player_answers(tmp, self.metadata, [self.circle], run_id="../escape")
            self.assertEqual(list(Path(tmp).iterdir()), [])


@unittest.skipUnless(shutil.which("node"), "Node is needed for the independent canvas geometry checks")
class CanvasGeometryTests(unittest.TestCase):
    def test_display_sizes_offsets_and_original_image_geometry(self):
        completed = subprocess.run(
            [shutil.which("node"), str(ROOT / "tests/test_canvas_geometry.js")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("Canvas geometry acceptance checks passed", completed.stdout)

    def test_delayed_load_acknowledgements_and_edit_events(self):
        completed = subprocess.run(
            [shutil.which("node"), str(ROOT / "tests/test_canvas_events.js")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("Canvas event acceptance checks passed", completed.stdout)


if __name__ == "__main__":
    unittest.main()
