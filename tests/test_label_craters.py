import sys
import unittest
import json
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import matplotlib
matplotlib.use("Agg")

from scripts.label_craters import LabelApp
from src.contracts import validate_crater_set

class TestLabelCraters(unittest.TestCase):
    def setUp(self):
        self.app = LabelApp("moon_ap16_m106777343r_c01", source_arg="", auto_uncertain=False)

    def tearDown(self):
        import matplotlib.pyplot as plt
        plt.close(self.app.fig)

    def test_loads_existing_labels_correctly(self):
        # Đã nạp ít nhất 4 hố mẫu C1, C2, C3, C4
        self.assertGreaterEqual(len(self.app.items), 4)
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
                "x": 100.0,
                "y": 100.0,
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
        
        # Dọn dẹp hố thử nghiệm
        self.app.items.pop()

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
        self.app.items.pop()

    def test_save_succeeds_on_valid_data(self):
        success = self.app._save()
        self.assertTrue(success)


if __name__ == "__main__":
    unittest.main()
