"""Tính trung bình ± độ lệch chuẩn theo ảnh cho các bảng kết quả Chương 4.

Đầu vào là hai bảng đã lưu trong hồ sơ:
- docs/evidence/s2-15/results.csv: 18 ảnh tuning, cấu hình game đã chốt (score).
- docs/evidence/s2-06-s3-02/results.csv: 3 ảnh tuning và 8 ảnh holdout, ba cách Hough.

Đầu ra: docs/evidence/s3-12/ch4_mean_sd.csv (hoặc --out), mỗi dòng một nhóm
(nguồn, tập, phương pháp) với số ảnh n, Recall_known trung bình ± độ lệch chuẩn mẫu
theo ảnh, Recall_known gộp TP/(TP+FN), thời gian trung bình ± độ lệch chuẩn.

Công thức: trung bình x̄ = Σx_i / n; độ lệch chuẩn mẫu s = sqrt(Σ(x_i − x̄)² / (n − 1)),
s = 0 khi n = 1. Recall_known = TP / (TP + FN) trên nhãn đã biết (mục 4.5).
Không tính Precision vì nhãn thưa (không biết FP).
"""

from __future__ import annotations

import argparse
import csv
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S215 = ROOT / "docs/evidence/s2-15/results.csv"
S206 = ROOT / "docs/evidence/s2-06-s3-02/results.csv"
DEFAULT_OUT = ROOT / "docs/evidence/s3-12/ch4_mean_sd.csv"

FIELDS = [
    "source", "split", "method", "n_images",
    "recall_mean", "recall_sd", "tp", "labels", "recall_pooled",
    "seconds_mean", "seconds_sd",
]


def mean_sd(values: list[float]) -> tuple[float, float]:
    """Trả (trung bình, độ lệch chuẩn mẫu) của danh sách số; sd = 0 khi chỉ có một giá trị."""
    if not values:
        raise ValueError("danh sách rỗng")
    sd = statistics.stdev(values) if len(values) > 1 else 0.0
    return statistics.fmean(values), sd


def summarize(rows: list[dict], source: str, split: str, method: str,
              recall_key: str, tp_key: str, fn_key: str, seconds_key: str) -> dict:
    """Gộp các dòng theo ảnh của một nhóm thành một dòng tóm tắt theo FIELDS."""
    recalls = [float(r[recall_key]) for r in rows]
    seconds = [float(r[seconds_key]) for r in rows]
    tp = sum(int(r[tp_key]) for r in rows)
    labels = tp + sum(int(r[fn_key]) for r in rows)
    r_mean, r_sd = mean_sd(recalls)
    s_mean, s_sd = mean_sd(seconds)
    return {
        "source": source, "split": split, "method": method, "n_images": len(rows),
        "recall_mean": round(r_mean, 4), "recall_sd": round(r_sd, 4),
        "tp": tp, "labels": labels, "recall_pooled": round(tp / labels, 4) if labels else "",
        "seconds_mean": round(s_mean, 2), "seconds_sd": round(s_sd, 2),
    }


def build(s215: Path = S215, s206: Path = S206) -> list[dict]:
    """Đọc hai bảng hồ sơ và trả các dòng tóm tắt theo thứ tự cố định."""
    out = []
    with s215.open(encoding="utf-8", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["split"] == "tuning"]
    out.append(summarize(rows, "s2-15", "tuning", "numpy_score",
                         "recall_known", "tp_known", "fn_known", "seconds_hough"))
    with s206.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    for split in ("tuning", "holdout"):
        for method in ("numpy_score", "numpy_balanced", "opencv"):
            sel = [r for r in rows if r["split"] == split and r["method"] == method]
            if sel:
                out.append(summarize(sel, "s2-06-s3-02", split, method,
                                     "recall", "tp", "fn", "median_seconds"))
    return out


def main() -> None:
    """Ghi bảng tóm tắt ra CSV và in ra màn hình."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    rows = build()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    for r in rows:
        print("{source} {split} {method}: n={n_images}, Recall_known "
              "{recall_mean:.4f} ± {recall_sd:.4f} (gộp {tp}/{labels}), "
              "{seconds_mean:.2f} ± {seconds_sd:.2f} s".format(**r))


if __name__ == "__main__":
    main()
