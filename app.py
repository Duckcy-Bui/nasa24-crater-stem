"""S1-09/S2-08/S2-13: open lunar images, edit and score circles, then show statistics and science cards."""
from __future__ import annotations

import base64
import io
import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

from src.contracts import ContractError, read_json, validate_metadata
from src.game_results import COLORS, render_overlay, save_round, score_round
from src.integration import cards_view, statistics_view
from src.pipeline import detect_machine, load_image as load_processed_image, load_overlay_set
from src.player_annotations import apply_canvas_event
from src.player_ui import handle_save_request

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "processed"
PLAYER_OUTPUT_DIR = ROOT / "outputs" / "player_answers"
SCORE_OUTPUT_DIR = ROOT / "outputs" / "player_scores"
REFERENCE_DIR = ROOT / "data" / "reference_labels"
CONFIG_PATH = ROOT / "configs" / "default.json"
canvas_component = components.declare_component("crater_player_canvas", path=str(ROOT / "src" / "crater_canvas"))


@st.cache_data(show_spinner=False)
def load_image(image_id: str, metadata_bytes: bytes, png_bytes: bytes) -> tuple[dict, str]:
    metadata = json.loads(metadata_bytes)
    validate_metadata(metadata)
    if metadata["image_id"] != image_id:
        raise ContractError("Tên ảnh và image_id metadata không khớp.")
    with Image.open(io.BytesIO(png_bytes)) as picture:
        if picture.size != (512, 512) or picture.format != "PNG":
            raise ContractError("Ảnh xem phải là PNG 512 × 512.")
        picture.verify()
    return metadata, "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii")


@st.cache_data(show_spinner=False, max_entries=8)
def machine_for_image(image_id: str, data_dir: str, stamp: float) -> dict:
    """Ứng viên máy của một ảnh; cache theo thời điểm sửa file ảnh (stamp)."""
    metadata, image, valid = load_processed_image(image_id, data_dir)
    detected = detect_machine(metadata, image, valid, hough_params=read_json(CONFIG_PATH)["hough"])
    return {"machine": detected["machine"], "hough": detected["hough"], "postprocess": detected["postprocess"],
            "raw_count": len(detected["raw_circles"]), "valid_pixels": int(detected["pre"]["valid_mask"].sum()),
            "seconds": round(detected["seconds_preprocess"] + detected["seconds_hough"], 1)}


def code_version() -> str:
    from scripts.run_end_to_end import code_version as version
    return version()


def score_current_answer(image_id: str, metadata: dict, draft: dict, png_bytes: bytes) -> dict:
    """Chạy máy, chấm câu trả lời hiện tại và lưu thành một lượt mới."""
    detected = machine_for_image(image_id, str(DATA_DIR), (DATA_DIR / f"{image_id}.npy").stat().st_mtime)
    reference_path = REFERENCE_DIR / f"{image_id}_craters_catalogue.json"
    reference = load_overlay_set(reference_path, metadata, "catalogue") if reference_path.is_file() else None
    evaluation = read_json(CONFIG_PATH)["evaluation"]
    scored = score_round(draft["circles"], metadata, detected["machine"], detected["hough"], reference, evaluation)
    config = {"hough": detected["hough"], "evaluation": evaluation, "postprocess": detected["postprocess"]}
    directory = save_round(SCORE_OUTPUT_DIR, metadata, scored, config=config, code_version=code_version())
    return {"revision": draft["revision"], "scored": scored, "detected": detected,
            "overlay": render_overlay(png_bytes, scored), "run_id": directory.name,
            "path": str(Path("outputs") / "player_scores" / directory.name), "time": datetime.now().strftime("%H:%M")}


def show_result(result: dict, draft: dict) -> None:
    scored, detected = result["scored"], result["detected"]
    score, scope = scored["score"], scored["scope"]
    machine, catalogue = score["vs_machine"], score["vs_catalogue"]
    if result["revision"] != draft["revision"]:
        st.warning("Bạn đã sửa vòng sau lần chấm này. Bấm Chấm bài để chấm lại.")
    picture_column, numbers_column = st.columns([1.3, 1])
    with picture_column:
        st.image(result["overlay"], width="stretch")
        legend = "".join(f'<span><i style="border-color:{COLORS[key]}"></i>{label}</span>' for key, label in (
            ("player", f"Vòng của bạn ({score['player_circles']})"),
            ("machine", f"Ứng viên máy ({len(scored['machine']['circles'])})"),
            ("reference", f"Nhãn tham chiếu ({len(scored['reference']['circles']) if scored['reference'] else 0})")))
        st.html(f'<div class="nasa-legend">{legend}</div>')
    with numbers_column:
        if catalogue["status"] == "scored":
            st.metric("Điểm theo nhãn đã kiểm chéo", f"{catalogue['score']:g}/100")
            line = f"Tìm đúng **{catalogue['correct']}** hố · bỏ sót **{len(catalogue['missed_ids'])}**"
            if catalogue["wrong_ids"] is not None:
                line += f" · khoanh sai **{len(catalogue['wrong_ids'])}**"
            st.markdown(line)
            st.caption(catalogue["reason"])
        else:
            st.info(f"Chưa có điểm. {catalogue['reason']}")
        st.markdown("**So với máy** · chỉ để tham khảo, máy không phải đáp án")
        same, mine, theirs = st.columns(3)
        same.metric("Trùng máy", machine["matched"])
        mine.metric("Chỉ bạn khoanh", len(machine["player_only_ids"]))
        theirs.metric("Chỉ máy có", len(machine["machine_only_ids"]))
        lo, hi = scope["searched_px"]
        st.caption(f"Máy tìm bán kính {lo}–{hi} px (đường kính {scope['diameter_m'][0]:g}–{scope['diameter_m'][1]:g} m), "
                   f"bước {scope['step_px']} px, {scope['radii']} bán kính. Hố ngoài dải này máy không tìm. "
                   f"Vòng trùng khi tâm lệch ≤ {score['rule']['center_tolerance_fraction']:g} × bán kính.")
        if scope["sparse"]:
            st.warning(f"Lưới bán kính thưa (bước {scope['step_px']} px): máy có thể bỏ sót hố có bán kính nằm giữa hai bước.")
        if detected["raw_count"] >= detected["hough"]["max_circles"]:
            st.caption(f"Máy dừng ở {detected['hough']['max_circles']} ứng viên (giới hạn max_circles), "
                       "nên có thể còn hố máy chưa xét.")
        st.caption(f"Đã lưu lượt chấm lúc {result['time']}: {result['path']}")
        st.download_button("Tải kết quả chấm (JSON)", data=json.dumps(score, ensure_ascii=False, indent=2),
                           file_name=f"{result['run_id']}_score.json", mime="application/json",
                           key=f"player_score_download_{result['run_id']}")


def section_head(title: str, text: str) -> None:
    st.html(f'<div class="nasa-results-head"><h2>{title}</h2><p>{text}</p></div>')


def show_statistics(result: dict, metadata: dict) -> None:
    """S2-13: thống kê ứng viên máy của lượt chấm gần nhất (hàm do S2-09 cài)."""
    st.html('<div class="nasa-rule"></div>')
    section_head("Thống kê hố trên ảnh", "Đếm, kích thước và mật độ của ứng viên máy trong vùng ảnh hợp lệ. "
                 "Đây là ứng viên chưa kiểm chứng, không phải số hố thật.")
    view = statistics_view(result["scored"]["machine"], metadata, result["detected"]["valid_pixels"])
    if view["status"] == "pending":
        st.info(f"Chưa có thống kê. {view['reason']}")
        return
    if view["status"] == "error":
        st.error(view["reason"])
        return
    data = view["data"]
    count, area, density = st.columns(3)
    count.metric("Số ứng viên", data["count"])
    area.metric("Diện tích hợp lệ", "—" if data.get("valid_area_km2") is None else f"{data['valid_area_km2']:.2f} km²")
    density.metric("Mật độ", "—" if data.get("density_per_km2") is None else f"{data['density_per_km2']:.2f} /km²")
    histogram = data.get("histogram")
    if histogram and histogram["counts"]:
        edges = histogram["bin_edges_m"]
        labels = [f"{a:g}–{b:g}" for a, b in zip(edges, edges[1:])]
        st.caption("Phân bố đường kính (m), số ứng viên mỗi khoảng")
        st.bar_chart({"Đường kính (m)": labels, "Số ứng viên": histogram["counts"]}, x="Đường kính (m)",
                     y="Số ứng viên", color=COLORS["machine"], height=220)
    for note in data.get("limitations") or []:
        st.caption(str(note))


def show_cards(image_id: str) -> None:
    """S2-13: thẻ khoa học của ảnh đang mở (dữ liệu do S2-10 cài); thẻ thiếu nguồn không hiện."""
    st.html('<div class="nasa-rule"></div>')
    section_head("Thẻ khoa học", "Kiến thức gắn với đúng địa điểm của ảnh, mỗi thẻ có nguồn đã kiểm tra.")
    view = cards_view(image_id)
    if view["status"] == "pending":
        st.info(f"Chưa có thẻ. {view['reason']}")
        return
    if view["status"] == "error":
        st.error(view["reason"])
        return
    if not view["cards"]:
        st.caption("Ảnh này chưa có thẻ khoa học.")
    for card in view["cards"]:
        with st.container(border=True):
            st.markdown(f"**{card['title']}**")
            st.markdown(card["body"])
            position = card.get("position")
            where = f"Vị trí trên ảnh: x = {position['x']:.0f}, y = {position['y']:.0f} px · " if position else ""
            st.caption(f"{where}Nguồn: [{card['source_title']}]({card['source_url']})")
    if view["rejected"]:
        st.warning("Không hiện các thẻ sai hợp đồng: " + "; ".join(view["rejected"]))


def render_results(image_id: str, metadata: dict, draft: dict, png_bytes: bytes) -> None:
    st.html('<div class="nasa-rule"></div>')
    head_column, button_column = st.columns([2.4, 1], vertical_alignment="center")
    with head_column:
        section_head("Chấm bài", "Máy tìm hố bằng Hough NumPy rồi so với các vòng bạn đã khoanh. "
                     "Điểm chỉ có khi ảnh có nhãn đã được kiểm chéo.")
    with button_column:
        clicked = st.button("Chấm bài", key=f"player_score_{image_id}", type="primary", width="stretch")
    results = st.session_state.setdefault("player_results", {})
    if clicked:
        try:
            with st.spinner("Máy đang tìm hố trên ảnh này (khoảng 5–10 giây)…"):
                results[image_id] = score_current_answer(image_id, metadata, draft, png_bytes)
        except (OSError, ValueError, ContractError) as error:
            st.error(f"Chưa chấm được: {error}")
    if image_id in results:
        show_result(results[image_id], draft)
        show_statistics(results[image_id], metadata)
    else:
        st.caption("Khoanh xong rồi bấm Chấm bài. Mỗi lần chấm được lưu thành một lượt riêng trong outputs/player_scores/. "
                   "Thống kê hố hiện sau khi máy chạy.")
    show_cards(image_id)


def main() -> None:
    st.set_page_config(page_title="Khoanh hố Mặt Trăng · NASA 24", page_icon="🌕", layout="wide")
    css = (ROOT / "src" / "crater_canvas" / "app.css").read_text(encoding="utf-8")
    st.html(f"<style>{css}</style>")
    brand_column, picker_column = st.columns([1, 1.15], vertical_alignment="center")
    with brand_column:
        st.html('''<header class="nasa-brand">
            <svg viewBox="0 0 24 24" fill="none" stroke="#ECEAE4" stroke-width="1.4" aria-hidden="true">
              <circle cx="12" cy="12" r="9.2"/><circle cx="9" cy="10" r="2.2"/>
              <circle cx="15.2" cy="15" r="1.5"/><circle cx="15.4" cy="7.8" r="1"/>
            </svg><div><h1>Khoanh hố Mặt Trăng</h1>
            <p>NASA 24 · Nhóm 2 · Mở ảnh, khoanh hố và lưu câu trả lời</p></div>
            </header>''')
    image_ids = read_json(ROOT / "data" / "s106_bundle" / "manifest.json")["image_ids"]
    missing = [ident for ident in image_ids if not (DATA_DIR / f"{ident}.png").is_file() or not (DATA_DIR / f"{ident}.json").is_file()]
    if missing:
        st.info("Mở bộ 26 ảnh Mặt Trăng có sẵn trong repo để bắt đầu.")
        if st.button("Chuẩn bị bộ ảnh ngoại tuyến", type="primary"):
            try:
                from scripts.install_s106_dataset import install_dataset
                with st.spinner("Đang xác minh và chuẩn bị bộ ảnh…"):
                    install_dataset(DATA_DIR)
                st.rerun()
            except (OSError, ValueError, ContractError) as error:
                st.error(f"Chưa chuẩn bị được bộ ảnh: {error}")
        st.caption("Bạn cũng có thể chạy: python scripts/install_s106_dataset.py")
        st.stop()
    st.session_state.setdefault("player_drafts", {})
    st.session_state.setdefault("player_session_token", uuid4().hex)
    drafts = st.session_state["player_drafts"]
    token = st.session_state["player_session_token"]
    previous_metadata = st.session_state.get("player_active_metadata")
    if previous_metadata is not None:
        previous_id = previous_metadata["image_id"]
        previous_event = st.session_state.get(f"player_canvas_{previous_id}")
        try:
            drafts[previous_id] = apply_canvas_event(drafts[previous_id], previous_event, previous_metadata, token)
        except ContractError as error:
            st.error(f"Thay đổi của {previous_id} chưa được lưu: {error}")
    groups = {item["image_id"]: item["region_group"] for item in json.loads((ROOT / "data" / "s106_bundle" / "crops.json").read_text(encoding="utf-8"))}
    def image_label(ident: str) -> str:
        count = len(drafts.get(ident, {}).get("circles", []))
        return f"{ident} · {groups.get(ident, '')}" + (f" · {count} vòng" if count else "")
    # Refresh the serialized selection together with changing draft-count labels.
    # Otherwise the frontend can reset to its first option when a label changes.
    if "player_image_picker" in st.session_state:
        st.session_state["player_image_picker"] = st.session_state["player_image_picker"]
    with picker_column:
        image_id = st.selectbox("Chọn ảnh để mở", image_ids, format_func=image_label, key="player_image_picker")
    try:
        metadata, image_url = load_image(image_id, (DATA_DIR / f"{image_id}.json").read_bytes(), (DATA_DIR / f"{image_id}.png").read_bytes())
    except (OSError, ValueError, ContractError) as error:
        st.error(f"Không mở được ảnh: {error}")
        st.stop()
    st.html('<div class="nasa-rule"></div>')
    st.session_state["player_active_metadata"] = metadata
    draft = drafts.setdefault(image_id, {"revision": 0, "circles": []})
    save_states = st.session_state.setdefault("player_save_states", {})
    save_state = save_states.setdefault(image_id, {"handled_nonces": [], "result": None})
    event = canvas_component(image_id=image_id, data_kind=metadata["data_kind"], image_url=image_url, scale_m_per_px=metadata["scale_m_per_px"], circles=draft["circles"], revision=draft["revision"], session_token=token, save_result=save_state["result"], key=f"player_canvas_{image_id}", default=None)
    try:
        draft = apply_canvas_event(draft, event, metadata, token)
        drafts[image_id] = draft
        def consume_save(consumed: dict) -> None:
            save_states[image_id] = consumed
        updated_save_state = handle_save_request(draft, event, metadata, token, save_state, PLAYER_OUTPUT_DIR,
                                                before_save=consume_save)
        if updated_save_state != save_state:
            save_states[image_id] = updated_save_state
            # Send the completed save result back even if its revision is unchanged.
            st.rerun()
    except ContractError as error:
        st.error(f"Thay đổi chưa được lưu: {error}")
    render_results(image_id, metadata, draft, (DATA_DIR / f"{image_id}.png").read_bytes())


if __name__ == "__main__":
    main()
