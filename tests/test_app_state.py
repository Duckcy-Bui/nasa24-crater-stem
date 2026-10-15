"""Independent rerun regressions; custom-canvas browser checks remain separate."""

from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

from scripts.install_s106_dataset import install_dataset


class PlayerRerunStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.images = Path(cls.temporary.name) / "images"
        install_dataset(cls.images)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def open_app(self):
        code = (
            "from pathlib import Path\n"
            "import app\n"
            f"app.DATA_DIR = Path({str(self.images)!r})\n"
            "app.main()\n"
        )
        application = AppTest.from_string(code, default_timeout=15).run()
        self.assertEqual(len(application.exception), 0)
        self.assertEqual(len(application.error), 0)
        return application

    def pending_event(self, app, **changes):
        return {
            "image_id": "moon_ap15_hia_c01",
            "session_token": app.session_state["player_session_token"],
            "revision": 7,
            "circles": [{"crater_id": "U9", "x": 300.5, "y": 99.25, "r": 30.75}],
            **changes,
        }

    def test_image_switch_drains_pending_previous_image_event_before_widget_cleanup(self):
        app = self.open_app()
        original = "moon_ap15_hia_c01"
        next_image = "moon_ap15_hia_c02"
        self.assertEqual(app.selectbox[0].value, original)
        event = self.pending_event(app)
        # Model a component change delivered in the same rerun as changing image.
        app.session_state[f"player_canvas_{original}"] = event
        app.selectbox[0].set_value(next_image).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.error), 0)
        self.assertEqual(app.session_state["player_active_metadata"]["image_id"], next_image)
        drafts = app.session_state["player_drafts"]
        self.assertEqual(drafts[original]["revision"], 7)
        self.assertEqual(drafts[original]["circles"][0], {**event["circles"][0], "confidence": None, "votes": None})
        self.assertEqual(drafts[next_image], {"revision": 0, "circles": []})
        app.selectbox[0].set_value(original).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.session_state["player_drafts"][original]["circles"][0]["x"], 300.5)

    def test_previous_widget_from_an_old_session_cannot_contaminate_saved_draft(self):
        app = self.open_app()
        original = "moon_ap15_hia_c01"
        before = copy.deepcopy(app.session_state["player_drafts"][original])
        app.session_state[f"player_canvas_{original}"] = self.pending_event(app, session_token="obsolete-session")
        app.selectbox[0].set_value("moon_ap15_hia_c02").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.error), 0)
        self.assertEqual(app.session_state["player_drafts"][original], before)

    def test_invalid_previous_event_is_reported_without_losing_draft_or_blocking_next_image(self):
        app = self.open_app()
        original = "moon_ap15_hia_c01"
        before = copy.deepcopy(app.session_state["player_drafts"][original])
        event = self.pending_event(app)
        event["circles"][0]["r"] = 0
        app.session_state[f"player_canvas_{original}"] = event
        app.selectbox[0].set_value("moon_ap15_hia_c02").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.error), 1)
        self.assertEqual(app.session_state["player_drafts"][original], before)
        self.assertEqual(app.session_state["player_active_metadata"]["image_id"], "moon_ap15_hia_c02")


if __name__ == "__main__":
    unittest.main()
