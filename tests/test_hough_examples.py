"""Lock the S1-12 hand-worked 5×5 example to src/hough.py.

docs/S1-12_VI_DU_VA_DOI_CHIEU_HOUGH.md quotes these numbers. If hough.py changes
how it votes, this test fails so the document is updated together with the code.
No OpenCV needed.
"""
import unittest

from scripts.verify_hough_examples import tiny_example


class TestHoughTinyExample(unittest.TestCase):
    def setUp(self):
        self.example = tiny_example()

    def test_full_circle_accumulator_matches_document(self):
        self.assertEqual(self.example["offsets"], [[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1]])
        self.assertEqual(len(self.example["trace"]), 4)
        self.assertEqual(sum(len(point["votes"]) for point in self.example["trace"]), 32)
        self.assertEqual(self.example["accumulator"], [
            [0, 1, 1, 1, 0],
            [1, 2, 2, 2, 1],
            [1, 2, 4, 2, 1],
            [1, 2, 2, 2, 1],
            [0, 1, 1, 1, 0],
        ])
        self.assertEqual(self.example["threshold"], 3)
        self.assertEqual(self.example["peaks_yx"], [[2, 2]])
        self.assertEqual(self.example["score"], 0.5)

    def test_gradient_accumulator_matches_document(self):
        self.assertEqual(self.example["gradient_accumulator"], [
            [0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0],
            [1, 0, 4, 0, 1],
            [0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0],
        ])
        self.assertEqual(self.example["gradient_support_size"], 7)
        self.assertAlmostEqual(self.example["gradient_score"], 4 / 7)


if __name__ == "__main__":
    unittest.main()
