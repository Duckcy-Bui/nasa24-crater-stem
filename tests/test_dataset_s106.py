"""Kiểm tra hợp đồng dữ liệu cho toàn bộ 26 ảnh cắt S1-06."""

import glob
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from src.contracts import validate_crater_set, validate_metadata


class S106DatasetContractTest(unittest.TestCase):
    def test_all_processed_images_have_valid_metadata_and_catalogue(self):
        json_files = sorted(glob.glob(str(ROOT / "data" / "processed" / "moon_*.json")))
        # Chỉ kiểm tra các file metadata (không phải _craters_catalogue.json)
        metadata_files = [p for p in json_files if not p.endswith("_craters_catalogue.json")]
        self.assertGreaterEqual(len(metadata_files), 20, "Cần tối thiểu 20 ảnh cắt theo mục tiêu S1-06")

        for meta_path_str in metadata_files:
            meta_path = Path(meta_path_str)
            with meta_path.open(encoding="utf-8") as f:
                metadata = json.load(f)

            # 1. Kiểm tra metadata khớp chuẩn 1.0 và data_kind == real
            validate_metadata(metadata)
            self.assertEqual(metadata["schema_version"], "1.0")
            self.assertEqual(metadata["data_kind"], "real")
            self.assertEqual(metadata["width"], 512)
            self.assertEqual(metadata["height"], 512)
            self.assertEqual(metadata["valid_ratio"], 1.0)

            # 2. Kiểm tra có đủ file .npy và .png tương ứng
            image_id = metadata["image_id"]
            npy_file = meta_path.parent / f"{image_id}.npy"
            png_file = meta_path.parent / f"{image_id}.png"
            self.assertTrue(npy_file.exists(), f"Thiếu file npy: {npy_file}")
            self.assertTrue(png_file.exists(), f"Thiếu file png: {png_file}")

            # 3. Kiểm tra file catalogue tương ứng nếu có
            cat_file = meta_path.parent / f"{image_id}_craters_catalogue.json"
            if cat_file.exists():
                with cat_file.open(encoding="utf-8") as f:
                    cat_data = json.load(f)
                validate_crater_set(cat_data, metadata)


if __name__ == "__main__":
    unittest.main()
