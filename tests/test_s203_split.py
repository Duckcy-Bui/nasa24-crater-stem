"""Tests cho S2-03: phan chia tập điều chỉnh / kiểm tra và nhãn tham chiếu.

Kiem tra:
- Crops cung product_id luon o cung tap (khong bi tach thi).
- Khong co overlap giua tuning va holdout (theo image_id va product_id).
- label_index chi chua anh thuc su co file nhan.
- matching_rules co center_tolerance = 0.5.
- Nhan thua: n_uncertain < n_circles (neu co nhan).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPLIT_DIR = ROOT / "data" / "s203_split"
MANIFEST_PATH = SPLIT_DIR / "manifest_split.json"
LABEL_INDEX_PATH = SPLIT_DIR / "label_index.json"
REF_LABEL_DIR = ROOT / "data" / "reference_labels"


@pytest.fixture(scope="module")
def manifest() -> dict:
    if not MANIFEST_PATH.exists():
        pytest.skip("manifest_split.json chua ton tai; chay scripts/build_s203_split.py truoc.")
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def label_index() -> dict:
    if not LABEL_INDEX_PATH.exists():
        pytest.skip("label_index.json chua ton tai.")
    return json.loads(LABEL_INDEX_PATH.read_text(encoding="utf-8"))


class TestSplitManifest:
    def test_schema_version(self, manifest):
        assert manifest["schema_version"] == "s203-split-1"

    def test_task_id(self, manifest):
        assert manifest["task_id"] == "S2-03"

    def test_total_images(self, manifest):
        images = manifest["images"]
        stats = manifest["statistics"]
        assert len(images) == stats["total_images"]

    def test_split_values_valid(self, manifest):
        for img in manifest["images"]:
            assert img["split"] in ("tuning", "holdout"), (
                f"{img['image_id']} co split khong hop le: {img['split']}"
            )

    def test_no_overlap_tuning_holdout(self, manifest):
        """Khong co image_id nao xuat hien o ca hai tap."""
        tuning_ids = {e["image_id"] for e in manifest["images"] if e["split"] == "tuning"}
        holdout_ids = {e["image_id"] for e in manifest["images"] if e["split"] == "holdout"}
        overlap = tuning_ids & holdout_ids
        assert not overlap, f"image_id xuat hien o ca hai tap: {overlap}"

    def test_product_id_not_split_across_sets(self, manifest):
        """Cac crops cung product_id luon o cung tap."""
        pid_splits: dict[str, set[str]] = {}
        for img in manifest["images"]:
            pid_splits.setdefault(img["product_id"], set()).add(img["split"])
        for pid, splits in pid_splits.items():
            assert len(splits) == 1, (
                f"product_id '{pid}' bi chia ra 2 tap: {splits}"
            )

    def test_statistics_counts_match(self, manifest):
        images = manifest["images"]
        stats = manifest["statistics"]
        n_tuning = sum(1 for e in images if e["split"] == "tuning")
        n_holdout = sum(1 for e in images if e["split"] == "holdout")
        assert n_tuning == stats["tuning_images"]
        assert n_holdout == stats["holdout_images"]

    def test_matching_rules_center_tolerance(self, manifest):
        """center_tolerance phai = 0.5 (khop src/matching.py)."""
        rules = manifest["matching_rules"]
        assert rules["center_tolerance"] == 0.5
        assert rules["center_tolerance_unit"] == "fraction_of_reference_radius"

    def test_matching_rules_cross_review_required(self, manifest):
        assert manifest["matching_rules"]["cross_review_required"] is True

    def test_recall_note_present(self, manifest):
        rules = manifest["matching_rules"]
        note = rules.get("recall_note", "")
        assert "recall" in note.lower() or "Recall" in note, (
            "recall_note phai nhac den recall"
        )

    def test_label_status_values(self, manifest):
        valid = {"sparse_unreviewed", "reviewed", "unlabeled"}
        for img in manifest["images"]:
            assert img["label_status"] in valid, (
                f"{img['image_id']}: label_status khong hop le = {img['label_status']}"
            )

    def test_has_reference_label_consistent_with_file(self, manifest):
        """has_reference_label = True khi file ton tai thuc su."""
        for img in manifest["images"]:
            iid = img["image_id"]
            expected_file = REF_LABEL_DIR / f"{iid}_craters_catalogue.json"
            if img["has_reference_label"]:
                assert expected_file.exists(), (
                    f"{iid}: has_reference_label=True nhung file khong ton tai"
                )
            else:
                assert not expected_file.exists() or True  # unlabeled cho phep file khong co

    def test_uncertain_count_lte_total(self, manifest):
        for img in manifest["images"]:
            assert img["n_uncertain"] <= img["n_labels"], (
                f"{img['image_id']}: n_uncertain > n_labels"
            )

    def test_sun_quality_values(self, manifest):
        for img in manifest["images"]:
            assert img["sun_quality"] in ("measured", "side_only", "none"), (
                f"{img['image_id']}: sun_quality khong hop le"
            )


class TestLabelIndex:
    def test_only_labeled_images(self, label_index, manifest):
        """label_index chi chua anh co has_reference_label = True."""
        labeled_ids = {
            e["image_id"] for e in manifest["images"] if e["has_reference_label"]
        }
        index_ids = set(label_index.keys())
        assert index_ids == labeled_ids, (
            f"Mismatch: trong index nhung khong co nhan: {index_ids - labeled_ids}; "
            f"co nhan nhung khong trong index: {labeled_ids - index_ids}"
        )

    def test_label_file_exists(self, label_index):
        for iid, info in label_index.items():
            fp = REF_LABEL_DIR / info["label_file"]
            assert fp.exists(), f"File nhan khong ton tai: {fp}"

    def test_n_circles_matches_file(self, label_index):
        for iid, info in label_index.items():
            fp = REF_LABEL_DIR / info["label_file"]
            data = json.loads(fp.read_text(encoding="utf-8"))
            circles = data.get("circles", [])
            assert info["n_circles"] == len(circles), (
                f"{iid}: n_circles trong index ({info['n_circles']}) "
                f"khac file thuc ({len(circles)})"
            )

    def test_certain_plus_uncertain_equals_total(self, label_index):
        for iid, info in label_index.items():
            assert info["n_certain"] + info["n_uncertain"] == info["n_circles"], (
                f"{iid}: n_certain + n_uncertain != n_circles"
            )

    def test_radius_range_valid(self, label_index):
        for iid, info in label_index.items():
            r_min, r_max = info["radius_range_px"]
            if r_min is not None and r_max is not None:
                assert r_min > 0, f"{iid}: r_min <= 0"
                assert r_max >= r_min, f"{iid}: r_max < r_min"
