(function () {
  "use strict";
  const canvas = document.getElementById("craterCanvas"), ctx = canvas.getContext("2d");
  const els = Object.fromEntries(["drawMode", "editMode", "deleteCircle", "undo", "status", "centerX", "centerY", "radius", "applyEdit", "error", "circles", "downloadAnswer"].map(id => [id, document.getElementById(id)]));
  let image = new Image(), loaded = false, state = null, circles = [], selected = null, mode = "draw", drag = null, history = [];
  let pendingSave = null, saveResult = null;
  const saveEls = Object.fromEntries(["saveAnswer", "saveLabel", "saveStatus", "saveStatusText", "savedPath", "copySavedPath", "saveError"].map(id => [id, document.getElementById(id)]));
  const clone = value => JSON.parse(JSON.stringify(value));
  function message(type, values) { window.parent.postMessage({ isStreamlitMessage: true, type, ...values }, "*"); }
  function frameHeight() { message("streamlit:setFrameHeight", { height: Math.ceil(document.body.getBoundingClientRect().height) + 8 }); }
  function chosen() { return circles.find(c => c.crater_id === selected); }
  function point(event) { return CraterGeometry.canvasToImage(event.clientX, event.clientY, canvas.getBoundingClientRect()); }
  function nextId() { let n = 1; while (circles.some(c => c.crater_id === "U" + n)) n++; return "U" + n; }
  function refreshSaved() {
    if (saveEls.saveAnswer) saveEls.saveAnswer.disabled = !state || !loaded || !!drag || !!pendingSave;
    if (saveEls.saveLabel) saveEls.saveLabel.textContent = pendingSave ? "Đang lưu…" : "Lưu trên máy";
    const current = !pendingSave && saveResult && state && saveResult.revision === state.revision && saveResult.image_id === state.image_id;
    if (saveEls.saveStatus) saveEls.saveStatus.hidden = !(current && saveResult.ok);
    if (saveEls.saveError) {
      saveEls.saveError.hidden = !(current && !saveResult.ok);
      saveEls.saveError.textContent = current && !saveResult.ok ? "Chưa lưu được câu trả lời: " + saveResult.error : "";
    }
    if (current && saveResult.ok) {
      if (saveEls.saveStatusText) saveEls.saveStatusText.textContent = `Đã lưu ${saveResult.count} vòng · ${saveResult.time}`;
      if (saveEls.savedPath) { saveEls.savedPath.textContent = saveResult.path; saveEls.savedPath.title = saveResult.path; }
    }
    frameHeight();
  }
  function commit(previous, remember = true) {
    if (remember) { history.push(clone(previous)); if (history.length > 50) history.shift(); }
    state.revision += 1;
    message("streamlit:setComponentValue", { dataType: "json", value: { image_id: state.image_id, session_token: state.session_token, revision: state.revision, circles: clone(circles) } });
    refresh();
  }
  function paint() {
    ctx.clearRect(0, 0, 512, 512);
    if (loaded) ctx.drawImage(image, 0, 0, 512, 512);
    const displayCircles = circles.filter(c => c.crater_id !== selected).concat(circles.filter(c => c.crater_id === selected), drag?.kind === "draw" ? [drag.circle] : []);
    for (const c of displayCircles) {
      const active = c.crater_id === selected;
      const lineWidth = active ? 2.5 : 1.6;
      ctx.strokeStyle = "rgba(0,0,0,.65)"; ctx.lineWidth = lineWidth + 2;
      ctx.beginPath(); ctx.arc(c.x, c.y, c.r, 0, Math.PI * 2); ctx.stroke();
      ctx.strokeStyle = active ? "#ffd84d" : "#5fe3f5"; ctx.lineWidth = lineWidth;
      ctx.stroke();
      ctx.beginPath(); ctx.moveTo(c.x - 4, c.y); ctx.lineTo(c.x + 4, c.y); ctx.moveTo(c.x, c.y - 4); ctx.lineTo(c.x, c.y + 4); ctx.stroke();
      ctx.font = "600 11px monospace"; ctx.fillStyle = ctx.strokeStyle;
      const labelX = Math.min(478, c.x + 6), labelY = Math.max(13, c.y - 6);
      ctx.strokeStyle = "rgba(10,12,15,.85)"; ctx.lineWidth = 3; ctx.strokeText(c.crater_id, labelX, labelY);
      ctx.fillText(c.crater_id, labelX, labelY);
      if (active) ctx.fillRect(c.x + c.r - 3, c.y - 3, 6, 6);
    }
  }
  function refresh() {
    const c = chosen();
    els.drawMode.setAttribute("aria-pressed", String(mode === "draw"));
    els.editMode.setAttribute("aria-pressed", String(mode === "edit"));
    els.drawMode.disabled = !!pendingSave; els.editMode.disabled = !!pendingSave;
    els.deleteCircle.disabled = !c || !!pendingSave; els.undo.disabled = !history.length || !!pendingSave;
    els.downloadAnswer.disabled = !state || !loaded || !!drag;
    for (const [field, key] of [["centerX", "x"], ["centerY", "y"], ["radius", "r"]]) {
      els[field].disabled = !c || !!pendingSave; els[field].value = c ? c[key] : "";
      els[field].setAttribute("aria-invalid", "false");
      if (els[field].parentElement?.dataset) els[field].parentElement.dataset.invalid = "false";
    }
    els.applyEdit.disabled = !c || !!pendingSave;
    document.getElementById("editor").hidden = !c;
    els.status.textContent = `${circles.length} vòng tròn${c ? " · Đã chọn " + c.crater_id : ""} · Tọa độ tính theo ảnh gốc 512 × 512 px`;
    const countLabel = document.getElementById("circleCount"), empty = document.getElementById("emptyCircles");
    const selectedLabel = document.getElementById("selectedId"), hint = document.getElementById("selectionHint");
    if (countLabel) countLabel.textContent = circles.length;
    if (empty) empty.hidden = circles.length > 0;
    const coach = document.getElementById("coach"), modeLabel = document.getElementById("modeChip");
    if (coach) coach.hidden = circles.length > 0;
    if (modeLabel) modeLabel.textContent = mode === "draw" ? "Vẽ: nhấn tâm hố, kéo ra vành" : "Chọn / sửa: kéo tâm để dời, kéo vành để đổi bán kính";
    if (selectedLabel) selectedLabel.textContent = c ? c.crater_id : "Chưa chọn";
    if (hint) hint.textContent = c ? "Nhập tọa độ hoặc kéo tâm và vành trên ảnh để điều chỉnh." : "Chọn một vòng trên ảnh hoặc trong danh sách để sửa.";
    els.circles.replaceChildren();
    let selectedRow = null;
    for (const circle of circles) {
      const button = document.createElement("button"); button.type = "button"; button.className = "crow circleRow";
      button.setAttribute("aria-pressed", String(circle.crater_id === selected));
      button.disabled = !!pendingSave;
      button.setAttribute("aria-label", `${circle.crater_id}, tâm x ${circle.x.toFixed(2)}, tâm y ${circle.y.toFixed(2)}, bán kính ${circle.r.toFixed(2)} px`);
      for (const [index, value] of [circle.crater_id, circle.x.toFixed(2), circle.y.toFixed(2), circle.r.toFixed(2)].entries()) {
        const cell = document.createElement("span"); cell.textContent = value;
        if (index === 0) cell.className = "cid circle-id";
        button.append(cell);
      }
      button.onclick = () => { if (pendingSave) return; selected = circle.crater_id; mode = "edit"; els.error.textContent = ""; refresh(); };
      els.circles.append(button);
      if (circle.crater_id === selected) selectedRow = button;
    }
    // Scroll only this list, so selecting a ring never moves the whole page.
    if (selectedRow?.getBoundingClientRect && els.circles.getBoundingClientRect) {
      const listRect = els.circles.getBoundingClientRect(), rowRect = selectedRow.getBoundingClientRect();
      if (rowRect.top < listRect.top) els.circles.scrollTop += rowRect.top - listRect.top;
      else if (rowRect.bottom > listRect.bottom) els.circles.scrollTop += rowRect.bottom - listRect.bottom;
    }
    paint(); refreshSaved();
  }
  canvas.addEventListener("pointerdown", event => {
    if (!loaded || !state || pendingSave || event.button !== 0) return;
    event.preventDefault(); const p = point(event), previous = clone(circles);
    const tolerance = 9 * 512 / canvas.getBoundingClientRect().width;
    els.error.textContent = "";
    if (mode === "draw") {
      if (circles.length >= 500) { els.error.textContent = "Mỗi ảnh hỗ trợ tối đa 500 vòng tròn."; return; }
      drag = { kind: "draw", previous, circle: { crater_id: nextId(), x: p.x, y: p.y, r: .01 } };
    } else {
      const active = chosen();
      const activeDistance = active ? Math.hypot(p.x - active.x, p.y - active.y) : Infinity;
      const picked = active && (activeDistance <= Math.min(tolerance, active.r / 2) || Math.abs(activeDistance - active.r) <= tolerance)
        ? active : circles.slice().reverse().find(c => Math.hypot(p.x - c.x, p.y - c.y) <= c.r + tolerance);
      if (!picked) { selected = null; refresh(); return; }
      selected = picked.crater_id;
      const distance = Math.hypot(p.x - picked.x, p.y - picked.y);
      drag = { kind: distance > Math.min(tolerance, picked.r / 2) && Math.abs(distance - picked.r) <= tolerance ? "resize" : "move", previous, offsetX: p.x - picked.x, offsetY: p.y - picked.y };
      refresh();
    }
    canvas.setPointerCapture(event.pointerId); paint();
  });
  canvas.addEventListener("pointermove", event => {
    if (!drag) return;
    const p = point(event), rect = canvas.getBoundingClientRect();
    if (drag.kind === "draw") {
      drag.circle.r = Math.max(.01, CraterGeometry.imageRadius(event.clientX - rect.left - drag.circle.x * rect.width / 512, event.clientY - rect.top - drag.circle.y * rect.height / 512, rect));
    } else {
      const c = chosen();
      if (drag.kind === "move") { c.x = Math.max(0, Math.min(511, p.x - drag.offsetX)); c.y = Math.max(0, Math.min(511, p.y - drag.offsetY)); }
      else c.r = Math.max(.01, CraterGeometry.imageRadius(event.clientX - rect.left - c.x * rect.width / 512, event.clientY - rect.top - c.y * rect.height / 512, rect));
    }
    paint();
  });
  function endDrag(event, cancel) {
    if (!drag) return;
    const previous = drag.previous;
    if (cancel) circles = previous;
    else if (drag.kind === "draw" && drag.circle.r >= .5) { circles.push(drag.circle); selected = drag.circle.crater_id; }
    drag = null;
    if (canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
    if (!cancel && JSON.stringify(previous) !== JSON.stringify(circles)) commit(previous); else refresh();
  }
  canvas.addEventListener("pointerup", event => endDrag(event, false));
  canvas.addEventListener("pointercancel", event => endDrag(event, true));
  els.drawMode.onclick = () => { mode = "draw"; refresh(); };
  els.editMode.onclick = () => { mode = "edit"; refresh(); };
  els.deleteCircle.onclick = () => {
    if (!chosen() || drag || pendingSave) return;
    const previous = clone(circles); circles = circles.filter(c => c.crater_id !== selected); selected = null; commit(previous);
  };
  els.undo.onclick = () => {
    if (!history.length || drag || pendingSave) return;
    circles = history.pop(); if (!chosen()) selected = null; commit(null, false);
  };
  els.downloadAnswer.onclick = () => {
    if (!state || !loaded || drag) return;
    const answer = { schema_version: "1.0", data_kind: state.data_kind, image_id: state.image_id,
      source: "player", reference_source: null,
      circles: circles.map(c => ({ crater_id: c.crater_id, x: c.x, y: c.y, r: c.r, confidence: null, votes: null })) };
    const blob = new Blob([JSON.stringify(answer, null, 2) + "\n"], { type: "application/json" });
    const url = URL.createObjectURL(blob), link = document.createElement("a");
    link.href = url; link.download = state.image_id + "_player.json";
    document.body.append(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
  };
  if (saveEls.saveAnswer) saveEls.saveAnswer.onclick = () => {
    if (!state || !loaded || drag || pendingSave) return;
    pendingSave = window.crypto?.randomUUID?.() || Date.now().toString(36) + "_" + Math.random().toString(36).slice(2);
    message("streamlit:setComponentValue", { dataType: "json", value: {
      image_id: state.image_id, session_token: state.session_token, revision: state.revision,
      circles: clone(circles), save_nonce: pendingSave
    } });
    refresh();
  };
  if (saveEls.copySavedPath) saveEls.copySavedPath.onclick = async () => {
    if (!saveResult?.ok) return;
    try { await navigator.clipboard.writeText(saveResult.path); saveEls.copySavedPath.title = "Đã sao chép"; }
    catch (_) { saveEls.copySavedPath.title = "Chọn đường dẫn để sao chép thủ công"; }
  };
  document.getElementById("editor").addEventListener("submit", event => {
    event.preventDefault(); const c = chosen(); if (!c || drag || pendingSave) return;
    const fields = [els.centerX, els.centerY, els.radius], values = fields.map(field => field.value);
    const numbers = values.map(Number), [x, y, r] = numbers;
    const invalid = values.map((value, index) => value.trim() === "" || !Number.isFinite(numbers[index])
      || (index < 2 ? numbers[index] < 0 || numbers[index] > 511 : numbers[index] <= 0));
    fields.forEach((field, index) => {
      field.setAttribute("aria-invalid", String(invalid[index]));
      if (field.parentElement?.dataset) field.parentElement.dataset.invalid = String(invalid[index]);
    });
    if (invalid.some(Boolean)) {
      els.error.textContent = "Tâm x, y phải trong 0–511; bán kính phải hữu hạn và lớn hơn 0."; return;
    }
    const previous = clone(circles); Object.assign(c, { x, y, r }); els.error.textContent = "";
    if (JSON.stringify(previous) !== JSON.stringify(circles)) commit(previous); else refresh();
  });
  window.addEventListener("message", event => {
    if (event.source !== window.parent || event.data?.type !== "streamlit:render") return;
    const args = event.data.args;
    if (!args || typeof args.image_id !== "string" || !Array.isArray(args.circles)) return;
    const metadataLabel = document.getElementById("imageMeta");
    if (metadataLabel) metadataLabel.textContent = "512 × 512 px · Gốc (0, 0) ở góc trên trái" + (Number.isFinite(args.scale_m_per_px) ? ` · ${args.scale_m_per_px} m/px` : "");
    if (!state || state.image_id !== args.image_id || state.session_token !== args.session_token) {
      state = { image_id: args.image_id, session_token: args.session_token, data_kind: args.data_kind, revision: args.revision };
      pendingSave = null; saveResult = args.save_result || null;
      circles = clone(args.circles); selected = null; drag = null; history = []; loaded = false;
      const nextImage = new Image(); image = nextImage;
      const currentImage = () => image === nextImage && state.image_id === args.image_id && state.session_token === args.session_token;
      nextImage.onload = () => { if (currentImage()) { loaded = true; refresh(); } };
      nextImage.onerror = () => { if (currentImage()) { loaded = false; els.error.textContent = "Không mở được ảnh; thử chọn lại ảnh hoặc kiểm tra bộ dữ liệu."; frameHeight(); } };
      nextImage.src = args.image_url;
      refresh();
    } else {
      const wasPending = pendingSave && args.save_result?.nonce === pendingSave;
      if (args.save_result) saveResult = args.save_result;
      if (wasPending) pendingSave = null;
      if (args.revision > state.revision) {
        state.revision = args.revision; circles = clone(args.circles); drag = null; history = []; if (!chosen()) selected = null;
        refresh();
      } else if (wasPending) refresh();
      else refreshSaved();
    }
  });
  new ResizeObserver(frameHeight).observe(document.body);
  message("streamlit:componentReady", { apiVersion: 1 }); frameHeight();
})();
