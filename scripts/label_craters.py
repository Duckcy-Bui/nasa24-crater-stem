"""S1-10 — Công cụ ghi nhãn hố tham chiếu thủ công.

Cách dùng:
  python scripts/label_craters.py <image_id> [--source <ghi_chú>] [--uncertain]

Ví dụ:
  python scripts/label_craters.py moon_ap16_m106777343r_c01
  python scripts/label_craters.py moon_ap15_hia_c01 --source "Robbins 2019 ID=123456"

Thao tác trong cửa sổ ảnh:
  - Click 1 (chuột trái): Đặt TÂM hố
  - Click 2 (chuột trái): Đặt điểm trên VÀNH miệng hố → bán kính tự tính
  - Phím U: đánh dấu hố vừa ghi là UNCERTAIN (chưa chắc chắn)
  - Phím Z: hoàn tác hố vừa ghi
  - Phím S: lưu file craters_catalogue.json và thoát
  - Phím Q: thoát không lưu

Quy tắc nhãn (theo S1-10):
  - Nhãn thủ công: đặt reference_source = "manual_label_s110; <ghi_chú>"; không gán Robbins.
  - Nhãn từ Robbins: ghi rõ DOI và crater_id Robbins; chỉ dùng cho hố > 1 km.
  - Hố uncertain: confidence = null, ghi rõ vào source_note trong crater_id (ví dụ "C3_uncertain").
  - Không gán nhãn Robbins cho hố chưa đối chiếu tọa độ pixel thực tế.
"""

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
# pyrefly: ignore [missing-import]
import matplotlib
matplotlib.use("TkAgg")
# pyrefly: ignore [missing-import]
import matplotlib.pyplot as plt
# pyrefly: ignore [missing-import]
import matplotlib.patches as mpatches

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.contracts import read_json, validate_crater_set, validate_metadata

# Màu sắc hố theo loại nhãn
COLOR_CERTAIN = "#00e5ff"   # xanh cyan = nhãn chắc chắn
COLOR_UNCERTAIN = "#ff9800" # cam = uncertain
COLOR_TEMP = "#ffffff"      # trắng = đang vẽ (chưa xác nhận)

STATE_IDLE = "idle"
STATE_WAIT_EDGE = "wait_edge"  # đã click tâm, chờ click vành


class LabelApp:
    def __init__(self, image_id: str, source_note: str, auto_uncertain: bool):
        self.image_id = image_id
        self.source_note = source_note
        self.auto_uncertain = auto_uncertain

        processed = ROOT / "data" / "processed"
        meta_path = processed / f"{image_id}.json"
        npy_path = processed / f"{image_id}.npy"

        if not meta_path.exists():
            print(f"Không tìm thấy: {meta_path}")
            sys.exit(1)
        if not npy_path.exists():
            print(f"Không tìm thấy: {npy_path}")
            sys.exit(1)

        self.metadata = read_json(meta_path)
        validate_metadata(self.metadata)
        self.scale = self.metadata["scale_m_per_px"]

        self.img = np.load(npy_path)  # float32 [0,1], 512x512
        self.output_path = processed / f"{image_id}_craters_catalogue.json"

        # Trạng thái ghi nhãn
        self.circles: list[dict] = []     # nhãn đã xác nhận
        self.state = STATE_IDLE
        self.pending_center: tuple[float, float] | None = None  # (x, y) đang chờ vành
        self.counter = 1

        # Nạp nhãn cũ nếu có (không ghi đè, chỉ hiển thị)
        self.existing_circles: list[dict] = []
        if self.output_path.exists():
            old = read_json(self.output_path)
            self.existing_circles = old.get("circles", [])
            print(f"Tải nhãn cũ: {len(self.existing_circles)} hố từ {self.output_path.name}")

        self._setup_figure()

    def _setup_figure(self):
        self.fig, self.ax = plt.subplots(figsize=(9, 9))
        self.fig.patch.set_facecolor("#1a1a2e")
        self.ax.set_facecolor("#0f0f23")

        self.ax.imshow(self.img, cmap="gray", vmin=0, vmax=1,
                       extent=[0, 512, 512, 0], origin="upper")

        title = (
            f"S1-10 Ghi nhãn: {self.image_id}\n"
            f"Scale={self.scale} m/px | "
            f"D=[{self.metadata['radius']['d_min_m']:.0f}–{self.metadata['radius']['d_max_m']:.0f} m] | "
            f"r=[{self.metadata['radius']['r_min_px']}–{self.metadata['radius']['r_max_px']} px]\n"
            "Click 1=tâm  Click 2=vành  [U]=uncertain  [Z]=hoàn tác  [S]=lưu  [Q]=thoát"
        )
        self.ax.set_title(title, color="#e0e0e0", fontsize=8.5, pad=6)
        self.ax.set_xlabel("x (cột pixel)", color="#90caf9")
        self.ax.set_ylabel("y (hàng pixel)", color="#90caf9")
        self.ax.tick_params(colors="#90caf9")
        for spine in self.ax.spines.values():
            spine.set_edgecolor("#37474f")

        # Hiển thị nhãn cũ màu xám
        for c in self.existing_circles:
            circle = plt.Circle((c["x"], c["y"]), c["r"],
                                 fill=False, color="#757575", linewidth=1, linestyle="--")
            self.ax.add_patch(circle)
            self.ax.annotate(c["crater_id"], (c["x"], c["y"] - c["r"] - 4),
                              color="#757575", fontsize=6, ha="center")

        # Trục reference
        r_min = self.metadata["radius"]["r_min_px"]
        r_max = self.metadata["radius"]["r_max_px"]
        self._ref_min = plt.Circle((40, 472), r_min, fill=False,
                                    color="#4caf50", linewidth=0.8, linestyle=":")
        self._ref_max = plt.Circle((180, 472), r_max, fill=False,
                                    color="#f44336", linewidth=0.8, linestyle=":")
        self.ax.add_patch(self._ref_min)
        self.ax.add_patch(self._ref_max)
        self.ax.text(40, 472, f"r_min\n{r_min}px", color="#4caf50", fontsize=5.5, ha="center", va="center")
        self.ax.text(180, 472, f"r_max\n{r_max}px", color="#f44336", fontsize=5.5, ha="center", va="center")

        self._temp_center_dot = None
        self._temp_circle = None
        self._status_text = self.ax.text(
            256, -22, "Trạng thái: Click chuột trái để đặt TÂM hố.",
            color="#ffeb3b", fontsize=8, ha="center", va="center",
            transform=self.ax.transData,
        )
        self.ax.set_xlim(0, 512)
        self.ax.set_ylim(512, 0)

        self.fig.canvas.mpl_connect("button_press_event", self._on_click)
        self.fig.canvas.mpl_connect("key_press_event", self._on_key)

        legend_elements = [
            mpatches.Patch(facecolor="none", edgecolor=COLOR_CERTAIN, label="Nhãn chắc chắn"),
            mpatches.Patch(facecolor="none", edgecolor=COLOR_UNCERTAIN, label="Nhãn uncertain"),
            mpatches.Patch(facecolor="none", edgecolor="#757575", linestyle="--", label="Nhãn cũ (đã lưu)"),
        ]
        self.ax.legend(handles=legend_elements, loc="upper right",
                       facecolor="#263238", edgecolor="#455a64",
                       labelcolor="#e0e0e0", fontsize=7)
        plt.tight_layout()

    def _set_status(self, msg: str):
        self._status_text.set_text(f"Trạng thái: {msg}")
        self.fig.canvas.draw_idle()

    def _on_click(self, event):
        if event.inaxes != self.ax or event.button != 1:
            return
        x, y = event.xdata, event.ydata
        if x is None or y is None:
            return

        if self.state == STATE_IDLE:
            # Click 1: đặt tâm
            self.pending_center = (x, y)
            self.state = STATE_WAIT_EDGE

            # Hiển thị chấm tâm tạm thời
            if self._temp_center_dot:
                self._temp_center_dot.remove()
            self._temp_center_dot, = self.ax.plot(x, y, "+", color=COLOR_TEMP, markersize=10, linewidth=1.5)

            self._set_status(f"Tâm: ({x:.1f}, {y:.1f}) — Bây giờ click lên VÀNH miệng hố để đo bán kính.")
            self.fig.canvas.draw_idle()

        elif self.state == STATE_WAIT_EDGE:
            # Click 2: đặt vành
            cx, cy = self.pending_center
            r = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            r_min = self.metadata["radius"]["r_min_px"]
            r_max = self.metadata["radius"]["r_max_px"]

            if r < 1.0:
                self._set_status(f"Bán kính quá nhỏ ({r:.1f} px). Click lại vào vành.")
                return

            # Vẽ vòng tròn xác nhận
            color = COLOR_UNCERTAIN if self.auto_uncertain else COLOR_CERTAIN
            circle = plt.Circle((cx, cy), r, fill=False, color=color, linewidth=1.5)
            self.ax.add_patch(circle)

            cid = f"C{self.counter}"
            if self.auto_uncertain:
                cid += "_uncertain"
            self.ax.annotate(cid, (cx, cy - r - 5),
                             color=color, fontsize=7, ha="center", fontweight="bold")

            # Cảnh báo nếu r ngoài dải
            warn = ""
            if r < r_min:
                warn = f" ⚠ r={r:.1f} < r_min={r_min}"
            elif r > r_max:
                warn = f" ⚠ r={r:.1f} > r_max={r_max}"

            d_m = 2 * r * self.scale
            self.circles.append({
                "crater_id": cid,
                "x": round(cx, 2),
                "y": round(cy, 2),
                "r": round(r, 2),
                "confidence": None,
                "votes": None,
                "_uncertain": self.auto_uncertain,
            })

            self.counter += 1

            # Dọn temp
            if self._temp_center_dot:
                self._temp_center_dot.remove()
                self._temp_center_dot = None

            self.pending_center = None
            self.state = STATE_IDLE

            status = f"Đã ghi {cid}: tâm=({cx:.1f},{cy:.1f}) r={r:.1f}px D≈{d_m:.0f}m{warn} | Tổng: {len(self.circles)}"
            self._set_status(status)
            print(status)
            self.fig.canvas.draw_idle()

    def _on_key(self, event):
        if event.key in ("u", "U"):
            # Đánh dấu hố cuối là uncertain
            if self.circles:
                last = self.circles[-1]
                if not last["_uncertain"]:
                    last["_uncertain"] = True
                    old_id = last["crater_id"]
                    if not old_id.endswith("_uncertain"):
                        last["crater_id"] = old_id + "_uncertain"
                    self._set_status(f"Đã đánh dấu {last['crater_id']} là uncertain.")
                    # Vẽ lại hố cuối màu cam (đơn giản nhất)
                    self.fig.canvas.draw_idle()
                else:
                    self._set_status("Hố này đã là uncertain rồi.")
            else:
                self._set_status("Chưa có hố nào để đánh dấu.")

        elif event.key in ("z", "Z"):
            # Hoàn tác hố cuối
            if self.circles:
                removed = self.circles.pop()
                # Xóa circle và text cuối khỏi axes
                patches = self.ax.patches
                if len(patches) > 3:  # 3 = ref_min, ref_max, existing old
                    patches[-1].remove()
                texts = [a for a in self.ax.texts if a != self._status_text]
                if texts:
                    texts[-1].remove()
                self.counter -= 1
                self._set_status(f"Đã hoàn tác: {removed['crater_id']}. Còn {len(self.circles)} nhãn.")
            elif self.state == STATE_WAIT_EDGE:
                # Hủy click tâm đang chờ
                if self._temp_center_dot:
                    self._temp_center_dot.remove()
                    self._temp_center_dot = None
                self.pending_center = None
                self.state = STATE_IDLE
                self._set_status("Đã hủy click tâm. Bắt đầu lại.")
            else:
                self._set_status("Không có gì để hoàn tác.")
            self.fig.canvas.draw_idle()

        elif event.key in ("s", "S"):
            self._save()
            plt.close(self.fig)

        elif event.key in ("q", "Q"):
            print("Thoát không lưu.")
            plt.close(self.fig)

    def _save(self):
        if not self.circles:
            print("Không có nhãn nào để lưu.")
            return

        # Lọc trường nội bộ _uncertain trước khi lưu
        clean_circles = []
        for c in self.circles:
            entry = {
                "crater_id": c["crater_id"],
                "x": c["x"],
                "y": c["y"],
                "r": c["r"],
                "confidence": c["confidence"],
                "votes": c["votes"],
            }
            clean_circles.append(entry)

        # Xác định reference_source
        ref_src = f"manual_label_s110"
        if self.source_note:
            ref_src += f"; {self.source_note}"

        crater_set = {
            "schema_version": "1.0",
            "data_kind": self.metadata["data_kind"],
            "image_id": self.image_id,
            "source": "catalogue",
            "reference_source": ref_src,
            "circles": clean_circles,
        }

        try:
            validate_crater_set(crater_set, self.metadata)
        except Exception as e:
            print(f"LỖI HỢP ĐỒNG DỮ LIỆU: {e}")
            print("Dữ liệu KHÔNG được lưu. Kiểm tra lại các nhãn.")
            return

        self.output_path.write_text(
            json.dumps(crater_set, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8"
        )
        print(f"\nĐã lưu {len(clean_circles)} nhãn -> {self.output_path.name}")
        for c in clean_circles:
            d_m = 2 * c["r"] * self.scale
            uncertain_flag = " [uncertain]" if "_uncertain" in c["crater_id"] else ""
            print(f"  {c['crater_id']:30s} | ({c['x']:6.1f}, {c['y']:6.1f}) | r={c['r']:5.1f}px | D≈{d_m:7.0f}m{uncertain_flag}")

    def run(self):
        print(f"\n=== S1-10 Ghi nhãn hố: {self.image_id} ===")
        print(f"Scale: {self.scale} m/px")
        print(f"Dải tìm kiếm: r=[{self.metadata['radius']['r_min_px']}–{self.metadata['radius']['r_max_px']}] px")
        print(f"Nguồn nhãn: {self.source_note or 'manual_label_s110'}")
        print("─" * 50)
        print("Click 1 = tâm hố  |  Click 2 = vành miệng hố")
        print("[U] = uncertain  |  [Z] = hoàn tác  |  [S] = lưu  |  [Q] = thoát")
        print("─" * 50)
        plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="S1-10: Ghi nhãn hố tham chiếu thủ công"
    )
    parser.add_argument(
        "image_id",
        nargs="?",
        default="moon_ap16_m106777343r_c01",
        help="image_id của ảnh cần ghi nhãn (mặc định: moon_ap16_m106777343r_c01 — ảnh demo S1-10)",
    )
    parser.add_argument(
        "--source",
        default="",
        help="Ghi chú nguồn nhãn (ví dụ: 'Robbins 2019 ID=123456' hoặc 'manual visual inspection')",
    )
    parser.add_argument(
        "--uncertain",
        action="store_true",
        help="Tự động đánh dấu tất cả hố ghi vào phiên này là uncertain",
    )
    args = parser.parse_args()

    # Kiểm tra ảnh tồn tại
    processed = ROOT / "data" / "processed"
    if not (processed / f"{args.image_id}.json").exists():
        available = sorted(p.stem for p in processed.glob("*.json")
                           if not p.stem.endswith("_craters_catalogue"))
        print(f"Không tìm thấy image_id: '{args.image_id}'")
        print("Các image_id có sẵn:")
        for iid in available:
            print(f"  {iid}")
        sys.exit(1)

    app = LabelApp(args.image_id, args.source, args.uncertain)
    app.run()


if __name__ == "__main__":
    main()
