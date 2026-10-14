"""S1-08: kiểm chứng phần tự viết theo S1-04 mục 9 và hợp đồng đầu ra.

OpenCV chỉ dùng ở đây làm đáp án đối chiếu. Cần numpy + opencv; nếu chưa cài
thì bỏ qua để checker S1-05 vẫn chạy được với Python chuẩn.
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch

try:
    import cv2
    import numpy as np
    from src import preprocessing as pp
    from scripts import run_preprocessing as cli
except ImportError:  # pragma: no cover
    cv2 = None

TOL = 1e-5


@unittest.skipIf(cv2 is None, "Chưa cài numpy/opencv-python-headless.")
class SelfWrittenVsOpenCV(unittest.TestCase):
    def setUp(self):
        self.rng = np.random.default_rng(0)
        self.img = self.rng.random((512, 512)).astype(np.float32)

    def test_b1_block_mean_matches_inter_area(self):
        for k in (2, 3, 4):
            src = self.rng.random((512 * k, 512 * k)).astype(np.float32)
            ours, _ = pp.block_mean(src, np.ones(src.shape, bool), k)
            ref = cv2.resize(src, (512, 512), interpolation=cv2.INTER_AREA)
            self.assertLess(np.abs(ours - ref).max(), TOL, f"k={k}")

    def test_b1_invalid_pixel_invalidates_block(self):
        src = np.ones((8, 8), np.float32)
        valid = np.ones((8, 8), bool)
        valid[5, 2] = False
        out, out_valid = pp.block_mean(src, valid, 2)
        self.assertFalse(out_valid[2, 1])
        self.assertEqual(out[2, 1], 0)
        self.assertEqual(int(out_valid.sum()), 15)

    def test_b2_gray_bt601(self):
        rgb = np.zeros((2, 2, 3), np.float32)
        rgb[0, 0] = (1, 0, 0)
        rgb[0, 1] = (0, 1, 0)
        rgb[1, 0] = (0, 0, 1)
        rgb[1, 1] = (1, 1, 1)
        np.testing.assert_allclose(pp.to_gray(rgb), [[0.299, 0.587], [0.114, 1.0]], atol=1e-6)

    def test_b3_percentile_by_hand(self):
        img = np.arange(1, 10, dtype=np.float32).reshape(3, 3)  # 1..9
        out, lo, hi = pp.normalize_percentile(img, np.ones((3, 3), bool), 0, 100)
        self.assertEqual((lo, hi), (1.0, 9.0))
        np.testing.assert_allclose(out, (img - 1) / 8, atol=1e-7)
        # 25 % – 75 % của 1..9 là 3 và 7 → 1, 2 bị kẹp về 0; 8, 9 kẹp về 1
        out, lo, hi = pp.normalize_percentile(img, np.ones((3, 3), bool), 25, 75)
        self.assertEqual((lo, hi), (3.0, 7.0))
        np.testing.assert_allclose(out.ravel(), [0, 0, 0, .25, .5, .75, 1, 1, 1], atol=1e-7)

    def test_b3_ignores_invalid_pixels(self):
        img = np.array([[0, 1], [2, 1000]], np.float32)
        valid = np.array([[True, True], [True, False]])
        out, lo, hi = pp.normalize_percentile(img, valid, 0, 100)
        self.assertEqual((lo, hi), (0.0, 2.0))
        self.assertEqual(out[1, 1], 0)

    def test_b4_clip_limit_has_effect_in_8bit_only(self):
        flat = np.clip(0.3 + self.rng.normal(0, 0.02, (512, 512)), 0, 1).astype(np.float32)
        valid = np.ones(flat.shape, bool)
        std8 = [pp.clahe(flat, valid, c, 8, bits=8).std() for c in (1, 2, 4)]
        std16 = [pp.clahe(flat, valid, c, 8, bits=16).std() for c in (1, 2, 4)]
        self.assertLess(std8[0], std8[1])
        self.assertLess(std8[1], std8[2])
        self.assertAlmostEqual(std16[0], std16[2], places=6)  # uint16: clip vô tác dụng

    def test_b5_gaussian_matches_opencv(self):
        for sigma in (1.0, 1.5, 2.5):
            size = 2 * int(np.ceil(3 * sigma)) + 1
            ours = pp.gaussian_blur(self.img, sigma)
            ref = cv2.GaussianBlur(self.img, (size, size), sigma, borderType=cv2.BORDER_REFLECT_101)
            self.assertLess(np.abs(ours - ref).max(), TOL, f"sigma={sigma}")

    def test_b5_default_kernel_size_is_11(self):
        self.assertEqual(len(pp.gaussian_kernel(1.5)), 11)
        self.assertAlmostEqual(pp.gaussian_kernel(1.5).sum(), 1.0)

    def test_b6_sobel_matches_opencv(self):
        gx, gy, mag, theta = pp.sobel(self.img)
        rx = cv2.Sobel(self.img, cv2.CV_32F, 1, 0, ksize=3, borderType=cv2.BORDER_REFLECT_101)
        ry = cv2.Sobel(self.img, cv2.CV_32F, 0, 1, ksize=3, borderType=cv2.BORDER_REFLECT_101)
        self.assertLess(np.abs(gx - rx).max(), TOL)
        self.assertLess(np.abs(gy - ry).max(), TOL)
        self.assertLess(np.abs(mag - np.hypot(rx, ry)).max(), TOL)

    def test_b6_gradient_sign_convention(self):
        ramp_x = np.tile(np.arange(16, dtype=np.float32), (16, 1))  # sáng dần sang phải
        gx, gy, _, theta = pp.sobel(ramp_x)
        self.assertGreater(gx[8, 8], 0)
        self.assertAlmostEqual(float(theta[8, 8]), 0.0, places=5)
        gx, gy, _, theta = pp.sobel(ramp_x.T)  # sáng dần xuống dưới
        self.assertGreater(gy[8, 8], 0)
        self.assertAlmostEqual(float(theta[8, 8]), np.pi / 2, places=5)

    def test_b8_erode_margin_from_border_and_nodata(self):
        valid = np.ones((40, 40), bool)
        valid[20, 20] = False
        keep = pp.erode(valid, 6)
        self.assertFalse(keep[:6].any() or keep[-6:].any() or keep[:, :6].any() or keep[:, -6:].any())
        self.assertTrue(keep[6, 6] and keep[33, 33])
        self.assertFalse(keep[14:27, 14:27].any())
        self.assertTrue(keep[13, 13] and keep[27, 27])


@unittest.skipIf(cv2 is None, "Chưa cài numpy/opencv-python-headless.")
class PipelineContract(unittest.TestCase):
    def setUp(self):
        # Đĩa sáng trên nền tối, có nhiễu, ô cắt 1024 để chạy cả B1 (k=2)
        yy, xx = np.mgrid[:1024, :1024]
        disc = ((xx - 500) ** 2 + (yy - 520) ** 2 < 200 ** 2).astype(np.float32)
        rng = np.random.default_rng(1)
        self.image = (disc * 3000 + 1000 + rng.normal(0, 50, disc.shape)).astype(np.float32)
        self.image[:100, 900:] = np.nan  # vùng nodata
        self.out = pp.preprocess(self.image, {"downsample_k": 2}, {"version": "test"})

    def test_output_contract(self):
        for key in ("gray", "enhanced", "smooth", "gx", "gy", "mag", "theta"):
            self.assertEqual(self.out[key].shape, (512, 512), key)
            self.assertEqual(self.out[key].dtype, np.float32, key)
            self.assertTrue(np.isfinite(self.out[key]).all(), key)
        for key in ("gray", "enhanced", "smooth"):
            self.assertGreaterEqual(self.out[key].min(), 0, key)
            self.assertLessEqual(self.out[key].max(), 1, key)
        for key in ("edges", "valid_mask"):
            self.assertEqual(self.out[key].dtype, bool, key)
            self.assertEqual(self.out[key].shape, (512, 512), key)

    def test_edges_respect_margin_and_nodata(self):
        edges, valid = self.out["edges"], self.out["valid_mask"]
        m = self.out["params"]["edge_margin_px"]
        self.assertFalse(edges[:m].any() or edges[-m:].any() or edges[:, :m].any() or edges[:, -m:].any())
        self.assertFalse(valid[:50, 450:].any())
        self.assertFalse((edges & ~pp.erode(valid, m)).any())

    def test_circle_rim_is_covered(self):
        # Tâm (500, 520) ở ô cắt 1024 → ảnh 512: (x − 0,5)/2; bán kính 200 → 100.
        # Chỉ đòi vành được bắt đủ: ảnh này 90 % phẳng nên ngưỡng P90 vẫn để lọt nhiễu.
        ang = np.linspace(0, 2 * np.pi, 360, endpoint=False)
        xs = np.round(249.75 + 100 * np.cos(ang)).astype(int)
        ys = np.round(259.75 + 100 * np.sin(ang)).astype(int)
        edges = self.out["edges"]
        hit = np.zeros(len(ang), bool)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                hit |= edges[ys + dy, xs + dx]
        self.assertGreater(hit.mean(), 0.95)

    def test_params_are_saved_and_json_serializable(self):
        params = self.out["params"]
        json.dumps(params, allow_nan=False)
        for key in ("p_lo", "p_hi", "clahe_clip", "clahe_grid", "gauss_sigma", "gauss_kernel_size",
                    "canny_high_pct", "canny_low_ratio", "canny_high", "canny_low", "edge_margin_px",
                    "p_lo_value", "p_hi_value", "version", "steps"):
            self.assertIn(key, params)
        self.assertTrue(params["b1_applied"])
        self.assertAlmostEqual(params["canny_low"], 0.4 * params["canny_high"])
        impl = {s["id"]: s["impl"] for s in params["steps"]}
        self.assertEqual([s["id"] for s in params["steps"]], [f"B{i}" for i in range(9)])
        self.assertTrue(all(impl[s].startswith("TỰ VIẾT") for s in ("B1", "B2", "B3", "B5", "B6", "B8")))
        self.assertTrue(all(impl[s].startswith("THƯ VIỆN") for s in ("B0", "B4", "B7")))

    def test_already_downsampled_input_skips_b1(self):
        out = pp.preprocess(self.out["gray"], {"downsample_k": 2})
        self.assertFalse(out["params"]["b1_applied"])

    def test_unknown_param_rejected(self):
        with self.assertRaises(ValueError):
            pp.preprocess(self.image, {"downsample_k": 2}, {"gauss_sigmaa": 2})


@unittest.skipIf(cv2 is None, "Chưa cài numpy/opencv-python-headless.")
class RegressionAndInputValidation(unittest.TestCase):
    def test_clean_discs_on_flat_background_keep_rims(self):
        yy, xx = np.mgrid[:512, :512]
        for radius in (5, 24, 32, 64, 100):
            with self.subTest(radius=radius):
                image = (((xx - 256) ** 2 + (yy - 256) ** 2) <= radius ** 2).astype(np.float32)
                out = pp.preprocess(image, {"downsample_k": 1})
                distance = np.hypot(xx - 256, yy - 256)
                self.assertGreater(int((out["edges"] & (abs(distance - radius) <= 2)).sum()), radius * 3)
                self.assertGreater(out["params"]["canny_high"], 0)
                self.assertEqual(out["params"]["canny_threshold_strategy"], "positive_gradient_percentile")
                if radius == 5:
                    self.assertEqual(out["params"]["normalization_strategy"], "valid_min_max_fallback")

    def test_flat_image_returns_empty_edges_with_explanation(self):
        out = pp.preprocess(np.ones((512, 512), np.float32), {"downsample_k": 1})
        self.assertFalse(out["edges"].any())
        self.assertEqual(out["params"]["normalization_strategy"], "constant_image")
        self.assertEqual(out["params"]["canny_threshold_strategy"], "no_gradient")
        self.assertEqual(out["params"]["canny_high"], 0)

    def test_all_invalid_and_too_small_support_rejected(self):
        image = np.ones((512, 512), np.float32)
        for mask in (np.zeros(image.shape, bool), np.pad(np.ones((3, 3), bool), ((254, 255), (254, 255)))):
            with self.subTest(valid_pixels=int(mask.sum())), self.assertRaisesRegex(ValueError, "hợp lệ"):
                pp.preprocess(image, {"downsample_k": 1}, valid_mask=mask)

    def test_larger_gaussian_increases_mask_margin(self):
        image = np.tile(np.linspace(0, 1, 512, dtype=np.float32), (512, 1))
        mask = np.ones(image.shape, bool)
        mask[180:205, 180:205] = False
        out = pp.preprocess(image, {"downsample_k": 1}, {"gauss_sigma": 2.5}, mask)
        self.assertEqual(out["params"]["gauss_kernel_size"], 17)
        self.assertEqual(out["params"]["edge_margin_requested_px"], 6)
        self.assertEqual(out["params"]["edge_margin_px"], 9)
        self.assertFalse((out["edges"] & ~pp.erode(mask, 9)).any())

    def test_invalid_parameters_fail_clearly(self):
        for key, values in {
            "p_lo": (-1, 100, True, float("nan")), "p_hi": (0, 101, "99"),
            "gauss_sigma": (0, -1, float("inf"), "1.5", True),
            "gauss_kernel_size": (2, 10, 511, 11.5, True),
            "clahe_clip": (0, float("nan"), True), "clahe_grid": (0, 513, 8.5, True),
            "clahe_bits": (7, 8.0, True), "canny_high_pct": (0, 101, False),
            "canny_low_ratio": (0, 1, float("inf")), "edge_margin_px": (-1, 256, 6.5, True),
        }.items():
            for value in values:
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    pp.resolve_params({key: value})

    def test_invalid_downsample_and_mask_are_rejected(self):
        image = np.ones((512, 512), np.float32)
        for k in (0, -1, 1.5, True, "2"):
            with self.subTest(k=k), self.assertRaises(ValueError):
                pp.preprocess(image, {"downsample_k": k})
        for mask in (np.ones((512, 1), bool), np.ones((512, 512), np.uint8), np.array(True)):
            with self.subTest(mask_shape=mask.shape), self.assertRaisesRegex(ValueError, "valid_mask"):
                pp.preprocess(image, {"downsample_k": 1}, valid_mask=mask)

    def test_unsupported_image_types_rejected(self):
        for image in (np.ones((512, 512), complex), np.ones((512, 512), object), np.ones((512, 512, 2)), np.ones(512)):
            with self.subTest(shape=image.shape, dtype=image.dtype), self.assertRaises(ValueError):
                pp.preprocess(image, {"downsample_k": 1})


@unittest.skipIf(cv2 is None, "Chưa cài numpy/opencv-python-headless.")
class PreprocessingFileAndCLI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.image = np.tile(np.linspace(0, 1, 512, dtype=np.float32), (512, 1))
        self.mask = np.ones((512, 512), bool)
        self.mask[180:205, 180:205] = False
        self.image[~self.mask] = 0
        self.path = self.folder / "masked.npy"
        np.save(self.path, self.image)
        self.metadata = json.loads((cli.ROOT / "data/examples/s105_synthetic_512.json").read_text())
        self.metadata.update(image_id="masked", valid_ratio=float(self.mask.mean()), downsample_k=1)
        self.metadata_path = self.folder / "masked.json"
        self.metadata_path.write_text(json.dumps(self.metadata))

    def test_npy_sidecar_mask_preserves_nodata_and_valid_zeros(self):
        np.save(self.folder / "masked_valid_mask.npy", self.mask)
        image, mask, metadata, _ = cli.file_input(self.path, self.metadata_path)
        out = pp.preprocess(image, metadata, valid_mask=mask)
        self.assertEqual(int((~out["valid_mask"]).sum()), 625)
        self.assertTrue(out["valid_mask"][100, 0])  # Có giá trị 0 nhưng vẫn hợp lệ.
        self.assertFalse((out["edges"] & ~pp.erode(self.mask, 6)).any())
        self.assertEqual(out["params"]["valid_ratio"], float(self.mask.mean()))
        self.assertIn("valid_mask", metadata["input_files"])

    def test_missing_mask_is_not_silently_ignored(self):
        with self.assertRaisesRegex(ValueError, "thiếu mặt nạ"):
            cli.file_input(self.path, self.metadata_path)

    def test_explicit_mask_and_invalid_mask_files(self):
        path = self.folder / "separate.npy"
        np.save(path, self.mask)
        _, mask, _, _ = cli.file_input(self.path, self.metadata_path, path)
        np.testing.assert_array_equal(mask, self.mask)
        for bad in (np.ones((512, 1), bool), np.ones((512, 512), np.uint8)):
            np.save(path, bad)
            with self.assertRaisesRegex(ValueError, "mảng bool"):
                cli.file_input(self.path, self.metadata_path, path)

    def test_mask_and_metadata_mismatch_is_rejected(self):
        np.save(self.folder / "masked_valid_mask.npy", np.ones((512, 512), bool))
        with self.assertRaisesRegex(ValueError, "không khớp"):
            cli.file_input(self.path, self.metadata_path)

    def test_png_alpha_is_kept_as_mask_and_channels_stay_rgb(self):
        rgba = np.zeros((512, 512, 4), np.uint8)
        rgba[..., :3] = (30, 80, 200)  # BGR trên đĩa
        rgba[..., 3] = self.mask.astype(np.uint8) * 255
        png = self.folder / "masked.png"
        self.assertTrue(cv2.imwrite(str(png), rgba))
        image, mask, _, _ = cli.file_input(png, self.metadata_path)
        np.testing.assert_array_equal(image[0, 0], [200, 80, 30, 255])
        np.testing.assert_array_equal(mask, self.mask)

    def test_cli_saves_mask_threshold_strategy_and_input_hashes(self):
        yy, xx = np.mgrid[:512, :512]
        image = (((xx - 256) ** 2 + (yy - 256) ** 2) <= 32 ** 2).astype(np.float32)
        image[~self.mask] = 0
        np.save(self.path, image)
        np.save(self.folder / "masked_valid_mask.npy", self.mask)
        run_id = f"test_s108_{uuid4().hex}"
        directory = cli.ROOT / "outputs" / run_id
        self.addCleanup(lambda: shutil.rmtree(directory, ignore_errors=True))
        cmd = [sys.executable, str(cli.ROOT / "scripts/run_preprocessing.py"), "--input", str(self.path),
               "--metadata", str(self.metadata_path), "--run-id", run_id]
        result = subprocess.run(cmd, cwd=cli.ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        params = json.loads((directory / "params.json").read_text())
        metadata = json.loads((directory / "metadata.json").read_text())
        run = json.loads((directory / "run.json").read_text())
        with np.load(directory / "result.npz", allow_pickle=False) as arrays:
            np.testing.assert_array_equal(arrays["valid_mask"], self.mask)
            self.assertGreater(int(arrays["edges"].sum()), 0)
        self.assertEqual(params["valid_ratio"], float(self.mask.mean()))
        self.assertEqual(metadata["valid_ratio"], float(self.mask.mean()))
        self.assertEqual(params["canny_threshold_strategy"], "positive_gradient_percentile")
        self.assertEqual(run["input_files"]["valid_mask"]["sha256"], cli.fingerprint(self.folder / "masked_valid_mask.npy")["sha256"])
        rerun = subprocess.run(cmd, cwd=cli.ROOT, capture_output=True, text=True)
        self.assertNotEqual(rerun.returncode, 0)
        self.assertEqual(json.loads((directory / "params.json").read_text()), params)

    def test_cli_rejects_path_traversal_before_writing(self):
        run = subprocess.run([sys.executable, str(cli.ROOT / "scripts/run_preprocessing.py"),
                              "--synthetic", "oblique", "--run-id", "../../outside"],
                             capture_output=True, text=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("run_id", run.stderr)

    def test_synthetic_truth_matches_search_radius_and_reports_exclusions(self):
        craters = [(500, 520, 200), (-5, 10, 24), (200, 200, 14),
                   (200, 200, 20), (200, 200, 250), (200, 200, 252), (1024, 100, 80)]
        with patch("scripts.synthetic_scene.make_scene", return_value=(np.ones((1024, 1024), np.float32), craters)):
            _, _, metadata, truth = cli.synthetic_input("oblique")
        self.assertEqual([circle["r"] for circle in truth["circles"]], [100, 10, 125])
        counts = metadata["synthetic_truth_scope"]
        self.assertEqual(counts["generated_craters"], 7)
        self.assertEqual(counts["centres_outside_image"], 2)
        self.assertEqual(counts["radius_outside_search_range_with_center_in_image"], 2)
        self.assertEqual(counts["reference_craters"], 3)
        self.assertEqual(metadata["radius"]["r_min_px"], counts["r_min_px"])
        self.assertEqual(metadata["radius"]["r_max_px"], counts["r_max_px"])

    def test_failed_render_does_not_leave_partial_output(self):
        np.save(self.folder / "masked_valid_mask.npy", self.mask)
        run_id = f"test_failed_render_{uuid4().hex}"
        directory = cli.ROOT / "outputs" / run_id
        argv = ["run_preprocessing.py", "--input", str(self.path), "--metadata", str(self.metadata_path), "--run-id", run_id]
        with patch.object(sys, "argv", argv), patch.object(cli, "save_images", side_effect=OSError("disk failure")):
            with self.assertRaisesRegex(OSError, "disk failure"):
                cli.main()
        self.assertFalse(directory.exists())


if __name__ == "__main__":
    unittest.main()
