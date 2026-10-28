"""Provenance checks against real temporary Git working trees."""

import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.evaluate_hough import code_version


class CodeVersionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.repo = Path(self.directory.name)
        self.git("init", "-q")
        (self.repo / "tracked.txt").write_text("original", encoding="utf-8")
        (self.repo / ".gitignore").write_text("outputs/\n", encoding="utf-8")
        self.git("add", ".")
        self.git(
            "-c",
            "user.name=Test Reviewer",
            "-c",
            "user.email=test@example.com",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-qm",
            "fixture",
        )
        self.revision = self.git("rev-parse", "HEAD")

    def git(self, *args):
        return subprocess.run(
            ["git", *args],
            cwd=self.repo,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    def test_clean_tree_and_ignored_outputs_keep_plain_revision(self):
        self.assertEqual(code_version(self.repo), self.revision)
        (self.repo / "outputs").mkdir()
        (self.repo / "outputs/report.json").write_text("{}", encoding="utf-8")
        self.assertEqual(code_version(self.repo), self.revision)

    def test_tracked_change_marks_working_tree(self):
        (self.repo / "tracked.txt").write_text("changed", encoding="utf-8")
        self.assertEqual(code_version(self.repo), self.revision + "+working-tree")

    def test_untracked_change_marks_working_tree(self):
        (self.repo / "new.txt").write_text("new", encoding="utf-8")
        self.assertEqual(code_version(self.repo), self.revision + "+working-tree")
