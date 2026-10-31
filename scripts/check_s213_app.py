"""Kiểm S2-13/S3-04 bằng Chromium thật; Streamlit phải chạy sẵn ở cổng 8621.

Môi trường: requirements-browser.txt và Chromium; --out phải chưa tồn tại.
--layout-only kiểm riêng lỗi #9, dùng cả khi đối chứng CSS trước sửa.
Các vòng ở đây chỉ là dữ liệu thử tương tác, không phải nhãn hố thật.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCORE_LABEL = "Điểm theo nhãn đã kiểm chéo"


def run_identity(url):
    paths = ("app.py", "src/integration.py", "src/statistics.py", "src/hough.py", "src/pipeline.py",
             "src/crater_canvas/geometry.js", "src/crater_canvas/canvas.js", "src/crater_canvas/app.css",
             "configs/default.json", "docs/evidence/s2-09/so_sanh.json", "data/s209_counts/regions.json",
             "scripts/check_s213_app.py", "requirements-browser.txt", "requirements-test.txt")
    return {"head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "url": url, "source_root": str(ROOT), "started_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_status": subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True),
            "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths},
            "server_source_verified": False}


def check_score_label(page, width, out, narrow=False):
    from playwright.sync_api import expect

    page.set_viewport_size({"width": width, "height": 1100})
    label = page.locator('[data-testid="stMetricLabel"] p').filter(has_text=SCORE_LABEL)
    expect(label).to_have_text(SCORE_LABEL)
    if narrow:
        # Reproduce a narrow metric column independently of the host's installed font.
        label.evaluate("""e => {const m=e.closest('[data-testid="stMetric"]');
          m.dataset.testStyle=m.getAttribute('style') || '';
          m.style.width='128px'; m.style.maxWidth='128px'; m.style.minWidth='0';} """)
    label.scroll_into_view_if_needed()
    measured = label.evaluate("""e => {
      const range = document.createRange(); range.selectNodeContents(e);
      const lines = [...range.getClientRects()].filter(r => r.width > 0);
      const clips = [];
      for (let p=e.parentElement; p; p=p.parentElement) {
        const s=getComputedStyle(p);
        if (['hidden','clip'].includes(s.overflowX) || ['hidden','clip'].includes(s.overflowY)) {
          const r=p.getBoundingClientRect();
          clips.push({left:r.left,right:r.right,top:r.top,bottom:r.bottom});
        }
      }
      const metric=e.closest('[data-testid="stMetric"]').getBoundingClientRect();
      const visible=lines.every(r => r.left>=metric.left-1 && r.right<=metric.right+1
        && clips.every(c => r.left>=c.left-1 && r.right<=c.right+1
        && r.top>=c.top-1 && r.bottom<=c.bottom+1));
      return {text:e.textContent,white_space:getComputedStyle(e).whiteSpace,visible,
        lines:lines.map(r=>({x:r.x,y:r.y,width:r.width,height:r.height})),clips};
    }""")
    if narrow:
        page.screenshot(path=str(out / "score_1440_narrow.png"))
        label.evaluate("""e => {const m=e.closest('[data-testid="stMetric"]');
          m.setAttribute('style',m.dataset.testStyle); delete m.dataset.testStyle;} """)
    assert measured["visible"], f"Nhãn bị cắt ở {width}px (narrow={narrow}): {measured}"
    return {"width": width, "narrow_metric": narrow, **measured}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8621")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--layout-only", action="store_true")
    args = parser.parse_args()
    try:
        args.out.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        parser.error("--out phải là thư mục chưa tồn tại; không ghi đè minh chứng.")
    identity = run_identity(args.url)
    (args.out / "run_identity.json").write_text(json.dumps(identity, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    from playwright.sync_api import expect, sync_playwright

    evidence = json.loads((ROOT / "docs/evidence/s2-09/so_sanh.json").read_text(encoding="utf-8"))
    results = {**identity, "navigation": "reload before each image",
               "scope": {"score_label": "text bounds at 1440/390px and a synthetic 128px metric",
                         "manual_table": "names, counts, areas, densities and displayed conclusion",
                         "flow": "candidate count, hidden density, one cap message and no Streamlit exception",
                         "recorded_only": "flow table counts and page text; CI, ratio and p are not asserted",
                         "radius": "displayed centre and radius after dragging the left rim"}}
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1100})
        page.set_default_timeout(30000)
        page.on("pageerror", lambda error: errors.append(str(error)))

        def capture(name, locator):
            locator.scroll_into_view_if_needed()
            page.screenshot(path=str(args.out / name))

        def choose(image_id):
            # Use a fresh page for each screenshot; image-switch state is covered by AppTest.
            page.reload()
            page.get_by_role("combobox", name="Chọn ảnh để mở").wait_for()
            expect(page.frame_locator('iframe[title="app.crater_player_canvas"]').locator("#downloadAnswer")).to_be_enabled()
            expect(page.locator('[data-testid="stApp"]')).to_have_attribute("data-test-script-state", "notRunning")
            picker = page.get_by_role("combobox", name="Chọn ảnh để mở")
            picker.click()
            picker.fill(image_id)
            expect(page.get_by_role("option", name=re.compile(r"^" + re.escape(image_id) + r" ·"))).to_be_visible()
            picker.press("ArrowDown")
            picker.press("Enter")
            expect(picker).to_have_value(re.compile(r"^" + re.escape(image_id) + r" ·"))
            container = page.locator(f".st-key-player_canvas_{image_id}")
            expect(container).to_have_attribute("data-stale", "false")
            frame = container.frame_locator('iframe[title="app.crater_player_canvas"]')
            expect(frame.locator("#imageMeta")).to_contain_text("m/px")
            expect(frame.locator("#downloadAnswer")).to_be_enabled()
            expect(page.locator('[data-testid="stApp"]')).to_have_attribute("data-test-script-state", "notRunning")
            return frame

        def score():
            page.get_by_role("button", name="Chấm bài", exact=True).click()
            page.locator('[data-testid="stMetricLabel"] p').filter(has_text=SCORE_LABEL).wait_for(timeout=90000)
            expect(page.locator('[data-testid="stApp"]')).to_have_attribute("data-test-script-state", "notRunning", timeout=90000)

        def check_cap_messages():
            captions = page.locator('[data-testid="stCaptionContainer"]').all_inner_texts()
            warnings = page.locator('[data-testid="stAlertContentWarning"]').all_inner_texts()
            claims = [text for text in captions + warnings
                      if any(term in text for term in ("chạm trần", "chạm giới hạn", "max_circles"))]
            assert len(claims) == 1 and claims[0] in warnings, captions + warnings
            return {"captions": captions, "warnings": warnings, "cap_claims": claims}

        try:
            page.goto(args.url)
            page.get_by_role("combobox").wait_for()
            score()
            results["score_label"] = []
            results["score_label"].append(check_score_label(page, 1440, args.out, narrow=True))
            print("PASS #9: nhãn xuống dòng đủ chữ trong cột thử hẹp 128px ở viewport 1440px", flush=True)
            for width in (1440, 390):
                measured = check_score_label(page, width, args.out)
                results["score_label"].append(measured)
                capture(f"score_{width}.png", page.get_by_text(SCORE_LABEL, exact=True))
                print(f"PASS #9: nhãn đủ chữ ở {width}px", flush=True)
            if not args.layout_only:
                page.set_viewport_size({"width": 1440, "height": 1100})
                warning = page.get_by_text(re.compile("Máy đã chạm giới hạn max_circles"))
                expect(warning).to_contain_text("không dùng để so tuổi hay so vùng")
                density = page.locator('[data-testid="stMetric"]').filter(
                    has=page.get_by_text("Mật độ", exact=True))
                expect(density.locator('[data-testid="stMetricValue"]')).to_have_text("—")
                capture("density_cap_20m.png", warning)
                results["density_cap"] = {"image_id": "moon_ap15_hia_c01", "scale_m_per_px": 20,
                                          "warning": warning.inner_text(), "density": "—",
                                          **check_cap_messages()}
                print("PASS #10: ẩn mật độ và chỉ một thông báo chạm giới hạn trên ảnh 20 m/px", flush=True)

                heading = page.get_by_text("So sánh mật độ hai vùng · đếm tay", exact=True)
                for key in ("lunokhod1", "marefrig"):
                    image_id = evidence["regions"][key]["crops"][0]
                    choose(image_id)
                    expect(heading).to_be_visible()
                    table = page.locator('[data-testid="stTable"]')
                    text = table.inner_text()
                    for region in evidence["regions"].values():
                        for value in (region["name"], str(region["n"]), f"{region['area_km2']:.1f}",
                                      f"{region['density_per_km2']:.3f}"):
                            assert value in text, (image_id, value, text)
                    expect(page.get_by_text("Chưa có khác biệt có ý nghĩa thống kê về tổng mật độ. "
                                            "Không kết luận được vùng nào cổ hơn.", exact=True)).to_be_visible()
                    capture(f"manual_{key}.png", heading)
                    results[key] = {"image_id": image_id, "table": text}
                    print(f"PASS #11: tên, số hố, diện tích, mật độ và câu kết luận trên {image_id}", flush=True)
                choose("moon_marefrig_loc_c01")
                expect(page.get_by_text(re.compile("Ảnh đang mở cùng ảnh nguồn"))).to_be_visible()
                capture("manual_marefrig_uncounted.png", heading)
                results["uncounted_crop"] = "PASS: c01 cùng nguồn, có lời giải thích không thuộc ô đếm"

                results["flow"] = []
                for image_id in ("moon_ap15_hia_c01", "moon_ap16_m109134835l_c01",
                                 "moon_ap16_m132732855l_c01", "moon_lunokhod1_loc_c01",
                                 "moon_lunokhod2_loc_c02", "moon_marefrig_loc_c02",
                                 "moon_vandegraff_hia_c01"):
                    choose(image_id)
                    score()
                    expect(warning).to_contain_text("không dùng để so tuổi hay so vùng")
                    metrics = page.locator('[data-testid="stMetric"]').evaluate_all("""els => els.map(e => ({
                      label:e.querySelector('[data-testid="stMetricLabel"]').textContent,
                      value:e.querySelector('[data-testid="stMetricValue"]').textContent}))""")
                    assert next(m["value"] for m in metrics if m["label"] == "Mật độ") == "—"
                    assert next(m["value"] for m in metrics if m["label"] == "Số ứng viên") == "100"
                    cap_messages = check_cap_messages()
                    expect(page.locator('[data-testid="stException"]')).to_have_count(0)
                    capture(f"flow_{image_id}.png", warning)
                    results["flow"].append({"image_id": image_id, "metrics": metrics,
                                            "manual_tables": page.locator('[data-testid="stTable"]').count(),
                                            **cap_messages,
                                            "page_text": page.locator("body").inner_text()})
                    print(f"PASS: số ứng viên, mật độ, một thông báo giới hạn và không exception trên {image_id}", flush=True)

                frame = choose("moon_ap15_hia_c01")
                expect(heading).to_have_count(0)
                capture("outside_regions.png", page.get_by_role("combobox"))
                results["outside_regions"] = "PASS: Apollo 15 không hiện bảng đếm tay"

                canvas = frame.locator("#craterCanvas")
                canvas.scroll_into_view_if_needed()
                box = canvas.bounding_box()
                factor = box["width"] / 512
                page.mouse.move(box["x"] + 400.5 * factor, box["y"] + 200.5 * factor)
                page.mouse.down()
                page.mouse.move(box["x"] + 440.5 * factor, box["y"] + 200.5 * factor, steps=5)
                page.mouse.up()
                frame.locator("#centerX").fill("500")
                frame.locator("#centerY").fill("200")
                frame.locator("#radius").fill("40")
                frame.locator("#applyEdit").click()
                frame.locator("#circles button").first.click()
                expect(frame.locator("#radius")).to_have_value("40.00")
                capture("radius_right_edge_before.png", canvas)
                # The visible handle is the left rim (460, 200), not a clamped point at x=511.
                box = canvas.bounding_box()
                factor = box["width"] / 512
                page.mouse.move(box["x"] + 460.5 * factor, box["y"] + 200.5 * factor)
                page.mouse.down()
                page.mouse.move(box["x"] + 450.5 * factor, box["y"] + 210.5 * factor, steps=8)
                page.mouse.up()
                expect(frame.locator("#centerX")).to_have_value("500.00")
                expect(frame.locator("#centerY")).to_have_value("200.00")
                expect(frame.locator("#radius")).to_have_value(f"{math.hypot(50, 10):.2f}")
                capture("radius_right_edge_after.png", canvas)
                results["radius_drag"] = {"centre": [500, 200], "before": 40,
                                          "after_display": frame.locator("#radius").input_value(),
                                          "expected": math.hypot(50, 10)}
                print("PASS #8: kéo nút vành trái đổi bán kính, tâm giữ nguyên", flush=True)
            assert not errors, errors
            expect(page.locator('[data-testid="stException"]')).to_have_count(0)
            results["page_errors"] = errors
            results["status"] = "PASS"
        except Exception:
            page.screenshot(path=str(args.out / "failure.png"))
            results["status"] = "FAIL"
            raise
        finally:
            results["observed_url"] = page.url
            (args.out / "browser_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            browser.close()
    print("PASS: các assertion đã chạy, phạm vi ghi tại browser_results.json; mỗi ảnh mở trang mới", flush=True)


if __name__ == "__main__":
    main()
