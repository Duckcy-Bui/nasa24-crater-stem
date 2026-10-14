"""S1-10 — Công cụ ghi nhãn hố tham chiếu thủ công và chuẩn hóa nhãn.

Cách dùng:
  .venv\\Scripts\\python.exe scripts/label_craters.py [image_id] [--source <ghi_chú>] [--uncertain]

Ví dụ:
  # Chạy ảnh demo mặc định (moon_ap16_m106777343r_c01)
  .venv\\Scripts\\python.exe scripts/label_craters.py

  # Chỉ định ảnh khác
  .venv\\Scripts\\python.exe scripts/label_craters.py moon_ap15_hia_c01

  # Ghi nhãn từ danh mục Robbins 2019
  .venv\\Scripts\\python.exe scripts/label_craters.py moon_ap15_hia_c01 --source "Robbins 2019 DOI:10.1029/2018JE005592 crater_id=123456"

Thao tác trong cửa sổ ảnh:
  - Click 1 (chuột trái): Đặt TÂM hố [0, 511]
  - Click 2 (chuột trái): Đặt điểm trên VÀNH miệng hố → bán kính tự tính (khoảng cách Euclid)
  - Phím U: Đổi trạng thái hố vừa ghi thành UNCERTAIN (chưa chắc chắn) hoặc ngược lại
  - Phím Z: Hoàn tác (nếu đang chọn tâm thì hủy tâm; nếu đã ghi thì xóa hố vừa ghi)
  - Phím S: Lưu file JSON và ảnh overlay kết quả (chỉ đóng cửa sổ khi lưu thành công)
  - Phím Q: Thoát không lưu
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import numpy as np
# pyrefly: ignore [missing-import]
import matplotlib

# Thử nạp TkAgg nếu có hỗ trợ GUI, giữ nguyên backend (ví dụ Agg) trên headless CI
try:
    matplotlib.use("TkAgg")
except Exception:
    pass

# pyrefly: ignore [missing-import]
import matplotlib.pyplot as plt
# pyrefly: ignore [missing-import]
import matplotlib.patches as mpatches

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.contracts import read_json, validate_crater_set, validate_metadata

# Màu sắc hố theo loại nhãn
COLOR_CERTAIN = "#00e5ff"    # Xanh cyan = nhãn chắc chắn
COLOR_UNCERTAIN = "#ff9800"  # Cam = uncertain (chưa chắc chắn)
COLOR_EXISTING = "#b0bec5"   # Xám nhạt = nhãn từ phiên trước
COLOR_TEMP = "#ffffff"       # Trắng = đang chọn tâm

STATE_IDLE = "idle"
STATE_WAIT_EDGE = "wait_edge"  # Đã click tâm, chờ click vành


class LabelApp:
    def __init__(
        self,
        image_id: str,
        source_arg: str = "",
        auto_uncertain: bool = False,
        processed_dir: Path | None = None,
        ref_dir: Path | None = None,
    ):
        self.image_id = image_id
        self.source_arg = source_arg.strip()
        self.auto_uncertain = auto_uncertain

        self.processed_dir = processed_dir or (ROOT / "data" / "processed")
        self.ref_dir = ref_dir or (ROOT / "data" / "reference_labels")
        self.ref_dir.mkdir(parents=True, exist_ok=True)

        meta_path = self.processed_dir / f"{image_id}.json"
        npy_path = self.processed_dir / f"{image_id}.npy"

        if not meta_path.exists():
            raise FileNotFoundError(f"Không tìm thấy metadata tại {meta_path}")
        if not npy_path.exists():
            raise FileNotFoundError(f"Không tìm thấy ảnh .npy tại {npy_path}")

        self.metadata = read_json(meta_path)
        validate_metadata(self.metadata)
        self.scale = float(self.metadata["scale_m_per_px"])
        self.r_min = float(self.metadata["radius"]["r_min_px"])
        self.r_max = float(self.metadata["radius"]["r_max_px"])

        self.img = np.load(npy_path)  # float32 [0,1], 512x512

        # Đường dẫn file lưu
        self.ref_json_path = self.ref_dir / f"{image_id}_craters_catalogue.json"
        self.ref_overlay_path = self.ref_dir / f"{image_id}_overlay.png"
        self.processed_json_path = self.processed_dir / f"{image_id}_craters_catalogue.json"

        # Cấu trúc lưu nhãn: danh sách các item
        # Mỗi item: {"data": dict, "patch": Patch, "text": Annotation, "is_existing": bool}
        self.items: list[dict[str, Any]] = []
        self.state = STATE_IDLE
        self.pending_center: tuple[float, float] | None = None
        self._temp_center_dot: Any = None

        # Nạp nhãn cũ nếu có
        self.existing_ref_source: str | None = None
        self._load_existing_labels()

        # Xác định số thứ tự ID tiếp theo
        self.counter = self._get_next_id_counter()

        self._setup_figure()

    def _load_existing_labels(self):
        """Nạp nhãn cũ từ data/reference_labels/ hoặc data/processed/ nếu có."""
        load_path = None
        if self.ref_json_path.exists():
            load_path = self.ref_json_path
        elif self.processed_json_path.exists():
            load_path = self.processed_json_path

        if load_path:
            try:
                old_data = read_json(load_path)
                self.existing_ref_source = old_data.get("reference_source")
                circles = old_data.get("circles", [])
                for c in circles:
                    is_unc = "_uncertain" in c["crater_id"]
                    self.items.append({
                        "data": {
                            "crater_id": c["crater_id"],
                            "x": float(c["x"]),
                            "y": float(c["y"]),
                            "r": float(c["r"]),
                            "confidence": c.get("confidence"),
                            "votes": c.get("votes"),
                            "_uncertain": is_unc,
                        },
                        "patch": None,
                        "text": None,
                        "is_existing": True,
                    })
                print(f"Đã nạp {len(circles)} nhãn từ {load_path.name}")
            except Exception as e:
                print(f"Cảnh báo: Không thể đọc file nhãn cũ ({e}), bắt đầu mới.")

    def _get_next_id_counter(self) -> int:
        """Tìm số thứ tự C{k} lớn nhất từ các nhãn hiện có để không trùng ID."""
        max_idx = 0
        for it in self.items:
            cid = it["data"]["crater_id"]
            m = re.search(r"C(\d+)", cid)
            if m:
                max_idx = max(max_idx, int(m.group(1)))
        return max_idx + 1

    def _determine_reference_source(self) -> str:
        """Xác định reference_source rõ ràng, không trộn lẫn nguồn mơ hồ."""
        if self.source_arg:
            if self.source_arg.lower().startswith("robbins"):
                return self.source_arg
            return f"manual_label_s110; {self.source_arg}"

        if self.existing_ref_source:
            return self.existing_ref_source

        return "manual_label_s110; visual inspection verified"

    def _setup_figure(self):
        self.fig, self.ax = plt.subplots(figsize=(9, 9))
        self.fig.patch.set_facecolor("#1a1a2e")
        self.ax.set_facecolor("#0f0f23")

        # Quy ước tâm pixel: dùng extent [-0.5, 511.5, 511.5, -0.5] với origin='upper'
        # để pixel [0, 511] có tâm nằm chính xác tại (0,0) -> (511,511).
        self.ax.imshow(
            self.img,
            cmap="gray",
            vmin=0.0,
            vmax=1.0,
            extent=[-0.5, 511.5, 511.5, -0.5],
            origin="upper",
        )

        title = (
            f"S1-10 Ghi nhãn: {self.image_id} (Scale: {self.scale} m/px) | "
            f"r=[{self.r_min:.0f}–{self.r_max:.0f} px]\n"
            "Click 1: Tâm | Click 2: Vành | [U]: Đổi uncertain | [Z]: Hoàn tác | [S]: Lưu | [Q]: Thoát"
        )
        self.ax.set_title(title, color="#e0e0e0", fontsize=9, pad=10)
        self.ax.set_xlabel("x (cột pixel [0, 511])", color="#90caf9", fontsize=8)
        self.ax.set_ylabel("y (hàng pixel [0, 511])", color="#90caf9", fontsize=8)
        self.ax.tick_params(colors="#90caf9")
        for spine in self.ax.spines.values():
            spine.set_edgecolor("#37474f")

        # Hiển thị các nhãn cũ đã nạp
        for it in self.items:
            c = it["data"]
            color = COLOR_UNCERTAIN if c["_uncertain"] else COLOR_EXISTING
            linestyle = "--" if not c["_uncertain"] else ":"
            circle = plt.Circle(
                (c["x"], c["y"]),
                c["r"],
                fill=False,
                color=color,
                linewidth=1.2,
                linestyle=linestyle,
            )
            self.ax.add_patch(circle)
            ann = self.ax.annotate(
                c["crater_id"],
                (c["x"], c["y"] - c["r"] - 4),
                color=color,
                fontsize=7,
                ha="center",
                fontweight="normal",
            )
            it["patch"] = circle
            it["text"] = ann

        # Vòng tròn kích thước tham chiếu ở góc
        self._ref_min = plt.Circle(
            (35, 475), self.r_min, fill=False, color="#4caf50", linewidth=0.8, linestyle=":"
        )
        self._ref_max = plt.Circle(
            (160, 475), self.r_max, fill=False, color="#f44336", linewidth=0.8, linestyle=":"
        )
        self.ax.add_patch(self._ref_min)
        self.ax.add_patch(self._ref_max)
        self.ax.text(
            35, 475, f"r_min\n{self.r_min:.0f}px", color="#4caf50", fontsize=6, ha="center", va="center"
        )
        self.ax.text(
            160, 475, f"r_max\n{self.r_max:.0f}px", color="#f44336", fontsize=6, ha="center", va="center"
        )

        self.ax.set_xlim(-0.5, 511.5)
        self.ax.set_ylim(511.5, -0.5)

        # Thanh trạng thái riêng biệt ở đáy figure (tránh đè lên tiêu đề hay đồ thị)
        self.fig.subplots_adjust(top=0.92, bottom=0.08)
        self._status_text = self.fig.text(
            0.5,
            0.02,
            f"Trạng thái: Sẵn sàng ({len(self.items)} nhãn). Click chuột trái để đặt TÂM hố.",
            color="#ffeb3b",
            fontsize=8.5,
            ha="center",
            va="bottom",
            backgroundcolor="#212121",
        )

        legend_elements = [
            mpatches.Patch(facecolor="none", edgecolor=COLOR_CERTAIN, label="Nhãn mới chắc chắn"),
            mpatches.Patch(facecolor="none", edgecolor=COLOR_UNCERTAIN, label="Nhãn uncertain"),
            mpatches.Patch(
                facecolor="none", edgecolor=COLOR_EXISTING, linestyle="--", label="Nhãn cũ đã nạp"
            ),
        ]
        self.ax.legend(
            handles=legend_elements,
            loc="upper right",
            facecolor="#263238",
            edgecolor="#455a64",
            labelcolor="#e0e0e0",
            fontsize=7,
        )

        self.fig.canvas.mpl_connect("button_press_event", self._on_click)
        self.fig.canvas.mpl_connect("key_press_event", self._on_key)

    def _set_status(self, msg: str):
        self._status_text.set_text(f"Trạng thái: {msg}")
        self.fig.canvas.draw_idle()

    def _on_click(self, event):
        if event.inaxes != self.ax or event.button != 1:
            return
        x, y = event.xdata, event.ydata
        if x is None or y is None:
            return

        # Kiểm tra giới hạn tọa độ [0, 511]
        if not (0.0 <= x <= 511.0 and 0.0 <= y <= 511.0):
            self._set_status(f"Tọa độ ({x:.1f}, {y:.1f}) ngoài phạm vi ảnh [0, 511]! Vui lòng click trong ảnh.")
            return

        if self.state == STATE_IDLE:
            # Click 1: Đặt tâm hố
            self.pending_center = (x, y)
            self.state = STATE_WAIT_EDGE

            if self._temp_center_dot:
                self._temp_center_dot.remove()
            self._temp_center_dot, = self.ax.plot(
                x, y, "+", color=COLOR_TEMP, markersize=12, linewidth=1.8
            )

            self._set_status(
                f"Đã chọn tâm: ({x:.1f}, {y:.1f}) — Bây giờ click lên VÀNH miệng hố (hoặc ấn Z để hủy)."
            )
            self.fig.canvas.draw_idle()

        elif self.state == STATE_WAIT_EDGE:
            # Click 2: Đặt vành miệng hố
            cx, cy = self.pending_center
            r = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)

            if r < 1.0:
                self._set_status(f"Bán kính r={r:.1f}px quá nhỏ! Click lại lên vành miệng hố.")
                return

            cid = f"C{self.counter}"
            if self.auto_uncertain:
                cid += "_uncertain"

            color = COLOR_UNCERTAIN if self.auto_uncertain else COLOR_CERTAIN
            circle = plt.Circle((cx, cy), r, fill=False, color=color, linewidth=1.5)
            self.ax.add_patch(circle)

            ann = self.ax.annotate(
                cid,
                (cx, cy - r - 4),
                color=color,
                fontsize=7.5,
                ha="center",
                fontweight="bold",
            )

            # Cảnh báo dải bán kính
            warn = ""
            if r < self.r_min:
                warn = f" [⚠ r={r:.1f} < r_min={self.r_min:.0f}]"
            elif r > self.r_max:
                warn = f" [⚠ r={r:.1f} > r_max={self.r_max:.0f}]"

            d_m = 2 * r * self.scale
            item = {
                "data": {
                    "crater_id": cid,
                    "x": round(cx, 2),
                    "y": round(cy, 2),
                    "r": round(r, 2),
                    "confidence": None,
                    "votes": None,
                    "_uncertain": self.auto_uncertain,
                },
                "patch": circle,
                "text": ann,
                "is_existing": False,
            }
            self.items.append(item)
            self.counter += 1

            if self._temp_center_dot:
                self._temp_center_dot.remove()
                self._temp_center_dot = None

            self.pending_center = None
            self.state = STATE_IDLE

            status = f"Đã ghi {cid}: tâm=({cx:.1f},{cy:.1f}), r={r:.1f}px, D≈{d_m:.0f}m{warn} | Tổng: {len(self.items)}"
            self._set_status(status)
            print(f"[Nhãn mới] {status}")
            self.fig.canvas.draw_idle()

    def _on_key(self, event):
        if event.key in ("u", "U"):
            # Chuyển đổi trạng thái uncertain của hố gần nhất
            if not self.items:
                self._set_status("Chưa có hố nào để đổi trạng thái uncertain.")
                return

            last = self.items[-1]
            c = last["data"]
            patch = last["patch"]
            ann = last["text"]

            if not c["_uncertain"]:
                # Chuyển sang uncertain
                c["_uncertain"] = True
                if not c["crater_id"].endswith("_uncertain"):
                    c["crater_id"] += "_uncertain"
                if patch:
                    patch.set_edgecolor(COLOR_UNCERTAIN)
                if ann:
                    ann.set_color(COLOR_UNCERTAIN)
                    ann.set_text(c["crater_id"])
                msg = f"Đã chuyển {c['crater_id']} sang UNCERTAIN (màu cam)."
            else:
                # Bỏ uncertain
                c["_uncertain"] = False
                c["crater_id"] = c["crater_id"].replace("_uncertain", "")
                target_color = COLOR_EXISTING if last["is_existing"] else COLOR_CERTAIN
                if patch:
                    patch.set_edgecolor(target_color)
                if ann:
                    ann.set_color(target_color)
                    ann.set_text(c["crater_id"])
                msg = f"Đã chuyển {c['crater_id']} thành CHẮC CHẮN."

            self._set_status(msg)
            print(f"[Đổi trạng thái] {msg}")
            self.fig.canvas.draw_idle()

        elif event.key in ("z", "Z"):
            # ƯU TIÊN 1: Nếu đang chờ click vành, chỉ hủy điểm tâm tạm
            if self.state == STATE_WAIT_EDGE:
                if self._temp_center_dot:
                    self._temp_center_dot.remove()
                    self._temp_center_dot = None
                self.pending_center = None
                self.state = STATE_IDLE
                self._set_status("Đã hủy click tâm đang chờ. Bạn có thể chọn lại tâm mới.")
                self.fig.canvas.draw_idle()
                return

            # ƯU TIÊN 2: Xóa hố gần nhất đã ghi
            if self.items:
                removed_item = self.items.pop()
                cid = removed_item["data"]["crater_id"]
                if removed_item["patch"]:
                    removed_item["patch"].remove()
                if removed_item["text"]:
                    removed_item["text"].remove()

                # Cập nhật lại counter nếu vừa xóa nhãn mới C{k}
                self.counter = self._get_next_id_counter()

                self._set_status(f"Đã hoàn tác (xóa) {cid}. Còn lại: {len(self.items)} nhãn.")
                print(f"[Hoàn tác] Đã xóa {cid}. Còn lại {len(self.items)} nhãn.")
                self.fig.canvas.draw_idle()
            else:
                self._set_status("Không còn nhãn nào để hoàn tác.")

        elif event.key in ("s", "S"):
            # Lưu file và chỉ đóng khi thành công
            success = self._save()
            if success:
                print("Lưu thành công! Đang đóng cửa sổ...")
                plt.close(self.fig)
            else:
                self._set_status("LƯU THẤT BẠI! Kiểm tra lỗi terminal và chỉnh lại nhãn trước khi thoát.")

        elif event.key in ("q", "Q"):
            print("Thoát không lưu các thay đổi chưa lưu.")
            plt.close(self.fig)

    def _save(self) -> bool:
        """Thực hiện validate và lưu JSON + ảnh overlay. Trả về True nếu thành công."""
        if not self.items:
            print("Cảnh báo: Không có nhãn nào trong danh sách.")
            self._set_status("Không có nhãn nào để lưu! Hãy chấm ít nhất 1 hố.")
            return False

        # Chuẩn bị danh sách circles theo schema
        clean_circles = []
        for it in self.items:
            c = it["data"]
            clean_circles.append({
                "crater_id": c["crater_id"],
                "x": round(float(c["x"]), 2),
                "y": round(float(c["y"]), 2),
                "r": round(float(c["r"]), 2),
                "confidence": c.get("confidence"),
                "votes": c.get("votes"),
            })

        ref_src = self._determine_reference_source()
        crater_set = {
            "schema_version": "1.0",
            "data_kind": self.metadata["data_kind"],
            "image_id": self.image_id,
            "source": "catalogue",
            "reference_source": ref_src,
            "circles": clean_circles,
        }

        # Kiểm tra hợp đồng dữ liệu nghiêm ngặt
        try:
            validate_crater_set(crater_set, self.metadata)
        except Exception as e:
            print("\n" + "=" * 60)
            print(f"LỖI HỢP ĐỒNG DỮ LIỆU (validate_crater_set): {e}")
            print("Dữ liệu KHÔNG được ghi vào đĩa. Cửa sổ KHÔNG đóng.")
            print("Hãy bấm 'Z' để hủy nhãn vi phạm hoặc kiểm tra lại tọa độ.")
            print("=" * 60 + "\n")
            return False

        # 1. Lưu file JSON vào cả data/reference_labels/ (Git theo dõi) và data/processed/
        json_content = json.dumps(crater_set, ensure_ascii=False, indent=2) + "\n"
        self.ref_json_path.write_text(json_content, encoding="utf-8")
        self.processed_json_path.write_text(json_content, encoding="utf-8")

        # 2. Tự động lưu ảnh overlay PNG phục vụ kiểm tra chéo
        try:
            # Ẩn thanh trạng thái tạm thời khi xuất ảnh
            self._status_text.set_text(f"Đã xác minh {len(clean_circles)} hố | Nguồn: {ref_src}")
            self.fig.savefig(self.ref_overlay_path, dpi=150, facecolor=self.fig.get_facecolor())
            print(f"Đã lưu ảnh overlay minh chứng: {self.ref_overlay_path.name}")
        except Exception as e:
            print(f"Cảnh báo: Không thể lưu ảnh overlay ({e})")

        print("\n" + "─" * 60)
        print(f"LƯU THÀNH CÔNG: {len(clean_circles)} nhãn hố")
        print(f"  → JSON tham chiếu (Git): {self.ref_json_path}")
        print(f"  → JSON bộ đệm cục bộ:   {self.processed_json_path}")
        print(f"  → Nguồn reference:       {ref_src}")
        print("Danh sách hố đã xác nhận:")
        for c in clean_circles:
            d_m = 2 * c["r"] * self.scale
            unc = " [uncertain]" if "_uncertain" in c["crater_id"] else ""
            print(f"  {c['crater_id']:25s} | Tâm=({c['x']:6.1f}, {c['y']:6.1f}) | r={c['r']:5.1f}px | D≈{d_m:6.0f}m{unc}")
        print("─" * 60 + "\n")
        return True

    def run(self):
        print(f"\n=== S1-10 Ghi nhãn hố tham chiếu: {self.image_id} ===")
        print(f"Scale: {self.scale} m/px | Dải tìm kiếm: r=[{self.r_min:.0f}–{self.r_max:.0f}] px")
        print(f"Nguồn: {self._determine_reference_source()}")
        print(f"Đang có sẵn: {len(self.items)} nhãn trong bộ nhớ")
        print("─" * 60)
        print("Thao tác:")
        print("  Click 1: Tâm hố  |  Click 2: Vành miệng hố")
        print("  [U]: Đổi uncertain  |  [Z]: Hoàn tác  |  [S]: Lưu  |  [Q]: Thoát")
        print("─" * 60)
        plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="S1-10: Ghi nhãn hố tham chiếu thủ công và chuẩn hóa nhãn"
    )
    parser.add_argument(
        "image_id",
        nargs="?",
        default="moon_ap16_m106777343r_c01",
        help="image_id cần ghi nhãn (mặc định: moon_ap16_m106777343r_c01 — ảnh demo S1-10)",
    )
    parser.add_argument(
        "--source",
        default="",
        help="Ghi chú nguồn nhãn (ví dụ: 'Robbins 2019 DOI:10.1029/2018JE005592 crater_id=12345' hoặc 'visual inspection')",
    )
    parser.add_argument(
        "--uncertain",
        action="store_true",
        help="Tự động gán cờ uncertain cho tất cả các nhãn ghi mới trong phiên này",
    )
    args = parser.parse_args()

    processed = ROOT / "data" / "processed"
    if not (processed / f"{args.image_id}.json").exists():
        available = sorted(
            p.stem for p in processed.glob("*.json")
            if not p.stem.endswith("_craters_catalogue")
        )
        print(f"Lỗi: Không tìm thấy image_id: '{args.image_id}'")
        print("Các image_id có sẵn:")
        for iid in available:
            print(f"  {iid}")
        sys.exit(1)

    app = LabelApp(args.image_id, args.source, args.uncertain)
    app.run()


if __name__ == "__main__":
    main()
