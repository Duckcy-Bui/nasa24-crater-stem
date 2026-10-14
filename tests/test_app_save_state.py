"""AppTest save-command reruns with bundle PNG/metadata and isolated outputs.

Custom widget values are injected; this is not real-browser save/ACK proof.
"""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
IMAGE_A = "moon_ap15_hia_c01"
IMAGE_B = "moon_ap15_hia_c02"


class CanvasSaveAppStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = tempfile.TemporaryDirectory()
        cls.addClassCleanup(fixture.cleanup)
        cls.images = Path(fixture.name) / "images"
        cls.images.mkdir()
        manifest = json.loads((ROOT / "data/s106_bundle/manifest.json").read_text())
        with zipfile.ZipFile(ROOT / "data/s106_bundle/s106_lroc_browse_v2.zip") as bundle:
            for ident in manifest["image_ids"]:
                for suffix in (".png", ".json"):
                    name = ident + suffix
                    (cls.images / name).write_bytes(bundle.read(name))

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name) / "player_answers"
        code = (
            "from pathlib import Path\n"
            "import app\n"
            f"app.DATA_DIR = Path({str(self.images)!r})\n"
            f"app.PLAYER_OUTPUT_DIR = Path({str(self.output)!r})\n"
            "app.main()\n"
        )
        self.ui = AppTest.from_string(code, default_timeout=15).run()
        self.assert_clean()
        self.assertEqual(self.ui.selectbox[0].value, IMAGE_A)

    def assert_clean(self):
        self.assertEqual(len(self.ui.exception), 0)
        self.assertEqual(len(self.ui.error), 0)

    def runs(self):
        return sorted(self.output.iterdir()) if self.output.is_dir() else []

    def disk(self):
        return {str(p.relative_to(self.output)): p.read_bytes()
                for p in self.output.rglob("*") if p.is_file()} if self.output.is_dir() else {}

    def inject(self, revision=7, *, nonce=None, x=300.5, circles=None, **changes):
        ident = self.ui.selectbox[0].value
        event = {"image_id": ident, "session_token": self.ui.session_state["player_session_token"],
                 "revision": revision,
                 "circles": [{"crater_id": "U9", "x": x, "y": 99.25, "r": 30.75}]
                            if circles is None else circles,
                 **changes}
        if nonce is not None:
            event["save_nonce"] = nonce
        self.ui.session_state[f"player_canvas_{ident}"] = event

    def rerun(self):
        self.ui.run()
        self.assert_clean()

    def switch(self, ident):
        self.ui.selectbox[0].set_value(ident).run()
        self.assert_clean()

    def state(self, ident=IMAGE_A):
        return self.ui.session_state["player_save_states"][ident]

    def test_save_applies_latest_event_before_writing_and_acknowledges_same_revision_once(self):
        self.inject(nonce="a-save-1")
        self.rerun()
        self.assertEqual(len(self.runs()), 1)
        state = self.state()
        self.assertEqual(state["handled_nonces"], ["a-save-1"])
        result = state["result"]
        self.assertTrue(result["ok"])
        self.assertEqual((result["nonce"], result["revision"], result["image_id"], result["count"]),
                         ("a-save-1", 7, IMAGE_A, 1))
        self.assertFalse(Path(result["path"]).is_absolute())
        answer = json.loads((self.runs()[0] / "craters.json").read_text())
        self.assertEqual((answer["source"], answer["image_id"], answer["data_kind"]),
                         ("player", IMAGE_A, "real"))
        self.assertEqual(answer["circles"][0]["x"], 300.5)
        self.assertIsNone(answer["circles"][0]["confidence"])
        self.assertIsNone(answer["circles"][0]["votes"])
        frozen = self.disk()
        for _ in range(2):
            self.rerun()
            self.assertEqual(self.state(), state)
            self.assertEqual(self.disk(), frozen)

    def test_edit_keeps_old_ack_for_dirty_comparison_then_new_click_saves_new_run(self):
        self.inject(nonce="a-save-1")
        self.rerun()
        first_ack = copy.deepcopy(self.state()["result"])
        frozen = self.disk()
        self.inject(revision=8, x=255.5)
        self.rerun()
        self.assertEqual(self.state()["result"], first_ack)
        self.assertEqual(self.ui.session_state["player_drafts"][IMAGE_A]["revision"], 8)
        self.assertEqual(self.state()["result"]["revision"], 7)
        self.assertEqual(self.disk(), frozen)
        self.inject(revision=8, x=255.5, nonce="a-save-2")
        self.rerun()
        self.assertTrue(self.state()["result"]["ok"])
        self.assertEqual(self.state()["result"]["revision"], 8)
        self.assertEqual(len(self.runs()), 2)
        self.assertTrue(all(self.disk()[name] == data for name, data in frozen.items()))
        answer = json.loads(next(p for p in self.runs()
                                 if p.name == Path(self.state()["result"]["path"]).name)
                            .joinpath("craters.json").read_text())
        self.assertEqual(answer["circles"][0]["x"], 255.5)
        second_state = copy.deepcopy(self.state())
        second_disk = self.disk()
        # Replay the older click against the current snapshot, not just old geometry.
        self.inject(revision=8, x=255.5, nonce="a-save-1")
        self.rerun()
        self.assertEqual(self.state(), second_state)
        self.assertEqual(self.disk(), second_disk)

    def test_per_image_ack_and_empty_save_remain_isolated_after_switch_and_return(self):
        self.inject(nonce="a-save-1")
        self.rerun()
        saved_a = copy.deepcopy(self.state())
        self.switch(IMAGE_B)
        self.assertEqual(self.state(IMAGE_B), {"handled_nonces": [], "result": None})
        self.inject(revision=0, circles=[], nonce="b-empty")
        self.rerun()
        saved_b = copy.deepcopy(self.state(IMAGE_B))
        self.assertTrue(saved_b["result"]["ok"])
        self.assertEqual((saved_b["result"]["image_id"], saved_b["result"]["count"]), (IMAGE_B, 0))
        self.assertEqual(len(self.runs()), 2)
        self.switch(IMAGE_A)
        self.assertEqual(self.state(), saved_a)
        self.assertEqual(self.state(IMAGE_B), saved_b)
        self.assertEqual(self.ui.session_state["player_drafts"][IMAGE_A]["revision"], 7)
        self.assertEqual(len(self.runs()), 2)

    def test_previous_image_drain_updates_draft_but_never_executes_its_save_command(self):
        from src.player_ui import handle_save_request

        self.inject(revision=9, nonce="a-pending-before-switch")
        with patch("app.handle_save_request", wraps=handle_save_request) as handler:
            self.switch(IMAGE_B)
        self.assertGreaterEqual(handler.call_count, 1)
        for call in handler.call_args_list:
            self.assertEqual(call.args[2]["image_id"], IMAGE_B,
                             "previous-image drain must never invoke a save handler for A")
            self.assertIsNone(call.args[1], "the pending A command must not be passed as B's event")
            self.assertTrue(callable(call.kwargs["before_save"]))
        self.assertEqual(self.ui.session_state["player_drafts"][IMAGE_A]["revision"], 9)
        self.assertEqual(self.state(), {"handled_nonces": [], "result": None})
        self.assertEqual(self.state(IMAGE_B), {"handled_nonces": [], "result": None})
        self.assertFalse(self.output.exists())

    def test_stale_origin_revision_and_mismatched_equal_revision_do_not_change_saved_state(self):
        self.inject(nonce="a-save-1")
        self.rerun()
        saved = copy.deepcopy(self.state())
        draft = copy.deepcopy(self.ui.session_state["player_drafts"][IMAGE_A])
        frozen = self.disk()
        cases = ({"revision": 6}, {"revision": 100, "session_token": "obsolete-session"},
                 {"revision": 100, "image_id": IMAGE_B},
                 {"revision": 7, "x": 400.5})
        for changes in cases:
            with self.subTest(changes=changes):
                self.inject(nonce="unhandled-but-invalid", **changes)
                self.rerun()
                self.assertEqual(self.state(), saved)
                self.assertEqual(self.ui.session_state["player_drafts"][IMAGE_A], draft)
                self.assertEqual(self.disk(), frozen)

    def test_malformed_equal_revision_save_is_reported_without_consuming_or_writing(self):
        self.inject(nonce="a-save-1")
        self.rerun()
        saved = copy.deepcopy(self.state())
        frozen = self.disk()
        self.inject(revision=7, nonce="bad-click", circles=[{"crater_id": "U9", "x": 100, "y": 100, "r": 0}])
        self.ui.run()
        self.assertEqual(len(self.ui.exception), 0)
        self.assertEqual(len(self.ui.error), 1)
        self.assertEqual(self.state(), saved)
        self.assertEqual(self.disk(), frozen)

    def test_io_failure_is_acknowledged_once_and_new_click_can_retry(self):
        self.output.write_text("simulate a non-directory output target")
        self.inject(nonce="io-failure")
        self.rerun()
        failed = copy.deepcopy(self.state())
        self.assertFalse(failed["result"]["ok"])
        self.assertTrue(failed["result"]["error"])
        self.assertEqual(failed["handled_nonces"], ["io-failure"])
        self.output.unlink()
        self.rerun()
        self.assertEqual(self.state(), failed)
        self.assertFalse(self.output.exists())
        self.inject(nonce="retry-after-recovery")
        self.rerun()
        self.assertTrue(self.state()["result"]["ok"])
        self.assertEqual(self.state()["handled_nonces"], ["io-failure", "retry-after-recovery"])
        self.assertEqual(len(self.runs()), 1)

    def test_app_session_records_current_image_nonce_before_real_writer_runs(self):
        import streamlit as st
        from src.player_annotations import save_player_answers

        self.inject(nonce="checkpoint-before-io")
        observations = []

        def writer(output, metadata, circles):
            active = st.session_state["player_active_metadata"]["image_id"]
            consumed = copy.deepcopy(st.session_state["player_save_states"][active])
            self.assertEqual(active, IMAGE_A)
            self.assertEqual(metadata["image_id"], active)
            self.assertEqual(Path(output), self.output)
            self.assertEqual(consumed["handled_nonces"], ["checkpoint-before-io"])
            self.assertIsNone(consumed["result"])
            self.assertEqual(st.session_state["player_drafts"][active]["revision"], 7)
            self.assertFalse(self.output.exists())
            observations.append(consumed)
            return save_player_answers(output, metadata, circles)

        with patch("src.player_ui.save_player_answers", side_effect=writer) as saver:
            self.rerun()
            self.rerun()  # Neither acknowledgement rerun nor explicit rerun writes again.
            saver.assert_called_once()
        self.assertEqual(len(observations), 1)
        self.assertTrue(self.state()["result"]["ok"])
        self.assertEqual(self.state()["handled_nonces"], ["checkpoint-before-io"])
        self.assertEqual(len(self.runs()), 1)


if __name__ == "__main__":
    unittest.main()
