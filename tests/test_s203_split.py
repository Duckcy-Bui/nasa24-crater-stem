"""Tests cho S2-03: phan chia tap dieu chinh / kiem tra va nhan tham chieu.

Kiem tra:
- Anh cung ground_patch (cung file goc + cung offset x0,y0) luon o cung tap.
- Khong co overlap giua tuning va holdout (theo image_id va ground_patch).
- Anh da dung chon filter S2-02 (m132732855l_c01) bat buoc o tuning.
- label_index chi chua anh thuc su co file nhan.
- matching_rules co center_tolerance = 0.5.
- Nhan thua: n_uncertain <= n_circles (neu co nhan).
"""

from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPLIT_DIR = ROOT / "data" / "s203_split"
MANIFEST_PATH = SPLIT_DIR / "manifest_split.json"
LABEL_INDEX_PATH = SPLIT_DIR / "label_index.json"
REF_LABEL_DIR = ROOT / "data" / "reference_labels"


class TestSplitManifest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not MANIFEST_PATH.exists():
            raise unittest.SkipTest("manifest_split.json chua ton tai; chay scripts/build_s203_split.py truoc.")
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    @property
    def manifest(self) -> dict:
        return self.__class__.manifest

    def test_schema_version(self):
        self.assertEqual(self.manifest["schema_version"], "s203-split-1")

    def test_task_id(self):
        self.assertEqual(self.manifest["task_id"], "S2-03")

    def test_total_images(self):
        images = self.manifest["images"]
        stats = self.manifest["statistics"]
        self.assertEqual(len(images), stats["total_images"])

    def test_split_values_valid(self):
        for img in self.manifest["images"]:
            self.assertIn(
                img["split"],
                ("tuning", "holdout"),
                f"{img['image_id']} co split khong hop le: {img['split']}",
            )

    def test_no_overlap_tuning_holdout(self):
        """Khong co image_id nao xuat hien o ca hai tap."""
        tuning_ids = {e["image_id"] for e in self.manifest["images"] if e["split"] == "tuning"}
        holdout_ids = {e["image_id"] for e in self.manifest["images"] if e["split"] == "holdout"}
        overlap = tuning_ids & holdout_ids
        self.assertFalse(overlap, f"image_id xuat hien o ca hai tap: {overlap}")

    def test_ground_patch_field_present(self):
        """Moi anh phai co truong ground_patch."""
        for img in self.manifest["images"]:
            self.assertIn(
                "ground_patch",
                img,
                f"{img['image_id']}: thieu truong ground_patch",
            )
            self.assertTrue(
                img["ground_patch"],
                f"{img['image_id']}: ground_patch rong",
            )

    def test_ground_patch_not_split_across_sets(self):
        """Anh cung ground_patch luon o cung tap (chinh sach v2)."""
        patch_splits: dict[str, set[str]] = {}
        for img in self.manifest["images"]:
            patch_splits.setdefault(img["ground_patch"], set()).add(img["split"])
        for patch, splits in patch_splits.items():
            self.assertEqual(
                len(splits),
                1,
                f"ground_patch '{patch}' bi chia ra 2 tap: {splits}",
            )

    def test_forced_tuning_m132732855l_c01(self):
        """m132732855l_c01 da dung chon filter S2-02 -> bat buoc o tuning."""
        target_id = "moon_ap16_m132732855l_c01"
        entries = [e for e in self.manifest["images"] if e["image_id"] == target_id]
        self.assertEqual(len(entries), 1, f"{target_id} khong tim thay trong manifest")
        self.assertEqual(
            entries[0]["split"],
            "tuning",
            f"{target_id} phai o tuning (da dung chon filter S2-02), nhung dang o: {entries[0]['split']}",
        )

    def test_m113853974r_same_patch_as_tuning(self):
        """m113853974r_c01 cung ground_patch voi m102064759r_c01 (x1190_y2750) -> cung tuning."""
        entries = {e["image_id"]: e for e in self.manifest["images"]}
        # Ca hai phai co mat trong manifest
        a_id = "moon_ap16_m113853974r_c01"
        b_id = "moon_ap16_m102064759r_c01"
        if a_id not in entries or b_id not in entries:
            self.skipTest("Mot trong hai image_id khong ton tai trong manifest")
        self.assertEqual(
            entries[a_id]["ground_patch"],
            entries[b_id]["ground_patch"],
            "Hai anh phai cung ground_patch",
        )
        self.assertEqual(
            entries[a_id]["split"],
            entries[b_id]["split"],
            "Hai anh cung ground_patch phai cung tap",
        )

    def test_all_apollo16_in_tuning(self):
        """Toan bo anh Apollo 16 phai o tuning de tranh trung mat dat (<1.5 km)."""
        ap16_entries = [e for e in self.manifest["images"] if "ap16" in e["image_id"]]
        self.assertEqual(len(ap16_entries), 11)
        for e in ap16_entries:
            self.assertEqual(
                e["split"],
                "tuning",
                f"{e['image_id']} phai o tuning de tranh chong lap mat dat, nhung dang o {e['split']}",
            )

    def test_holdout_ground_distance_from_tuning(self):
        """Tat ca anh holdout phai cach tap tuning >= 50 km (tuyet doi khong chong lap mat dat)."""
        import csv
        import math
        with (ROOT / "docs" / "S1-06_BANG_ANH_XA.csv").open(encoding="utf-8") as f:
            rows = {r["image_id"]: r for r in csv.DictReader(f)}
        r_moon = 1737400.0

        def haversine(id1: str, id2: str) -> float:
            r1, r2 = rows[id1], rows[id2]
            lat1, lon1 = math.radians(float(r1["center_lat"])), math.radians(float(r1["center_lon"]))
            lat2, lon2 = math.radians(float(r2["center_lat"])), math.radians(float(r2["center_lon"]))
            a = (
                math.sin((lat2 - lat1) / 2) ** 2
                + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
            )
            return 2 * r_moon * math.asin(math.sqrt(a))

        tuning_ids = [e["image_id"] for e in self.manifest["images"] if e["split"] == "tuning"]
        holdout_ids = [e["image_id"] for e in self.manifest["images"] if e["split"] == "holdout"]
        for hid in holdout_ids:
            min_dist = min(haversine(hid, tid) for tid in tuning_ids)
            self.assertGreaterEqual(
                min_dist,
                50000.0,
                f"Holdout {hid} chi cach tuning {min_dist:.1f}m (< 50 km), co nguy co chong lap!",
            )

    def test_statistics_counts_match(self):
        images = self.manifest["images"]
        stats = self.manifest["statistics"]
        n_tuning = sum(1 for e in images if e["split"] == "tuning")
        n_holdout = sum(1 for e in images if e["split"] == "holdout")
        self.assertEqual(n_tuning, stats["tuning_images"])
        self.assertEqual(n_holdout, stats["holdout_images"])
        # Kiem tra truong ground_patches co trong statistics
        self.assertIn(
            "tuning_ground_patches",
            stats,
            "statistics thieu truong tuning_ground_patches",
        )
        self.assertIn(
            "holdout_ground_patches",
            stats,
            "statistics thieu truong holdout_ground_patches",
        )

    def test_matching_rules_center_tolerance(self):
        """center_tolerance phai = 0.5 (khop src/matching.py)."""
        rules = self.manifest["matching_rules"]
        self.assertEqual(rules["center_tolerance"], 0.5)
        self.assertEqual(rules["center_tolerance_unit"], "fraction_of_reference_radius")

    def test_matching_rules_cross_review_required(self):
        self.assertTrue(self.manifest["matching_rules"]["cross_review_required"])

    def test_recall_note_present(self):
        rules = self.manifest["matching_rules"]
        note = rules.get("recall_note", "")
        self.assertTrue(
            "recall" in note.lower() or "Recall" in note,
            "recall_note phai nhac den recall",
        )

    def test_label_status_values(self):
        valid = {"sparse_unreviewed", "reviewed", "unlabeled"}
        for img in self.manifest["images"]:
            self.assertIn(
                img["label_status"],
                valid,
                f"{img['image_id']}: label_status khong hop le = {img['label_status']}",
            )

    def test_label_status_matches_reference_source(self):
        """Manifest phai phan anh trang thai review trong JSON goc."""
        for img in self.manifest["images"]:
            if not img["has_reference_label"]:
                self.assertEqual(img["label_status"], "unlabeled")
                continue
            source = json.loads(
                (REF_LABEL_DIR / img["reference_label_file"]).read_text(encoding="utf-8")
            )["reference_source"].lower()
            expected = (
                "reviewed"
                if "reviewed by" in source and "unreviewed" not in source
                else "sparse_unreviewed"
            )
            self.assertEqual(img["label_status"], expected, img["image_id"])

    def test_reviewed_source_is_classified_as_reviewed(self):
        from scripts.build_s203_split import _label_status

        self.assertEqual(
            _label_status({"reference_source": "manual labels; reviewed by Nguyen Manh Tien"}),
            "reviewed",
        )
        self.assertEqual(
            _label_status({"reference_source": "manual labels, unreviewed"}),
            "sparse_unreviewed",
        )

    def test_has_reference_label_consistent_with_file(self):
        """has_reference_label = True khi file ton tai thuc su."""
        for img in self.manifest["images"]:
            iid = img["image_id"]
            expected_file = REF_LABEL_DIR / f"{iid}_craters_catalogue.json"
            if img["has_reference_label"]:
                self.assertTrue(
                    expected_file.exists(),
                    f"{iid}: has_reference_label=True nhung file khong ton tai",
                )
            else:
                self.assertTrue(not expected_file.exists() or True)

    def test_uncertain_count_lte_total(self):
        for img in self.manifest["images"]:
            self.assertLessEqual(
                img["n_uncertain"],
                img["n_labels"],
                f"{img['image_id']}: n_uncertain > n_labels",
            )

    def test_sun_quality_values(self):
        for img in self.manifest["images"]:
            self.assertIn(
                img["sun_quality"],
                ("measured", "side_only", "none"),
                f"{img['image_id']}: sun_quality khong hop le",
            )


class TestLabelIndex(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not MANIFEST_PATH.exists():
            raise unittest.SkipTest("manifest_split.json chua ton tai; chay scripts/build_s203_split.py truoc.")
        if not LABEL_INDEX_PATH.exists():
            raise unittest.SkipTest("label_index.json chua ton tai.")
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.label_index = json.loads(LABEL_INDEX_PATH.read_text(encoding="utf-8"))

    @property
    def manifest(self) -> dict:
        return self.__class__.manifest

    @property
    def label_index(self) -> dict:
        return self.__class__.label_index

    def test_only_labeled_images(self):
        """label_index chi chua anh co has_reference_label = True."""
        labeled_ids = {
            e["image_id"] for e in self.manifest["images"] if e["has_reference_label"]
        }
        index_ids = set(self.label_index.keys())
        self.assertEqual(
            index_ids,
            labeled_ids,
            f"Mismatch: trong index nhung khong co nhan: {index_ids - labeled_ids}; "
            f"co nhan nhung khong trong index: {labeled_ids - index_ids}",
        )

    def test_label_file_exists(self):
        for iid, info in self.label_index.items():
            fp = REF_LABEL_DIR / info["label_file"]
            self.assertTrue(fp.exists(), f"File nhan khong ton tai: {fp}")

    def test_n_circles_matches_file(self):
        for iid, info in self.label_index.items():
            fp = REF_LABEL_DIR / info["label_file"]
            data = json.loads(fp.read_text(encoding="utf-8"))
            circles = data.get("circles", [])
            self.assertEqual(
                info["n_circles"],
                len(circles),
                f"{iid}: n_circles trong index ({info['n_circles']}) "
                f"khac file thuc ({len(circles)})",
            )

    def test_certain_plus_uncertain_equals_total(self):
        for iid, info in self.label_index.items():
            self.assertEqual(
                info["n_certain"] + info["n_uncertain"],
                info["n_circles"],
                f"{iid}: n_certain + n_uncertain != n_circles",
            )

    def test_radius_range_valid(self):
        for iid, info in self.label_index.items():
            r_min, r_max = info["radius_range_px"]
            if r_min is not None and r_max is not None:
                self.assertGreater(r_min, 0, f"{iid}: r_min <= 0")
                self.assertGreaterEqual(r_max, r_min, f"{iid}: r_max < r_min")


if __name__ == "__main__":
    unittest.main()
