"""Offline handoff tests and regressions for S1-06 raster validity/provenance."""
from __future__ import annotations

import io
import json
import math
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.transform import Affine, from_origin

from scripts.generate_s106_crops import (BUNDLE_DIR, CROPS_CONFIG, make_crop,
                                         normalize_p05_p995, read_crop, sha256_file, sun_metadata)
from scripts.install_s106_dataset import install_dataset, verified_bundle
from scripts.scan_windows import scan_windows

ROOT = Path(__file__).resolve().parents[1]
MOON_CRS = CRS.from_dict(proj="eqc", lat_ts=0, lat_0=0, lon_0=0, R=1737400, units="m")


class RasterValidityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.directory = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write_tiff(self, array, *, nodata=None, affine=None, crs=MOON_CRS):
        path = self.directory / "fixture.tif"
        with rasterio.open(path, "w", driver="GTiff", height=array.shape[0], width=array.shape[1],
                           count=1, dtype=array.dtype, nodata=nodata, crs=crs,
                           transform=affine or from_origin(0, 20000, 20, 20)) as dst:
            dst.write(array, 1)
        return path

    def test_positive_nodata_is_excluded_and_valid_zero_is_kept(self):
        arr = np.arange(512 * 512, dtype=np.uint32).reshape(512, 512) % 1000
        arr = arr.astype(np.uint16)
        arr[20:45, 20:45] = 65535
        path = self.write_tiff(arr, nodata=65535)
        raw, mask, _ = read_crop(path, 0, 0)
        self.assertEqual(np.count_nonzero(~mask), 625)
        self.assertTrue(mask[0, 0], "A legitimate dark pixel is not nodata")
        normalized = normalize_p05_p995(raw, mask)
        self.assertEqual(normalized.dtype, np.float32)
        self.assertTrue(np.isfinite(normalized).all())
        self.assertTrue(np.all(normalized[~mask] == 0))
        valid = raw[mask].astype(np.float64)
        lo, hi = np.percentile(valid, (0.5, 99.5))
        np.testing.assert_array_equal(normalized[mask], np.clip((valid - lo) / (hi - lo), 0, 1).astype(np.float32))

    def test_window_scan_uses_mask_and_keeps_zero_intensity(self):
        arr = np.zeros((512, 512), dtype=np.uint16)
        arr[0:25, 0:25] = 65535
        path = self.write_tiff(arr, nodata=65535)
        records = list(scan_windows(path, min_valid=0.99))
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["valid_ratio"], 1 - 625 / (512 * 512))
        self.assertEqual(records[0]["nonzero_brightness_ratio"], 0)
        self.assertEqual(list(scan_windows(path, min_valid=1)), [])

    def test_explicit_raster_mask_and_nonfinite_pixels_are_combined(self):
        arr = np.linspace(0, 1, 512 * 512, dtype=np.float32).reshape(512, 512)
        arr[0, 0] = np.nan
        arr[0, 1] = np.inf
        path = self.write_tiff(arr)
        with rasterio.open(path, "r+") as dst:
            mask = np.full((512, 512), 255, dtype=np.uint8)
            mask[0, 2] = 0
            dst.write_mask(mask)
        _, mask, _ = read_crop(path, 0, 0)
        self.assertEqual(np.count_nonzero(~mask), 3)

    def test_zero_percentile_participates_when_valid(self):
        arr = np.array([[0, 0, 1], [2, 3, 4]], dtype=np.float32)
        actual = normalize_p05_p995(arr)
        lo, hi = np.percentile(arr.astype(float), (0.5, 99.5))
        np.testing.assert_array_equal(actual, np.clip((arr - lo) / (hi - lo), 0, 1).astype(np.float32))

    def test_no_valid_pixels_fails_and_constant_valid_image_is_finite(self):
        with self.assertRaisesRegex(ValueError, "không có pixel"):
            normalize_p05_p995(np.zeros((2, 2)), np.zeros((2, 2), dtype=bool))
        np.testing.assert_array_equal(normalize_p05_p995(np.zeros((2, 2))), np.zeros((2, 2), dtype=np.float32))

    def test_sparse_feature_survives_collapsed_percentiles(self):
        arr = np.zeros((512, 512), dtype=np.float32)
        arr[250:260, 250:260] = 2
        normalized = normalize_p05_p995(arr)
        self.assertEqual(np.count_nonzero(normalized), 100)
        self.assertEqual(float(normalized.max()), 1.0)

    def test_mask_shape_and_dtype_are_checked(self):
        for mask in (np.ones((2, 2), dtype=np.uint8), np.ones((1, 2), dtype=bool)):
            with self.assertRaises(ValueError):
                normalize_p05_p995(np.ones((2, 2)), mask)

    def test_windows_out_of_bounds_are_rejected(self):
        path = self.write_tiff(np.ones((512, 512), dtype=np.uint8))
        for x, y, size in ((1, 0, 512), (0, 1, 512), (-1, 0, 512), (0, 0, 256), (True, 0, 512)):
            with self.subTest(x=x, y=y, size=size), self.assertRaises(ValueError):
                read_crop(path, x, y, size)

    def test_rotated_anisotropic_and_earth_crs_are_rejected(self):
        for affine, crs in ((Affine(20, 1, 0, 0, -20, 20000), MOON_CRS),
                            (from_origin(0, 20000, 20, 10), MOON_CRS),
                            (from_origin(0, 20000, 20, 20), CRS.from_epsg(32648))):
            with self.subTest(affine=affine, crs=crs):
                path = self.write_tiff(np.ones((512, 512), dtype=np.uint8), affine=affine, crs=crs)
                with self.assertRaises(ValueError):
                    read_crop(path, 0, 0)

    def test_crop_centre_uses_corner_affine_without_half_pixel_shift(self):
        path = self.write_tiff(np.ones((512, 512), dtype=np.uint8))
        _, _, geo = read_crop(path, 0, 0)
        self.assertAlmostEqual(geo["center_lon"], math.degrees(5120 / 1737400))
        self.assertAlmostEqual(geo["center_lat"], math.degrees((20000 - 5120) / 1737400))

    def test_metadata_mask_matches_raster_and_no_catalogue_is_invented(self):
        arr = np.full((512, 512), 100, dtype=np.uint16)
        arr[0:25, 0:25] = 65535
        path = self.write_tiff(arr, nodata=65535)
        cfg = {**CROPS_CONFIG[0], "image_id": "fixture_crop", "x0": 0, "y0": 0}
        output = self.directory / "processed"
        make_crop(path, cfg, {"filename": path.name, "sha256": sha256_file(path)}, output)
        metadata = json.loads((output / "fixture_crop.json").read_text())
        mask = np.load(output / "fixture_crop_valid_mask.npy", allow_pickle=False)
        self.assertEqual(metadata["valid_ratio"], 1 - 625 / (512 * 512))
        self.assertEqual(metadata["valid_ratio"], float(mask.mean()))
        self.assertEqual(metadata["reference_status"], "unavailable")
        self.assertEqual(list(output.glob("*_craters_catalogue.json")), [])

    def test_legacy_catalogue_is_rejected_before_writing_new_outputs(self):
        path = self.write_tiff(np.ones((512, 512), dtype=np.uint8))
        cfg = {**CROPS_CONFIG[0], "image_id": "fixture_crop", "x0": 0, "y0": 0}
        output = self.directory / "processed"
        output.mkdir()
        (output / "fixture_crop_craters_catalogue.json").write_text('{}')
        with self.assertRaisesRegex(ValueError, "catalogue cũ"):
            make_crop(path, cfg, {}, output)
        self.assertEqual(len(list(output.iterdir())), 1)

    def test_sun_metadata_preserves_coarse_known_sides_and_uncertainty(self):
        west = sun_metadata(next(c for c in CROPS_CONFIG if c["stt"] == 9))
        east_candidate = sun_metadata(next(c for c in CROPS_CONFIG if c["stt"] == 11))
        mosaic = sun_metadata(CROPS_CONFIG[0])
        self.assertEqual((west["quality"], west["azimuth_deg"]), ("side_only", 270.0))
        self.assertEqual((east_candidate["quality"], east_candidate["azimuth_deg"]), ("none", None))
        self.assertEqual(east_candidate["side_candidate"], "east")
        self.assertIsNone(mosaic["incidence_deg"])
        self.assertEqual(mosaic["incidence_range_deg"], [28, 53])


class OfflineDatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest, cls.payloads = verified_bundle()

    def test_fresh_checkout_contains_all_26_real_crops(self):
        self.assertEqual(self.manifest["total_images"], 26)
        self.assertEqual(len(self.payloads), 104)
        self.assertEqual(self.manifest["generator_sha256"], sha256_file(ROOT / "scripts" / "generate_s106_crops.py"))
        self.assertTrue(all(not name.endswith("_craters_catalogue.json") for name in self.payloads))
        for image_id in self.manifest["image_ids"]:
            metadata = json.loads(self.payloads[f"{image_id}.json"])
            self.assertEqual(metadata["reference_status"], "unavailable")
            self.assertEqual(metadata["source"]["source_product_level"], "browse")
            self.assertFalse(metadata["source"]["radiometrically_calibrated"])
            self.assertTrue(metadata["source"]["url"].startswith('https://pds.lroc.im-ldi.com/'))

    def test_matched_apollo16_pair_has_same_ground_window(self):
        pair = [json.loads(self.payloads[f"{c['image_id']}.json"]) for c in CROPS_CONFIG if c.get("comparison_pair")]
        self.assertEqual(len(pair), 2)
        self.assertEqual(sorted(m["sun"]["incidence_deg"] for m in pair), [7.64, 81.08])
        for key in ("crop_x0", "crop_y0", "scale_m_per_px", "center_lat", "center_lon"):
            self.assertEqual(pair[0][key], pair[1][key])
        self.assertEqual(pair[0]["source"]["source_transform"], pair[1]["source"]["source_transform"])
        self.assertEqual(pair[0]["source"]["source_crs_wkt"], pair[1]["source"]["source_crs_wkt"])

    def test_installation_is_offline_and_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            self.assertEqual(install_dataset(output), 26)
            self.assertEqual(len(list(output.iterdir())), 104)
            self.assertEqual(install_dataset(output), 26)
            first = self.manifest["image_ids"][0]
            image = np.load(output / f"{first}.npy", allow_pickle=False)
            self.assertGreater(float(image.std()), 0.01)

    def test_installation_does_not_overwrite_modified_files_or_keep_old_catalogue(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            first = self.manifest["image_ids"][0]
            path = output / f"{first}.json"
            path.write_text('user edit')
            with self.assertRaises(FileExistsError):
                install_dataset(output)
            self.assertEqual(path.read_text(), 'user edit')
            path.unlink()
            legacy = output / f"{first}_craters_catalogue.json"
            legacy.write_text('{}')
            with self.assertRaisesRegex(ValueError, "Catalogue cũ"):
                install_dataset(output, overwrite=True)
            self.assertEqual(list(output.iterdir()), [legacy])

    def test_corrupted_archive_is_rejected_before_installation(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "bundle"
            shutil.copytree(BUNDLE_DIR, directory)
            archive = directory / self.manifest["archive"]["filename"]
            with archive.open("r+b") as handle:
                handle.seek(100); handle.write(b'corrupt')
            output = Path(tmp) / "processed"
            with self.assertRaisesRegex(ValueError, "SHA256"):
                install_dataset(output, bundle_dir=directory)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
