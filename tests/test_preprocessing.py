"""S1-08: kiểm chứng phần tự viết theo S1-04 mục 9 và hợp đồng đầu ra.

OpenCV chỉ dùng ở đây làm đáp án đối chiếu. Cần numpy + opencv; nếu chưa cài
thì bỏ qua để checker S1-05 vẫn chạy được với Python chuẩn.
"""

import json
import unittest

try:
    import cv2
    import numpy as np
    from src import preprocessing as pp
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


if __name__ == "__main__":
    unittest.main()
