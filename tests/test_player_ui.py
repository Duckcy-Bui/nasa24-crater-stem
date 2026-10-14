"""Save-request acceptance with real bundle metadata and temporary run files.

Backend checks only; browser behavior and crater ground truth remain separate.
"""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

from src.contracts import ContractError, validate_crater_set
from src.player_annotations import save_player_answers
from src.player_ui import handle_save_request

ROOT = Path(__file__).resolve().parents[1]


class SaveRequestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with zipfile.ZipFile(ROOT / "data/s106_bundle/s106_lroc_browse_v2.zip") as bundle:
            cls.real_metadata = json.loads(bundle.read("moon_ap15_hia_c01.json"))

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name) / "runs"
        self.metadata = copy.deepcopy(self.real_metadata)
        self.token = "current-player-session"
        self.circle = {"crater_id": "U7", "x": 300.5, "y": 99.25, "r": 30.75}
        self.draft = {"revision": 1, "circles": [copy.deepcopy(self.circle)]}
        self.state = {"handled_nonces": [], "result": None}

    def event(self, **changes):
        return {"image_id": self.metadata["image_id"], "session_token": self.token,
                "revision": self.draft["revision"], "circles": copy.deepcopy(self.draft["circles"]),
                "save_nonce": "click-1", **changes}

    def request(self, event, state=None):
        return handle_save_request(self.draft, event, self.metadata, self.token,
                                   self.state if state is None else state, self.output)

    def disk(self):
        return {str(p.relative_to(self.output)): p.read_bytes()
                for p in self.output.rglob("*") if p.is_file()} if self.output.is_dir() else {}

    def runs(self):
        return sorted(self.output.iterdir()) if self.output.is_dir() else []

    def test_valid_save_preserves_contract_and_inputs_and_returns_relative_ack(self):
        event = self.event(circles=[{**self.circle, "confidence": None, "votes": None}])
        before = copy.deepcopy((self.draft, event, self.metadata, self.state))
        saved = self.request(event)
        self.assertEqual((self.draft, event, self.metadata, self.state), before)
        self.assertEqual(saved["handled_nonces"], ["click-1"])
        result = saved["result"]
        self.assertTrue(result["ok"])
        self.assertEqual((result["nonce"], result["revision"], result["image_id"], result["count"]),
                         ("click-1", 1, self.metadata["image_id"], 1))
        self.assertRegex(result["time"], r"^\d{2}:\d{2}$")
        directory, = self.runs()
        self.assertEqual({p.name for p in directory.iterdir()},
                         {"craters.json", "metadata.json", "params.json", "run.json"})
        self.assertEqual(result["path"], str(Path("outputs/player_answers") / directory.name))
        self.assertFalse(Path(result["path"]).is_absolute())
        answer = json.loads((directory / "craters.json").read_text())
        metadata = json.loads((directory / "metadata.json").read_text())
        validate_crater_set(answer, metadata)
        self.assertEqual((answer["source"], answer["data_kind"], answer["image_id"]),
                         ("player", "real", self.metadata["image_id"]))
        self.assertIsNone(answer["reference_source"])
        self.assertEqual(answer["circles"], [{**self.circle, "confidence": None, "votes": None}])
        self.assertEqual(metadata["reference_status"], "unavailable")
        saved["handled_nonces"].append("another-click")
        self.assertEqual(self.state, {"handled_nonces": [], "result": None})

    def test_empty_player_answer_can_be_saved_at_revision_zero(self):
        self.draft = {"revision": 0, "circles": []}
        saved = self.request(self.event())
        self.assertTrue(saved["result"]["ok"])
        self.assertEqual(saved["result"]["count"], 0)
        answer = json.loads((self.runs()[0] / "craters.json").read_text())
        self.assertEqual(answer["circles"], [])
        self.assertEqual(answer["source"], "player")

    def test_new_click_makes_separate_run_and_old_nonce_after_new_nonce_never_resaves(self):
        first = self.request(self.event())
        frozen = self.disk()
        second = self.request(self.event(save_nonce="click-2"), first)
        second_frozen = self.disk()
        self.assertEqual(len(self.runs()), 2)
        self.assertNotEqual(first["result"]["path"], second["result"]["path"])
        self.assertTrue(all(second_frozen[name] == data for name, data in frozen.items()))
        for nonce in ("click-1", "click-2", "click-1"):
            with self.subTest(nonce=nonce):
                self.assertEqual(self.request(self.event(save_nonce=nonce), second), second)
                self.assertEqual(self.disk(), second_frozen)

    def test_edit_without_explicit_nonce_never_saves(self):
        events = (None, [], "save", {k: v for k, v in self.event().items() if k != "save_nonce"})
        for event in events:
            with self.subTest(event=event):
                self.assertEqual(self.request(event), self.state)
                self.assertFalse(self.output.exists())

    def test_invalid_nonce_preserves_prior_ack_and_files(self):
        saved = self.request(self.event())
        frozen = self.disk()
        for nonce in (None, "", "x" * 65, True, 12, [], {}):
            with self.subTest(nonce=nonce):
                self.assertEqual(self.request(self.event(save_nonce=nonce), saved), saved)
                self.assertEqual(self.disk(), frozen)

    def test_nonce_length_boundaries_are_valid_and_nonce_is_not_an_output_path(self):
        state = self.state
        for nonce in ("x", "x" * 64, "../a-click"):
            with self.subTest(nonce=nonce):
                state = self.request(self.event(save_nonce=nonce), state)
                self.assertTrue(state["result"]["ok"])
                self.assertIn(nonce, state["handled_nonces"])
        self.assertEqual(len(self.runs()), 3)
        self.assertTrue(all(p.parent == self.output for p in self.runs()))

    def test_wrong_image_or_session_ignores_request_even_if_circles_are_malformed(self):
        saved = self.request(self.event())
        frozen = self.disk()
        for changes in ({"image_id": "moon_ap15_hia_c02"},
                        {"session_token": "old-session"}, {"session_token": None}):
            with self.subTest(changes=changes):
                event = self.event(save_nonce="other-click", circles=None, **changes)
                self.assertEqual(self.request(event, saved), saved)
                self.assertEqual(self.disk(), frozen)

    def test_old_future_or_noninteger_revision_cannot_write_or_consume_nonce(self):
        for revision in (0, 2, -1, True, 1.0, "1", None):
            with self.subTest(revision=revision):
                self.assertEqual(self.request(self.event(revision=revision)), self.state)
                self.assertFalse(self.output.exists())

    def test_equal_revision_with_different_valid_snapshot_is_ignored(self):
        for circles in ([], [{**self.circle, "x": 300.75}], [{**self.circle, "crater_id": "U8"}]):
            with self.subTest(circles=circles):
                self.assertEqual(self.request(self.event(circles=circles)), self.state)
                self.assertFalse(self.output.exists())

    def test_malformed_matching_circles_raise_before_io_or_nonce_consumption(self):
        cases = (None, {}, [None], [{**self.circle, "r": 0}],
                 [{**self.circle, "x": float("nan")}], [self.circle, self.circle],
                 [{**self.circle, "confidence": .9}])
        for circles in cases:
            with self.subTest(circles=circles):
                with patch("src.player_ui.save_player_answers") as saver:
                    with self.assertRaises(ContractError):
                        self.request(self.event(circles=circles))
                    saver.assert_not_called()
                self.assertEqual(self.state, {"handled_nonces": [], "result": None})
                self.assertFalse(self.output.exists())

    def test_consumed_nonce_replay_keeps_latest_ack_without_revalidating_payload(self):
        saved = self.request(self.event())
        frozen = self.disk()
        self.assertEqual(self.request(self.event(circles=None), saved), saved)
        self.assertEqual(self.disk(), frozen)

    def test_io_error_consumes_click_rerun_does_not_retry_but_new_click_can(self):
        self.output.write_text("block directory creation")
        failed = self.request(self.event())
        self.assertFalse(failed["result"]["ok"])
        self.assertTrue(failed["result"]["error"])
        self.assertEqual(failed["handled_nonces"], ["click-1"])
        self.assertEqual((failed["result"]["nonce"], failed["result"]["revision"],
                          failed["result"]["image_id"]), ("click-1", 1, self.metadata["image_id"]))
        self.output.unlink()
        self.assertEqual(self.request(self.event(), failed), failed)
        self.assertFalse(self.output.exists(), "IO recovery must not retry a consumed click")
        retried = self.request(self.event(save_nonce="click-2"), failed)
        self.assertTrue(retried["result"]["ok"])
        self.assertEqual(retried["handled_nonces"], ["click-1", "click-2"])
        self.assertEqual(len(self.runs()), 1)
        self.assertEqual(self.request(self.event(), retried), retried)

    def test_existing_run_is_immutable_and_collision_is_consumed(self):
        def fixed_run(output, metadata, circles):
            return save_player_answers(output, metadata, circles, run_id="fixed_run")

        with patch("src.player_ui.save_player_answers", side_effect=fixed_run):
            saved = self.request(self.event())
            frozen = self.disk()
            collision = self.request(self.event(save_nonce="click-2"), saved)
            self.assertFalse(collision["result"]["ok"])
            self.assertEqual(collision["handled_nonces"], ["click-1", "click-2"])
            self.assertEqual(self.disk(), frozen)
            self.assertEqual(self.request(self.event(save_nonce="click-2"), collision), collision)
            self.assertEqual(self.disk(), frozen)

    def test_callback_checkpoints_consumed_nonce_before_writer_and_blocks_reentrant_replay(self):
        event = self.event()
        before = copy.deepcopy((self.draft, event, self.metadata, self.state))
        session = {"state": copy.deepcopy(self.state)}
        order = []

        def checkpoint(consumed):
            order.append("checkpoint")
            self.assertFalse(self.output.exists())
            self.assertEqual(consumed["handled_nonces"], ["click-1"])
            self.assertIsNone(consumed["result"])
            session["state"] = consumed

        def writer(output, metadata, circles):
            order.append("writer")
            self.assertEqual(session["state"]["handled_nonces"], ["click-1"])
            replay = handle_save_request(self.draft, event, metadata, self.token,
                                         session["state"], output, before_save=checkpoint)
            self.assertEqual(replay, session["state"])
            self.assertEqual(order, ["checkpoint", "writer"],
                             "reentrant replay must not checkpoint or call the writer again")
            return save_player_answers(output, metadata, circles)

        with patch("src.player_ui.save_player_answers", side_effect=writer) as saver:
            saved = handle_save_request(self.draft, event, self.metadata, self.token,
                                        self.state, self.output, before_save=checkpoint)
            saver.assert_called_once()
        self.assertTrue(saved["result"]["ok"])
        self.assertEqual(order, ["checkpoint", "writer"])
        self.assertEqual((self.draft, event, self.metadata, self.state), before)
        self.assertIsNone(session["state"]["result"],
                          "completion result is returned separately from the pre-IO checkpoint")
        self.assertEqual(len(self.runs()), 1)

    def test_checkpoint_survives_interrupted_writer_and_rerun_cannot_repeat_same_click(self):
        event = self.event()
        session = {"state": copy.deepcopy(self.state)}

        def checkpoint(consumed):
            session["state"] = consumed

        with patch("src.player_ui.save_player_answers", side_effect=RuntimeError("interrupted after checkpoint")) as saver:
            with self.assertRaisesRegex(RuntimeError, "interrupted"):
                handle_save_request(self.draft, event, self.metadata, self.token,
                                    self.state, self.output, before_save=checkpoint)
            self.assertEqual(session["state"]["handled_nonces"], ["click-1"])
            self.assertIsNone(session["state"]["result"])
            replay = handle_save_request(self.draft, event, self.metadata, self.token,
                                         session["state"], self.output, before_save=checkpoint)
            self.assertEqual(replay, session["state"])
            saver.assert_called_once()
        self.assertFalse(self.output.exists())
        retried = handle_save_request(self.draft, self.event(save_nonce="click-2"),
                                      self.metadata, self.token, session["state"],
                                      self.output, before_save=checkpoint)
        self.assertTrue(retried["result"]["ok"])
        self.assertEqual(retried["handled_nonces"], ["click-1", "click-2"])
        self.assertEqual(self.state, {"handled_nonces": [], "result": None})

    def test_rejected_or_malformed_requests_never_call_checkpoint_or_writer(self):
        saved = self.request(self.event())
        frozen = self.disk()
        events = (None, self.event(session_token="old-session"),
                  self.event(image_id="moon_ap15_hia_c02"), self.event(revision=0),
                  self.event(save_nonce=""), self.event(),  # Already consumed.
                  self.event(save_nonce="new-click", circles=[]))
        with patch("src.player_ui.save_player_answers") as saver:
            # Use an independent spy rather than a production callback implementation.
            checkpoint = Mock()
            for event in events:
                with self.subTest(event=event):
                    ignored = handle_save_request(self.draft, event, self.metadata, self.token,
                                                  saved, self.output, before_save=checkpoint)
                    self.assertEqual(ignored, saved)
            with self.assertRaises(ContractError):
                handle_save_request(self.draft, self.event(save_nonce="new-click", circles=None),
                                    self.metadata, self.token, saved, self.output,
                                    before_save=checkpoint)
            checkpoint.assert_not_called()
            saver.assert_not_called()
        self.assertEqual(self.disk(), frozen)


if __name__ == "__main__":
    unittest.main()
