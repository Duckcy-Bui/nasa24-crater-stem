"""Chụp minh họa báo cáo bằng Playwright, không tạo dữ liệu khảo sát."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

IMAGE = "moon_ap16_m109134835l_c01"
CIRCLES = [(370, 360, 21), (320, 446, 15), (434, 410, 12), (276, 200, 17),
           (195, 211, 11), (251, 390, 14), (90, 120, 16)]


def choose_image(page, expect):
    picker = page.get_by_role("combobox", name="Chọn ảnh để mở")
    picker.wait_for()
    expect(page.frame_locator('iframe[title="app.crater_player_canvas"]').locator("#downloadAnswer")).to_be_enabled()
    expect(page.locator('[data-testid="stApp"]')).to_have_attribute("data-test-script-state", "notRunning")
    picker.fill(IMAGE)
    page.get_by_role("option", name=re.compile("^" + IMAGE + r" ·")).click()
    container = page.locator(".st-key-player_canvas_" + IMAGE)
    expect(container).to_have_attribute("data-stale", "false")
    frame = container.frame_locator('iframe[title="app.crater_player_canvas"]')
    expect(frame.locator("#downloadAnswer")).to_be_enabled()
    expect(page.locator('[data-testid="stApp"]')).to_have_attribute("data-test-script-state", "notRunning")
    return container, frame


def draw_circles(page, frame, expect):
    canvas = frame.locator("#craterCanvas")
    for i, (x, y, radius) in enumerate(CIRCLES):
        frame.locator("#drawMode").click()
        canvas.scroll_into_view_if_needed()
        box = canvas.bounding_box()
        factor = box["width"] / 512
        page.mouse.move(box["x"] + (x + 0.5) * factor, box["y"] + (y + 0.5) * factor)
        page.mouse.down()
        page.mouse.move(box["x"] + (x + radius + 0.5) * factor, box["y"] + (y + 0.5) * factor, steps=6)
        page.mouse.up()
        expect(frame.locator("#circles button")).to_have_count(i + 1)
        frame.locator("#centerX").fill(str(x))
        frame.locator("#centerY").fill(str(y))
        frame.locator("#radius").fill(str(radius))
        frame.locator("#applyEdit").click()
    frame.locator("#editMode").click()
    frame.locator("#circles button").nth(3).click()
    expect(frame.locator("#centerX")).to_have_value("276.00")


def download(page, button, target: Path):
    with page.expect_download() as pending:
        button.click()
    pending.value.save_as(target)


def score_answer(page, expect):
    page.get_by_role("button", name="Chấm bài", exact=True).click()
    score = page.locator('[data-testid="stMetric"]').filter(
        has=page.get_by_text("Điểm theo nhãn đã kiểm chéo", exact=True))
    expect(score.locator('[data-testid="stMetricValue"]')).to_have_text("60/100", timeout=90000)
    expect(page.locator('[data-testid="stApp"]')).to_have_attribute(
        "data-test-script-state", "notRunning", timeout=90000)
    expect(page.get_by_text("Tìm đúng 6 hố · bỏ sót 4", exact=True)).to_be_visible()
    return score


def capture_score(page, out: Path):
    # Đưa tiêu đề lên đầu khung, giữ kích thước ảnh minh họa cũ.
    head = page.get_by_role("heading", name="Chấm bài", exact=True)
    main = page.locator('[data-testid="stMain"]')
    y = head.bounding_box()["y"]
    main.evaluate("(e,y)=>e.scrollTop+=y-20", y)
    page.evaluate("()=>new Promise(requestAnimationFrame)")
    page.screenshot(path=str(out / "ket_qua_cham_bai.jpg"), type="jpeg", quality=92,
                    clip={"x": 0, "y": 0, "width": 1440, "height": 829})


def capture_card(page, out: Path):
    head = page.get_by_role("heading", name="Thẻ khoa học", exact=True)
    # Thêm chỗ cuộn cuối trang cho khung cắt, giữ nguyên nội dung và chiều rộng.
    block = page.locator('[data-testid="stMainBlockContainer"]')
    old_style = block.get_attribute("style")
    block.evaluate("e=>e.style.paddingBottom='60px'")
    head.scroll_into_view_if_needed()
    y = head.bounding_box()["y"]
    page.locator('[data-testid="stMain"]').evaluate("(e,y)=>e.scrollTop+=y-20", y)
    page.evaluate("()=>new Promise(requestAnimationFrame)")
    page.screenshot(path=str(out / "the_khoa_hoc.jpg"), type="jpeg", quality=92,
                    clip={"x": 0, "y": head.bounding_box()["y"] - 16, "width": 1440, "height": 230.4})
    block.evaluate('(e,s)=>s===null?e.removeAttribute("style"):e.setAttribute("style",s)', old_style)


def main():
    parser = argparse.ArgumentParser(
        description="Chụp Hình 5.1–5.3 qua app đang chạy; tạo một lượt chấm minh họa trên máy chủ.")
    parser.add_argument("--url", default="http://127.0.0.1:8501")
    parser.add_argument("--out", type=Path, required=True, help="thư mục mới, không ghi đè bằng chứng")
    parser.add_argument("--server-commit", default="unknown",
                        help="mốc do người triển khai cung cấp, không được script xác minh")
    args = parser.parse_args()

    from playwright.sync_api import expect, sync_playwright

    args.out.mkdir(parents=True, exist_ok=False)
    results = {
        "url": args.url,
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "viewport": {"width": 1440, "height": 900},
        "device_scale_factor": 10 / 9,
        "image_id": IMAGE,
        "circles": CIRCLES,
        "server_commit_provided_by_owner": args.server_commit,
        "server_commit_independently_verified": False,
        "method": ("Playwright mouse draw + numeric edit; seven illustration circles copied from old Figure 5.1; "
                   "no learner data"),
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport=results["viewport"], device_scale_factor=results["device_scale_factor"])
        page.set_default_timeout(30000)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        try:
            page.goto(results["url"])
            container, frame = choose_image(page, expect)
            draw_circles(page, frame, expect)
            download(page, frame.locator("#downloadAnswer"), args.out / "player_answer.json")
            page.locator('[data-testid="stMain"]').evaluate("(e)=>e.scrollTop=0")
            page.screenshot(path=str(args.out / "giao_dien_khoanh_ho.jpg"), type="jpeg", quality=92)
            score = score_answer(page, expect)
            download(page, page.get_by_role("button", name="Tải kết quả chấm (JSON)"), args.out / "score.json")
            results["metrics"] = page.locator('[data-testid="stMetric"]').all_inner_texts()
            results["page_text"] = page.locator("body").inner_text()
            results["canvas_text"] = frame.locator("body").inner_text()
            results["bounds"] = {"iframe": container.bounding_box(), "score": score.bounding_box()}
            capture_score(page, args.out)
            capture_card(page, args.out)
            results["card_capture_bottom_padding_px"] = 60
            results["page_errors"] = errors
            assert not errors
            expect(page.locator('[data-testid="stException"]')).to_have_count(0)
            results["status"] = "PASS"
        except Exception:
            page.screenshot(path=str(args.out / "failure.png"))
            results["status"] = "FAIL"
            raise
        finally:
            (args.out / "capture.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
            browser.close()
    print("PASS: seven circles, score 60/100, 6/10 known labels; three screenshots captured")


if __name__ == "__main__":
    main()
