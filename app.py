"""S1-09: local player interface for opening lunar images and editing circles."""
from __future__ import annotations

import base64
import io
import json
from pathlib import Path
from uuid import uuid4

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

from src.contracts import ContractError, read_json, validate_metadata
from src.player_annotations import apply_canvas_event
from src.player_ui import handle_save_request

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "processed"
PLAYER_OUTPUT_DIR = ROOT / "outputs" / "player_answers"
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
    with picker_column:
        image_id = st.selectbox("Chọn ảnh để mở", image_ids, format_func=lambda ident: f"{groups.get(ident, '')} · {ident}")
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


if __name__ == "__main__":
    main()
