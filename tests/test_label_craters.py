import sys
import unittest
import json
import tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from scripts.label_craters import LabelApp


class TestLabelCraters(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        self.processed_dir = self.tmp_path / "processed"
        self.ref_dir = self.tmp_path / "reference_labels"
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.ref_dir.mkdir(parents=True, exist_ok=True)

        self.image_id = "test_crop_01"
        meta = {
            "schema_version": "1.0",
            "data_kind": "real",
            "image_id": self.image_id,
            "source_stt": 10,
            "product_id": "M106777343R",
            "body": "moon",
            "crop_x0": 0,
            "crop_y0": 0,
            "downsample_k": 1,
            "width": 512,
            "height": 512,
            "scale_m_per_px": 2.0,
            "center_lat": -9.0,
            "center_lon": 15.0,
            "north_up": True,
            "north_angle_deg": 0.0,
            "sun": {
                "azimuth_deg": None,
                "incidence_deg": 28.38,
                "quality": "none",
                "source": "LROC PHO",
            },
            "radius": {
                "d_min_m": 20.0,
                "d_max_m": 500.0,
                "r_min_px": 5,
                "r_max_px": 125,
            },
            "valid_ratio": 1.0,
            "preprocess": {
                "version": "s106-pipeline",
                "p_lo": 0.5,
                "p_hi": 99.5,
            },
        }
        (self.processed_dir / f"{self.image_id}.json").write_text(
            json.dumps(meta, indent=2), encoding="utf-8"
        )
        dummy_img = np.zeros((512, 512), dtype=np.float32)
        np.save(self.processed_dir / f"{self.image_id}.npy", dummy_img)

        # Tạo file nhãn có sẵn để kiểm tra nạp nhãn cũ
        existing_catalogue = {
            "schema_version": "1.0",
            "data_kind": "real",
            "image_id": self.image_id,
            "source": "catalogue",
            "reference_source": "manual_label_s110; fixture",
            "circles": [
                {"crater_id": "C1", "x": 100.0, "y": 100.0, "r": 10.0, "confidence": None, "votes": None},
                {"crater_id": "C2", "x": 200.0, "y": 200.0, "r": 15.0, "confidence": None, "votes": None},
                {"crater_id": "C3", "x": 300.0, "y": 300.0, "r": 8.0, "confidence": None, "votes": None},
                {"crater_id": "C4_uncertain", "x": 400.0, "y": 400.0, "r": 12.0, "confidence": None, "votes": None},
            ],
        }
        (self.ref_dir / f"{self.image_id}_craters_catalogue.json").write_text(
            json.dumps(existing_catalogue, indent=2), encoding="utf-8"
        )

        self.app = LabelApp(
            self.image_id,
            source_arg="",
            auto_uncertain=False,
            processed_dir=self.processed_dir,
            ref_dir=self.ref_dir,
        )

    def tearDown(self):
        plt.close(self.app.fig)
        self.tmp.cleanup()

    def test_loads_existing_labels_correctly(self):
        # Đã nạp 4 hố mẫu C1, C2, C3, C4
        self.assertEqual(len(self.app.items), 4)
        cids = [it["data"]["crater_id"] for it in self.app.items]
        self.assertIn("C1", cids)
        self.assertIn("C4_uncertain", cids)
        # Counter tiếp theo phải là 5 (không bị reset về 1)
        self.assertEqual(self.app.counter, 5)

    def test_extent_and_pixel_conventions(self):
        extent = list(self.app.ax.images[0].get_extent())
        # Extent phải là [-0.5, 511.5, 511.5, -0.5]
        self.assertEqual(extent, [-0.5, 511.5, 511.5, -0.5])

    def test_toggle_uncertain_key_u(self):
        # Thêm 1 hố mới C5
        self.app.items.append({
            "data": {
                "crater_id": "C5",
                "x": 150.0,
                "y": 150.0,
                "r": 10.0,
                "confidence": None,
                "votes": None,
                "_uncertain": False,
            },
            "patch": None,
            "text": None,
            "is_existing": False,
        })

        class FakeEvent:
            key = "u"

        self.app._on_key(FakeEvent())
        self.assertTrue(self.app.items[-1]["data"]["_uncertain"])
        self.assertEqual(self.app.items[-1]["data"]["crater_id"], "C5_uncertain")

        # Bấm U lần nữa thì bỏ uncertain
        self.app._on_key(FakeEvent())
        self.assertFalse(self.app.items[-1]["data"]["_uncertain"])
        self.assertEqual(self.app.items[-1]["data"]["crater_id"], "C5")

    def test_undo_key_z_priority(self):
        class FakeEvent:
            key = "z"

        # Khi đang chờ click vành: Z phải hủy tâm chờ, không xóa hố đã ghi
        initial_count = len(self.app.items)
        self.app.state = "wait_edge"
        self.app.pending_center = (200.0, 200.0)

        self.app._on_key(FakeEvent())
        self.assertEqual(self.app.state, "idle")
        self.assertIsNone(self.app.pending_center)
        self.assertEqual(len(self.app.items), initial_count)

    def test_save_fails_gracefully_on_invalid_data(self):
        # Tạo hố ngoài phạm vi x = 512.5 (vi phạm schema)
        self.app.items.append({
            "data": {
                "crater_id": "C99",
                "x": 512.5,
                "y": 200.0,
                "r": 10.0,
                "confidence": None,
                "votes": None,
                "_uncertain": False,
            },
            "patch": None,
            "text": None,
            "is_existing": False,
        })
        success = self.app._save()
        self.assertFalse(success, "Lưu dữ liệu sai hợp đồng phải trả về False để không đóng cửa sổ")

    def test_save_succeeds_on_valid_data(self):
        success = self.app._save()
        self.assertTrue(success)
        self.assertTrue((self.ref_dir / f"{self.image_id}_craters_catalogue.json").exists())


if __name__ == "__main__":
    unittest.main()
