import tempfile
import unittest
from pathlib import Path

from scripts.build_report import combined_markdown, public_links

BLOB = "https://github.com/Duckcy-Bui/nasa24-crater-stem/blob/main/"


class PublicLinkTests(unittest.TestCase):
    def test_relative_evidence_link_becomes_public_url(self):
        text = "Xem [E1](../evidence/s3-05/E1.csv) và [S3-10](../S3-10_TAI_TAO_KET_QUA.md)."
        self.assertEqual(
            public_links(text),
            f"Xem [E1]({BLOB}docs/evidence/s3-05/E1.csv) và "
            f"[S3-10]({BLOB}docs/S3-10_TAI_TAO_KET_QUA.md).",
        )

    def test_images_and_absolute_links_unchanged(self):
        text = "![Hình 4.1. A](../images/report/a.png){width=85%} [x](https://example.org/a)"
        self.assertEqual(public_links(text), text)

    def test_repo_root_link(self):
        self.assertEqual(public_links("[mã](../../scripts/build_report.py)"),
                         f"[mã]({BLOB}scripts/build_report.py)")

    def test_title_and_reference_links(self):
        self.assertEqual(public_links('[E1](../evidence/a.csv "bảng")'),
                         f'[E1]({BLOB}docs/evidence/a.csv "bảng")')
        self.assertEqual(public_links("[e1]: ../evidence/a.csv"),
                         f"[e1]: {BLOB}docs/evidence/a.csv")

    def test_code_is_not_rewritten(self):
        text = "`[E1](../evidence/a.csv)`\n\n```\n[E1](../evidence/a.csv)\n```\n"
        self.assertEqual(public_links(text), text)

    def test_link_outside_repo_rejected(self):
        with self.assertRaises(ValueError):
            public_links("[x](../../../outside.md)")

    def test_combined_markdown_applies_rewrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            chapter = Path(tmp) / "04.md"
            chapter.write_text("Xem [E1](../evidence/s3-05/E1.csv).", encoding="utf-8")
            merged = combined_markdown([chapter])
        self.assertIn(f"({BLOB}docs/evidence/s3-05/E1.csv)", merged)
        self.assertNotIn("](../evidence/", merged)


if __name__ == "__main__":
    unittest.main()
