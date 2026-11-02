import unittest

from scripts.build_report import REPO_BLOB, public_links


class PublicLinkTests(unittest.TestCase):
    def test_relative_evidence_link_becomes_public_url(self):
        text = "Xem [E1](../evidence/s3-05/E1.csv) và [S3-10](../S3-10_TAI_TAO_KET_QUA.md)."
        self.assertEqual(
            public_links(text),
            f"Xem [E1]({REPO_BLOB}docs/evidence/s3-05/E1.csv) và "
            f"[S3-10]({REPO_BLOB}docs/S3-10_TAI_TAO_KET_QUA.md).",
        )

    def test_images_and_absolute_links_unchanged(self):
        text = "![Hình 4.1. A](../images/report/a.png){width=85%} [x](https://example.org/a)"
        self.assertEqual(public_links(text), text)

    def test_repo_root_link(self):
        self.assertEqual(public_links("[mã](../../scripts/build_report.py)"),
                         f"[mã]({REPO_BLOB}scripts/build_report.py)")


if __name__ == "__main__":
    unittest.main()
