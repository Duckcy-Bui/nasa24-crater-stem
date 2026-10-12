import copy
import math
import tempfile
import unittest
from pathlib import Path

from src.contracts import ContractError, radius_range_px, read_json, save_run, source_coordinates, validate_crater_set, validate_metadata

ROOT = Path(__file__).resolve().parents[1]


class ContractsTest(unittest.TestCase):
    def setUp(self):
        self.metadata = read_json(ROOT / "data/examples/s105_synthetic_512.json")
        self.craters = read_json(ROOT / "data/examples/craters_machine.json")

    def test_all_shared_sources_use_same_image(self):
        for source in ("machine", "catalogue", "player"):
            validate_crater_set(read_json(ROOT / f"data/examples/craters_{source}.json"), self.metadata)

    def test_radius_conversion_from_s104_example(self):
        self.assertEqual(radius_range_px(40, 500, 2), (10, 125))
        self.assertEqual(radius_range_px(1, 2000, 2), (5, 128))

    def test_unusable_radius_range_is_rejected(self):
        with self.assertRaises(ContractError):
            radius_range_px(1, 2, 100)

    def test_resize_center_offset_and_crop_origin(self):
        self.metadata.update(crop_x0=100, crop_y0=200, downsample_k=2, scale_m_per_px=4.0)
        self.metadata["radius"].update(r_min_px=5, r_max_px=62)
        self.assertEqual(source_coordinates(10, 20, 5, self.metadata), (120.5, 240.5, 10))

    def test_cross_image_merge_is_rejected(self):
        self.craters["image_id"] = "another_image"
        with self.assertRaises(ContractError):
            validate_crater_set(self.craters, self.metadata)

    def test_synthetic_results_cannot_be_mixed_with_real_metadata(self):
        self.craters["data_kind"] = "real"
        with self.assertRaises(ContractError):
            validate_crater_set(self.craters, self.metadata)

    def test_invalid_geometry_is_rejected(self):
        for field, value in (("x", -1), ("y", 512), ("r", 0), ("x", math.nan), ("r", True)):
            with self.subTest(field=field, value=value):
                data = copy.deepcopy(self.craters)
                data["circles"][0][field] = value
                with self.assertRaises(ContractError):
                    validate_crater_set(data, self.metadata)

    def test_duplicate_crater_id_is_rejected(self):
        self.craters["circles"].append(copy.deepcopy(self.craters["circles"][0]))
        with self.assertRaises(ContractError):
            validate_crater_set(self.craters, self.metadata)

    def test_unknown_sun_direction_is_not_invented(self):
        self.metadata["sun"]["azimuth_deg"] = 90
        with self.assertRaises(ContractError):
            validate_metadata(self.metadata)

    def test_metadata_radius_cannot_be_typed_inconsistently(self):
        self.metadata["radius"]["r_max_px"] = 128
        with self.assertRaises(ContractError):
            validate_metadata(self.metadata)

    def test_saved_run_can_be_read_back_and_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = save_run(folder, "test_01", metadata=self.metadata, crater_set=self.craters, params={"sigma": 1.5}, code_version="test-commit")
            self.assertEqual(read_json(directory / "craters.json"), self.craters)
            self.assertEqual(read_json(directory / "params.json"), {"sigma": 1.5})
            self.assertEqual(read_json(directory / "run.json")["code_version"], "test-commit")
            with self.assertRaises(FileExistsError):
                save_run(folder, "test_01", metadata=self.metadata, crater_set=self.craters, params={}, code_version="test-commit")

    def test_run_id_cannot_escape_output_folder(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ContractError):
                save_run(folder, "../escape", metadata=self.metadata, crater_set=self.craters, params={}, code_version="test-commit")


if __name__ == "__main__":
    unittest.main()
