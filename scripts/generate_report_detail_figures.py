"""Dựng hình tiền xử lý/Hough có ô phóng chi tiết, giữ nguyên ảnh lịch sử.

    python -B scripts/generate_report_detail_figures.py --out-dir outputs/report_details

Đầu ra: tien_xu_ly_stt13_phong_to.png (1280×688),
hough_gia_lap_phong_to.png (2048×570). Mỗi ô phóng dùng cùng vùng 64×64 px,
phóng 4 lần so với ô toàn ảnh và giữ thang hiển thị của ô đó. Bộ ảnh được
cài từ bundle vào thư mục tạm; không cần data/processed hoặc truy cập mạng.
JSON trên stdout ghi tọa độ, số biên/vòng và hash để đối chiếu khi tái tạo.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile

os.environ.setdefault("MPLBACKEND", "Agg")

# Import dưới đây đặt sau cấu hình backend/sys.path ở trên; giữ thứ tự (E402).
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import hsv_to_rgb  # noqa: E402
from matplotlib.patches import Circle, Rectangle  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.install_s106_dataset import install_dataset  # noqa: E402
from scripts.verify_hough_examples import comparison, nearest_truth  # noqa: E402
from src.pipeline import load_image  # noqa: E402
from src.preprocessing import preprocess  # noqa: E402

IMAGE_ID = "moon_ap16_m132732855l_c01"
PREPROCESS_ROI = (64, 104, 64)
HOUGH_ROI = (0, 388, 64)
GOLD = "#ffcc33"
SOFTWARE = {"Software": "NASA24 report detail figures"}


def sha(path: Path) -> str:
    """Tính SHA-256 của một tệp.

    Vào: đường dẫn tệp. Ra: chuỗi băm thập lục phân; không ghi tệp.
    """
    return hashlib.sha256(path.read_bytes()).hexdigest()


def show(ax, image: np.ndarray, *, cmap="gray") -> None:
    """Hiển thị ảnh với thang màu và giới hạn trục cố định.

    Vào: trục ax, mảng ảnh và bảng màu tùy chọn. Ra: None; cập nhật ax, dùng [0, 1] cho ảnh xám và
    nội suy nearest.
    """
    ax.imshow(
        image,
        cmap=cmap,
        vmin=0 if cmap else None,
        vmax=1 if cmap else None,
        interpolation="nearest",
    )
    height, width = image.shape[:2]
    ax.set_xlim(-0.5, width - 0.5)
    ax.set_ylim(height - 0.5, -0.5)
    ax.set_xticks([])
    ax.set_yticks([])


def detail(ax, image: np.ndarray, roi: tuple[int, int, int], *, cmap="gray", upper=False):
    """Thêm khung nguồn và ô phóng chi tiết vào trục ảnh.

    Vào: ax, ảnh, ROI (x, y, cạnh), bảng màu và vị trí ô phóng. Ra: trục ô phóng; với ảnh 512 và
    ROI 64, ô rộng nửa ảnh cho độ phóng 512/64 × 1/2 = 4 lần.
    """
    x, y, size = roi
    ax.add_patch(
        Rectangle((x - 0.5, y - 0.5), size, size, fill=False, edgecolor=GOLD, linewidth=1)
    )
    zoom = ax.inset_axes([0.49, 0.49 if upper else 0.03, 0.5, 0.5], zorder=10)
    show(zoom, image, cmap=cmap)
    zoom.set_xlim(x - 0.5, x + size - 0.5)
    zoom.set_ylim(y + size - 0.5, y - 0.5)
    for spine in zoom.spines.values():
        spine.set_color(GOLD)
        spine.set_linewidth(1.2)
    zoom.text(
        0.04,
        0.96,
        "×4 · 64×64 px",
        transform=zoom.transAxes,
        va="top",
        color=GOLD,
        fontsize=8,
        bbox={"facecolor": "black", "alpha": 0.8, "pad": 1},
    )
    return zoom


def preprocessing_figure(path: Path) -> dict:
    """Vẽ chuỗi tiền xử lý có phóng vùng kết cấu đã gán nhãn.

    Vào: đường dẫn PNG. Ra: dict tọa độ, số biên và băm đối chiếu; ghi PNG 1280×688 tại path, cài
    dữ liệu trong thư mục tạm và kiểm tham số với hồ sơ; minh họa mục 4.6.
    """
    with tempfile.TemporaryDirectory(prefix="report_detail_") as temporary:
        processed = Path(temporary) / "processed"
        with contextlib.redirect_stdout(io.StringIO()):
            install_dataset(processed)
        metadata, image, valid = load_image(IMAGE_ID, processed)
        result = preprocess(image, metadata, None, valid_mask=valid)

    expected_path = ROOT / "docs/evidence/s1-14" / f"tham_so_{IMAGE_ID}.json"
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    for key in ("edge_px_canny", "edge_px_final", "canny_low", "canny_high"):
        if result["params"][key] != expected[key]:
            raise ValueError(
                f"Tiền xử lý khác hồ sơ lịch sử ở {key}; cần đối chiếu trước khi minh họa."
            )
    label_path = ROOT / "data/s202_labels" / f"{IMAGE_ID}.json"
    labels = json.loads(label_path.read_text(encoding="utf-8"))
    known = next(c for c in labels["candidates"] if c["crater_id"] == "M3")
    x, y, size = PREPROCESS_ROI
    assert (
        known["label"] == "texture" and x <= known["x"] < x + size and y <= known["y"] < y + size
    )
    before = int(result["edges_canny"][y: y + size, x: x + size].sum())
    after = int(result["edges"][y: y + size, x: x + size].sum())
    assert before == after and after > 0, "Vùng chọn phải cho thấy biên trong ảnh còn sau B8."

    magnitude = np.clip(result["mag"] / np.percentile(result["mag"], 99), 0, 1)
    hue = (result["theta"] + np.pi) / (2 * np.pi)
    direction = hsv_to_rgb(np.dstack([hue, np.ones_like(hue), magnitude]))
    panels = [
        ("Đầu vào", image, "gray", "#6e7781"),
        ("B3 chuẩn hóa", result["gray"], "gray", "#1f6feb"),
        ("B4 CLAHE", result["enhanced"], "gray", "#d1495b"),
        ("B5 Gauss σ=1,5", result["smooth"], "gray", "#1f6feb"),
        ("B6 |G|", magnitude, "gray", "#1f6feb"),
        ("B6 θ × |G|", direction, None, "#1f6feb"),
        (f"B7 Canny ({expected['edge_px_canny']} px)", result["edges_canny"], "gray", "#d1495b"),
        (f"B8 mặt nạ ({expected['edge_px_final']} px)", result["edges"], "gray", "#1f6feb"),
    ]
    fig, axes = plt.subplots(2, 4, figsize=(16, 8.6), constrained_layout=True)
    for ax, (title, data, cmap, color) in zip(axes.ravel(), panels):
        show(ax, data, cmap=cmap)
        ax.set_title(title, fontsize=10, color=color)
        detail(ax, data, PREPROCESS_ROI, cmap=cmap)
    fig.suptitle(
        "STT 13 · khung vàng: cùng vùng kết cấu · xanh: tự viết, đỏ: thư viện", fontsize=12
    )
    fig.savefig(path, dpi=80, metadata=SOFTWARE)
    plt.close(fig)
    return {
        "image_id": IMAGE_ID,
        "size_px": [1280, 688],
        "roi_xywh": [x, y, size, size],
        "zoom_relative_to_full_panel": 4,
        "display_range": [0, 1],
        "magnitude_scale": "same global P99 before cropping; hue encodes theta",
        "known_texture": {k: known[k] for k in ("crater_id", "x", "y", "r", "label")},
        "edge_count_full": [expected["edge_px_canny"], expected["edge_px_final"]],
        "edge_count_roi": [before, after],
        "label_sha256": sha(label_path),
        "parameters_sha256": sha(expected_path),
        "image_array_sha256": hashlib.sha256(image.tobytes()).hexdigest(),
    }


def circles(ax, truth: list[dict], found: list[dict]) -> None:
    """Vẽ vòng thật và vòng phát hiện bằng hai kiểu nét.

    Vào: trục ax, danh sách truth và found. Ra: None; thêm vòng xanh liền và đỏ đứt vào ax, giữ tọa
    độ thực.
    """
    for rows, color, style in ((truth, "#22d34a", "-"), (found, "#ff3939", "--")):
        for circle in rows:
            ax.add_patch(
                Circle(
                    (circle["x"], circle["y"]),
                    circle["r"],
                    fill=False,
                    edgecolor=color,
                    linestyle=style,
                    linewidth=1,
                )
            )


def hough_figure(path: Path) -> dict:
    """Vẽ đối chiếu Hough có ô phóng cùng vùng và cùng thang sáng.

    Vào: đường dẫn PNG. Ra: dict vùng phóng, đáp án và kết quả vẽ; ghi PNG 2048×570, kiểm số vòng
    3/1/4 và bù tâm OpenCV −0,5 px để minh họa mục 4.7.
    """
    report, arrays = comparison()
    methods = ("full_circle", "gradient", "opencv")
    counts = {m: len(report["results"][m]["detections"]) for m in methods}
    if counts != {"full_circle": 3, "gradient": 1, "opencv": 4}:
        raise ValueError("Số vòng khác hồ sơ S1-12; cần đối chiếu trước khi dựng hình báo cáo.")
    found = {}
    for method in methods:
        shift = 0.5 if method == "opencv" else 0
        corrected = [
            {**c, "x": c["x"] - shift, "y": c["y"] - shift}
            for c in report["results"][method]["detections"]
        ]
        found[method] = nearest_truth(corrected, report["truth"])
    image = arrays["gray_u8"].astype(float) / 255
    fig = plt.figure(figsize=(20.48, 5.7))
    titles = ("Đầu vào", "Toàn vòng (3)", "Gradient (1)", "OpenCV (4)")
    for i, (method, title) in enumerate(zip(("input", *methods), titles)):
        ax = fig.add_axes([i / 4, 0, 1 / 4, 512 / 570])
        show(ax, image)
        detections = [] if method == "input" else found[method]
        circles(ax, report["truth"], detections)
        zoom = detail(ax, image, HOUGH_ROI, upper=True)
        circles(zoom, report["truth"], detections)
        fig.text(i / 4 + 0.006, 0.97, title, va="top", fontsize=13)
        fig.text(i / 4 + 0.006, 0.922, "Thật: xanh liền; tìm: đỏ đứt", va="top", fontsize=10)
    fig.savefig(path, dpi=100, metadata=SOFTWARE)
    plt.close(fig)
    x, y, size = HOUGH_ROI
    return {
        "size_px": [2048, 570],
        "roi_xywh": [x, y, size, size],
        "zoom_relative_to_full_panel": 4,
        "display_range": [0, 1],
        "input_sha256": hashlib.sha256(arrays["gray_u8"].tobytes()).hexdigest(),
        "truth": report["truth"],
        "counts": counts,
        "opencv_center_shift_px": [-0.5, -0.5],
        "detections_plot_coordinates": found,
        "radius_range_px": report["radius_range_px"],
    }


def main() -> int:
    """Sinh hai hình chi tiết và in thông tin tái tạo.

    Vào: CLI --out-dir. Ra: mã 0; ghi tien_xu_ly_stt13_phong_to.png và hough_gia_lap_phong_to.png
    vào thư mục mới, từ chối ghi đè và in JSON có băm; xem Phụ lục A.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out-dir", type=Path, default=ROOT / "docs/images/report")
    args = parser.parse_args()
    names = ("tien_xu_ly_stt13_phong_to.png", "hough_gia_lap_phong_to.png")
    paths = [args.out_dir / name for name in names]
    if any(path.exists() for path in paths):
        parser.error("Ảnh đầu ra đã tồn tại; chọn thư mục mới để giữ bản cũ.")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    result = {names[0]: preprocessing_figure(paths[0]), names[1]: hough_figure(paths[1])}
    for name, path in zip(names, paths):
        result[name]["sha256"] = sha(path)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
