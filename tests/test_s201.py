"""S2-01 regression: exact votes, radius logging and configurable CLI."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import numpy as np
from src.hough import _accumulate, resolve_hough_params
from src.pipeline import radius_range
from scripts.run_end_to_end import main


class TestAccumulationS201(unittest.TestCase):
    def test_bounded_bins_equal_scalar_votes_for_random_and_outside_centers(self):
        rng = np.random.default_rng(201)
        for shape in [(3, 7), (20, 19), (512, 512)]:
            ys = rng.integers(0, shape[0], size=60, dtype=np.int32)
            xs = rng.integers(0, shape[1], size=60, dtype=np.int32)
            offsets = rng.integers(-30, 31, size=(80, 2), dtype=np.int32)
            expected = np.zeros(shape, dtype=np.int32)
            for y, x in zip(ys, xs):
                for dx, dy in offsets:
                    a, b = int(x-dx), int(y-dy)
                    if 0 <= a < shape[1] and 0 <= b < shape[0]:
                        expected[b, a] += 1
            for batch in [1, 7, 256]:
                with self.subTest(shape=shape, batch=batch):
                    np.testing.assert_array_equal(_accumulate(ys, xs, shape, offsets, batch), expected)
        ys, xs = np.array([0], dtype=np.int32), np.array([0], dtype=np.int32)
        outside = np.array([[100, 100]], dtype=np.int32)
        self.assertFalse(_accumulate(ys, xs, (3, 7), outside, 1).any())
        self.assertFalse(_accumulate(ys[:0], xs[:0], (3, 7), outside, 1).any())

    def test_radius_intersection_and_sparse_grid(self):
        params = resolve_hough_params({'r_min_limit_px': 12, 'r_max_limit_px': 30, 'radius_step_px': 4})
        meta = {'radius': {'r_min_px': 10, 'r_max_px': 29}}
        lo, hi = radius_range(meta, params)
        self.assertEqual(list(range(lo, hi+1, params['radius_step_px'])), [12, 16, 20, 24, 28])
        with self.assertRaises(ValueError):
            radius_range({'radius': {'r_min_px': 31, 'r_max_px': 40}}, params)


class TestHoughConfigCli(unittest.TestCase):
    def capture_params(self, argv):
        with mock.patch('scripts.run_end_to_end.run_end_to_end', side_effect=RuntimeError('capture')) as run:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(argv), 1)
            return run.call_args.kwargs['hough_params']

    def test_defaults_config_and_explicit_overrides(self):
        params = self.capture_params(['image', '--no-player'])
        self.assertEqual(params, resolve_hough_params({}))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'hough.json'
            path.write_text(json.dumps({'hough': {'voting_method': 'gradient', 'radius_step_px': 2,
                                                  'max_circles': 17, 'r_max_limit_px': 40}}), encoding='utf-8')
            args = ['image', '--no-player', '--hough-config', str(path)]
            configured = self.capture_params(args)
            self.assertEqual(configured['voting_method'], 'gradient')
            self.assertEqual(configured['radius_step_px'], 2)
            self.assertEqual(configured['max_circles'], 17)
            overridden = self.capture_params(args+['--voting', 'full_circle', '--max-circles', '9'])
            self.assertEqual(overridden['voting_method'], 'full_circle')
            self.assertEqual(overridden['max_circles'], 9)
            self.assertEqual(overridden['r_max_limit_px'], 40)

    def test_bad_config_fails_before_running(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'hough.json'
            for text in ['{', '{"unknown": 3}', '[]']:
                path.write_text(text, encoding='utf-8')
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
                    main(['image', '--hough-config', str(path)])
                self.assertEqual(raised.exception.code, 2)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            main(['image', '--max-circles', '0'])
        self.assertEqual(raised.exception.code, 2)


class TestRadiusRun(unittest.TestCase):
    def test_saved_grid_reports_last_sample_instead_of_upper_bound(self):
        from src.pipeline import run_end_to_end
        root = Path(__file__).resolve().parents[1]
        metadata = json.loads((root/'data/examples/s105_synthetic_512.json').read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory() as tmp:
            processed = Path(tmp)/'processed'
            processed.mkdir()
            image_id = metadata['image_id']
            (processed/(image_id+'.json')).write_text(json.dumps(metadata), encoding='utf-8')
            np.save(processed/(image_id+'.npy'), np.zeros((512, 512), dtype=np.float32))
            directory, summary = run_end_to_end(
                image_id, processed_dir=processed, output_root=Path(tmp)/'outputs',
                code_version='test-s201', render=False,
                hough_params={'r_min_limit_px': 12, 'r_max_limit_px': 29, 'radius_step_px': 4})
            saved = json.loads((directory/'params.json').read_text(encoding='utf-8'))
            expected = {'metadata_px': [10, 125], 'bounds_px': [12, 29],
                        'step_px': 4, 'count': 5, 'last_radius_px': 28}
            self.assertEqual(saved['radius_search'], expected)
            self.assertEqual(summary['steps']['hough']['radius_search'], expected)


if __name__ == '__main__':
    unittest.main()
