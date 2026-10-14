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
from src.player_annotations import apply_canvas_event, build_player_crater_set, save_player_answers

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "processed"
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
    st.set_page_config(page_title="Khoanh hố Mặt Trăng · NASA 24", page_icon="🌕", layout="centered")
    st.title("Khoanh hố Mặt Trăng")
    st.caption("NASA 24 · Nhóm 2 · Mở ảnh, khoanh hố và lưu câu trả lời của bạn.")
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
    image_id = st.selectbox("Chọn ảnh để mở", image_ids, format_func=lambda ident: f"{ident} · {groups.get(ident, '')}")
    try:
        metadata, image_url = load_image(image_id, (DATA_DIR / f"{image_id}.json").read_bytes(), (DATA_DIR / f"{image_id}.png").read_bytes())
    except (OSError, ValueError, ContractError) as error:
        st.error(f"Không mở được ảnh: {error}")
        st.stop()
    st.caption(f"Ảnh gốc: 512 × 512 px · Mặt Trăng · {metadata['scale_m_per_px']:g} m/px")
    st.session_state["player_active_metadata"] = metadata
    draft = drafts.setdefault(image_id, {"revision": 0, "circles": []})
    event = canvas_component(image_id=image_id, data_kind=metadata["data_kind"], image_url=image_url, circles=draft["circles"], revision=draft["revision"], session_token=token, key=f"player_canvas_{image_id}", default=None)
    try:
        draft = apply_canvas_event(draft, event, metadata, token)
        drafts[image_id] = draft
    except ContractError as error:
        st.error(f"Thay đổi chưa được lưu: {error}")
    answer = build_player_crater_set(draft["circles"], metadata)
    count = len(answer["circles"])
    st.markdown(f"**Câu trả lời hiện tại: {count} vòng tròn.**")
    if st.button("Lưu câu trả lời trên máy", use_container_width=True):
        try:
            directory = save_player_answers(ROOT / "outputs" / "player_answers", metadata, draft["circles"])
            st.session_state["player_saved_message"] = f"Đã lưu {count} vòng tròn cho {image_id}: {directory}"
        except (OSError, ValueError, ContractError) as error:
            st.error(f"Chưa lưu được câu trả lời: {error}")
    if st.session_state.get("player_saved_message"):
        st.success(st.session_state["player_saved_message"])
    st.caption("Đổi ảnh rồi quay lại vẫn giữ bản nháp trong phiên hiện tại. Tải JSON hoặc lưu trên máy trước khi đóng trang.")
    st.info("Đây là phần khoanh hố của người chơi. Bộ ảnh chưa có đáp án đã xác minh nên hiện chưa chấm điểm.")


if __name__ == "__main__":
    main()
