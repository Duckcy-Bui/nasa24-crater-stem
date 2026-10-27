(function () {
  "use strict";
  const canvas = document.getElementById("craterCanvas"), ctx = canvas.getContext("2d");
  const els = Object.fromEntries(["drawMode", "editMode", "panMode", "deleteCircle", "undo", "status", "centerX", "centerY", "radius", "applyEdit", "error", "circles", "downloadAnswer",
    "zoomIn", "zoomOut", "zoomFit", "zoomLevel", "canvasWrap", "workspace"].map(id => [id, document.getElementById(id)]));
  let image = new Image(), loaded = false, state = null, circles = [], selected = null, mode = "draw", drag = null, history = [];
  let pendingSave = null, saveResult = null;
  // View-only state: zoom z in [1, 8] and the top-left of the visible window in pixel-edge units.
  // It never enters history, the Streamlit value, the saved answer or the JSON download.
  // Circles use the data contract instead: pixel centres are integers (see geometry.js).
  const HALF = CraterGeometry.PIXEL_CENTER;
  const FIT = Object.freeze({ z: 1, x: 0, y: 0 }), ZOOM_STEP = 1.25;
  let view = { ...FIT }, panDrag = null, gesture = null, spaceHeld = false;
  const touches = new Map();
  const saveEls = Object.fromEntries(["saveAnswer", "saveLabel", "saveStatus", "saveStatusText", "savedPath", "copySavedPath", "saveError"].map(id => [id, document.getElementById(id)]));
  const MONO = 'ui-monospace, "SF Mono", "Cascadia Mono", "JetBrains Mono", "Ubuntu Mono", "DejaVu Sans Mono", Menlo, Consolas, monospace';
  const clone = value => JSON.parse(JSON.stringify(value));
  const clamp = (value, low, high) => Math.min(high, Math.max(low, value));
  function message(type, values) { window.parent.postMessage({ isStreamlitMessage: true, type, ...values }, "*"); }
  function frameHeight() { message("streamlit:setFrameHeight", { height: Math.ceil(document.body.getBoundingClientRect().height) + 8 }); }
  function chosen() { return circles.find(c => c.crater_id === selected); }
  function rect() { return canvas.getBoundingClientRect(); }
  function imagePoint(event) { return CraterGeometry.screenToPixel(event.clientX, event.clientY, rect(), view); }
  function point(event) { const p = imagePoint(event); return { x: clamp(p.x, 0, 511), y: clamp(p.y, 0, 511) }; }
  function screenScale() { return (rect().width || 512) * view.z / 512; } // CSS px per image px
  function nextId() { let n = 1; while (circles.some(c => c.crater_id === "U" + n)) n++; return "U" + n; }
  function setClass(element, name, on) { element?.classList?.toggle(name, on); }

  /* Fit the square map to the visible height of the Streamlit page, so wheel zoom never fights page scroll. */
  function fitStage() {
    const workspace = els.workspace;
    if (!workspace?.style?.setProperty) return;
    try {
      const frame = window.frameElement, host = window.parent;
      const width = document.documentElement.clientWidth;
      if (!frame || !host?.innerHeight || !width || width <= 720) { setClass(workspace, "fitted", false); return; }
      let scrolled = 0;
      for (let node = frame.parentElement; node; node = node.parentElement) scrolled += node.scrollTop || 0;
      const frameTop = frame.getBoundingClientRect().top + scrolled;
      const stageTop = els.canvasWrap.getBoundingClientRect().top;
      const byHeight = host.innerHeight - frameTop - stageTop - 64; // zoom/meta row under the map
      const byWidth = width - 28 - 340;
      const size = Math.floor(clamp(Math.min(byWidth, byHeight), 420, 900));
      workspace.style.setProperty("--stage-size", size + "px");
      setClass(workspace, "fitted", true);
    } catch (_) { setClass(workspace, "fitted", false); }
  }

  function refreshSavedPath() {
    if (!saveEls.savedPath || !saveResult?.ok) return;
    const path = saveResult.path;
    const width = saveEls.savedPath.getBoundingClientRect?.().width || 260;
    const limit = Math.max(20, Math.floor(width / 7.3)); // 12px monospace, including fallback fonts.
    const split = path.lastIndexOf("/"), run = path.slice(split + 1);
    let display = path;
    if (path.length > limit) {
      const firstDirectory = path.slice(0, path.indexOf("/") + 1);
      let prefix = firstDirectory + "…/";
      if (prefix.length + 7 + 1 + 13 > limit) prefix = firstDirectory.slice(0, 3) + "…/";
      if (run.length + prefix.length <= limit) display = prefix + run;
      else {
        const tail = Math.min(13, Math.max(4, limit - prefix.length - 8));
        display = prefix + run.slice(0, limit - prefix.length - tail - 1) + "…" + run.slice(-tail);
      }
    }
    saveEls.savedPath.textContent = display; saveEls.savedPath.title = path;
  }
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
      refreshSavedPath();
    }
    frameHeight();
  }
  function commit(previous, remember = true) {
    if (remember) { history.push(clone(previous)); if (history.length > 50) history.shift(); }
    state.revision += 1;
    message("streamlit:setComponentValue", { dataType: "json", value: { image_id: state.image_id, session_token: state.session_token, revision: state.revision, circles: clone(circles) } });
    refresh();
  }

  /* Drawing: image crop for zoom; strokes, labels and handles keep their on-screen size. */
  function paint() {
    const box = rect(), css = box.width || 512, dpr = window.devicePixelRatio || 1, backing = Math.max(1, Math.round(css * dpr));
    if (canvas.width !== backing || canvas.height !== backing) { canvas.width = backing; canvas.height = backing; }
    ctx.setTransform(backing / css, 0, 0, backing / css, 0, 0);
    ctx.clearRect(0, 0, css, css);
    ctx.imageSmoothingEnabled = view.z < 3;
    const span = 512 / view.z, k = css / span;
    if (loaded) ctx.drawImage(image, view.x, view.y, span, span, 0, 0, css, css);
    const screen = c => ({ x: (c.x + HALF - view.x) * k, y: (c.y + HALF - view.y) * k, r: c.r * k });
    const drawing = drag?.kind === "draw" ? [drag.circle] : [];
    const ordered = circles.filter(c => c.crater_id !== selected).concat(circles.filter(c => c.crater_id === selected), drawing);
    for (const c of ordered) {
      const s = screen(c);
      if (s.x + s.r < -40 || s.y + s.r < -40 || s.x - s.r > css + 40 || s.y - s.r > css + 40) continue;
      const active = c.crater_id === selected, sketch = drawing.includes(c);
      const color = active ? "#FFD84D" : "#5FE3F5", width = active ? 2.5 : 1.6;
      ctx.setLineDash?.(sketch ? [4, 4] : []);
      ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(0,0,0,.55)"; ctx.lineWidth = width + 2; ctx.stroke();
      ctx.strokeStyle = color; ctx.lineWidth = width; ctx.stroke();
      ctx.setLineDash?.([]);
      ctx.beginPath(); ctx.moveTo(s.x - 4, s.y); ctx.lineTo(s.x + 4, s.y); ctx.moveTo(s.x, s.y - 4); ctx.lineTo(s.x, s.y + 4);
      ctx.lineWidth = 1.5; ctx.stroke();
      const label = sketch ? `r ${c.r.toFixed(1)} px` : c.crater_id;
      const lx = clamp(s.x + s.r * 0.72 + 3, 2, css - (sketch ? 74 : 30)), ly = clamp(s.y - s.r * 0.72 - 3, 13, css - 4);
      ctx.font = `600 11px ${MONO}`;
      ctx.strokeStyle = "rgba(10,12,15,.85)"; ctx.lineWidth = 3; ctx.strokeText(label, lx, ly);
      ctx.fillStyle = sketch ? "#ECEAE4" : active ? "#FFD84D" : "#8DEFFB"; ctx.fillText(label, lx, ly);
      if (active) {
        ctx.fillStyle = "#FFD84D"; ctx.strokeStyle = "#0A0C0F"; ctx.lineWidth = 1.5;
        const hx = (Math.min(511, c.x + c.r) + HALF - view.x) * k;
        ctx.fillRect(hx - 4, s.y - 4, 8, 8); ctx.strokeRect(hx - 4, s.y - 4, 8, 8);
      }
    }
  }

  function refreshView() {
    const fit = view.z <= 1 + 1e-9;
    if (els.zoomLevel) els.zoomLevel.textContent = Math.round(view.z * 100) + "%";
    if (els.zoomOut) els.zoomOut.disabled = fit;
    if (els.zoomIn) els.zoomIn.disabled = view.z >= 8 - 1e-9;
    if (els.zoomFit) els.zoomFit.disabled = fit;
    setClass(els.canvasWrap, "can-pan", spaceHeld && !fit);
    setClass(els.canvasWrap, "panning", !!panDrag || !!gesture);
  }
  function setView(next) { view = CraterGeometry.clampView(next); refreshView(); paint(); }
  function zoomBy(factor, clientX, clientY) {
    const box = rect();
    if (clientX === undefined) { clientX = box.left + box.width / 2; clientY = box.top + box.height / 2; }
    setView(CraterGeometry.zoomViewAt(view, view.z * factor, clientX, clientY, box));
  }

  function refresh() {
    const c = chosen();
    for (const [name, value] of [["drawMode", "draw"], ["editMode", "edit"], ["panMode", "pan"]]) {
      if (!els[name]) continue;
      els[name].setAttribute("aria-pressed", String(mode === value)); els[name].disabled = !!pendingSave;
    }
    if (els.canvasWrap?.dataset) els.canvasWrap.dataset.mode = mode;
    els.deleteCircle.disabled = !c || !!pendingSave; els.undo.disabled = !history.length || !!pendingSave;
    els.downloadAnswer.disabled = !state || !loaded || !!drag;
    for (const [field, key] of [["centerX", "x"], ["centerY", "y"], ["radius", "r"]]) {
      els[field].disabled = !c || !!pendingSave; els[field].value = c ? Number(c[key]).toFixed(2) : "";
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
    const listHead = document.getElementById("listHead");
    if (listHead) listHead.hidden = circles.length === 0;
    const coach = document.getElementById("coach"), chipText = document.getElementById("modeChipText");
    if (coach) coach.hidden = circles.length > 0;
    if (chipText) chipText.textContent = mode === "draw" ? "Vẽ: nhấn tâm hố, kéo ra vành"
      : mode === "pan" ? "Kéo ảnh: kéo để di chuyển, cuộn chuột để phóng to" : "Chọn / sửa: kéo tâm để dời, kéo vành để đổi bán kính";
    if (selectedLabel) selectedLabel.textContent = c ? c.crater_id : "";
    if (hint) {
      hint.hidden = !!c;
      hint.textContent = circles.length ? "Chọn một vòng trên ảnh hoặc trong danh sách để sửa tọa độ." : "Vẽ vòng đầu tiên, sau đó có thể sửa tọa độ chính xác ở đây.";
    }
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
    refreshView(); paint(); refreshSaved();
  }

  /* Pointer input: one finger or the mouse annotates; two fingers, the pan mode, Space or the middle button move the view. */
  function rollbackDrag() {
    if (!drag) return;
    circles = drag.previous; drag = null;
    if (!chosen()) selected = null;
    refresh();
  }
  function touchPair() {
    const [a, b] = [...touches.values()];
    return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2, d: Math.hypot(a.x - b.x, a.y - b.y) || 1 };
  }
  canvas.addEventListener("pointerdown", event => {
    if (!loaded || !state || pendingSave) return;
    if (event.pointerType === "touch") {
      touches.set(event.pointerId, { x: event.clientX, y: event.clientY });
      if (touches.size >= 2) {
        event.preventDefault(); rollbackDrag();
        if (touches.size === 2) {
          const pair = touchPair();
          gesture = { d: pair.d, z: view.z, anchor: CraterGeometry.screenToImage(pair.x, pair.y, rect(), view) };
          refreshView();
        }
        return;
      }
    }
    if (gesture) return;
    if (event.button === 1 || spaceHeld || mode === "pan") {
      event.preventDefault();
      if (view.z > 1 + 1e-9) {
        panDrag = { pointerId: event.pointerId, clientX: event.clientX, clientY: event.clientY, x: view.x, y: view.y };
        canvas.setPointerCapture(event.pointerId); refreshView();
      }
      return;
    }
    if (event.button !== 0) return;
    event.preventDefault(); const p = point(event), previous = clone(circles);
    const tolerance = 9 / screenScale();
    els.error.textContent = "";
    if (mode === "draw") {
      if (circles.length >= 500) { els.error.textContent = "Mỗi ảnh hỗ trợ tối đa 500 vòng tròn."; return; }
      drag = { kind: "draw", previous, pointerId: event.pointerId, circle: { crater_id: nextId(), x: p.x, y: p.y, r: .01 } };
    } else {
      const active = chosen();
      const activeDistance = active ? Math.hypot(p.x - active.x, p.y - active.y) : Infinity;
      const picked = active && (activeDistance <= Math.min(tolerance, active.r / 2) || Math.abs(activeDistance - active.r) <= tolerance)
        ? active : circles.slice().reverse().find(c => Math.hypot(p.x - c.x, p.y - c.y) <= c.r + tolerance);
      if (!picked) { selected = null; refresh(); return; }
      selected = picked.crater_id;
      const distance = Math.hypot(p.x - picked.x, p.y - picked.y);
      drag = { kind: distance > Math.min(tolerance, picked.r / 2) && Math.abs(distance - picked.r) <= tolerance ? "resize" : "move", previous, pointerId: event.pointerId, offsetX: p.x - picked.x, offsetY: p.y - picked.y };
      refresh();
    }
    canvas.setPointerCapture(event.pointerId); paint();
  });
  canvas.addEventListener("pointermove", event => {
    if (event.pointerType === "touch" && touches.has(event.pointerId)) {
      touches.set(event.pointerId, { x: event.clientX, y: event.clientY });
      if (gesture && touches.size >= 2) {
        const pair = touchPair(), box = rect(), z = clamp(gesture.z * pair.d / gesture.d, 1, 8);
        setView({ z, x: gesture.anchor.x - (pair.x - box.left) * 512 / (box.width * z), y: gesture.anchor.y - (pair.y - box.top) * 512 / (box.height * z) });
        return;
      }
    }
    if (panDrag) {
      if (event.pointerId !== panDrag.pointerId) return;
      const k = 512 / ((rect().width || 512) * view.z);
      setView({ z: view.z, x: panDrag.x - (event.clientX - panDrag.clientX) * k, y: panDrag.y - (event.clientY - panDrag.clientY) * k });
      return;
    }
    if (!drag || event.pointerId !== drag.pointerId) return;
    const p = point(event), raw = imagePoint(event);
    if (drag.kind === "draw") drag.circle.r = Math.max(.01, Math.hypot(raw.x - drag.circle.x, raw.y - drag.circle.y));
    else {
      const c = chosen();
      if (drag.kind === "move") { c.x = clamp(p.x - drag.offsetX, 0, 511); c.y = clamp(p.y - drag.offsetY, 0, 511); }
      else c.r = Math.max(.01, Math.hypot(raw.x - c.x, raw.y - c.y));
    }
    paint();
  });
  function endPointer(event, cancel) {
    if (event.pointerType === "touch" && touches.delete(event.pointerId) && gesture) {
      if (touches.size < 2) { gesture = null; refreshView(); }
      return;
    }
    if (panDrag && event.pointerId === panDrag.pointerId) {
      panDrag = null;
      if (canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
      refreshView(); return;
    }
    if (!drag || event.pointerId !== drag.pointerId) return;
    const previous = drag.previous;
    if (cancel) circles = previous;
    else if (drag.kind === "draw" && drag.circle.r >= .5) { circles.push(drag.circle); selected = drag.circle.crater_id; }
    drag = null;
    if (canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
    if (!chosen()) selected = null;
    if (!cancel && JSON.stringify(previous) !== JSON.stringify(circles)) commit(previous); else refresh();
  }
  canvas.addEventListener("pointerup", event => endPointer(event, false));
  canvas.addEventListener("pointercancel", event => endPointer(event, true));
  canvas.addEventListener("wheel", event => {
    if (!loaded || !state) return;
    event.preventDefault();
    if (drag || gesture) return;
    zoomBy(event.deltaY < 0 ? ZOOM_STEP : 1 / ZOOM_STEP, event.clientX, event.clientY);
  }, { passive: false });
  // Keyboard shortcuts stay on the focused map; nothing is registered on window or document.
  canvas.addEventListener("keydown", event => {
    if (!loaded || !state) return;
    if (event.key === "+" || event.key === "=") { event.preventDefault(); zoomBy(ZOOM_STEP); }
    else if (event.key === "-" || event.key === "_") { event.preventDefault(); zoomBy(1 / ZOOM_STEP); }
    else if (event.key === "0") { event.preventDefault(); setView(FIT); }
    else if (event.code === "Space" || event.key === " ") { event.preventDefault(); spaceHeld = true; refreshView(); }
  });
  canvas.addEventListener("keyup", event => { if (event.code === "Space" || event.key === " ") { spaceHeld = false; refreshView(); } });
  canvas.addEventListener("blur", () => { spaceHeld = false; refreshView(); });
  if (els.zoomIn) els.zoomIn.onclick = () => zoomBy(ZOOM_STEP);
  if (els.zoomOut) els.zoomOut.onclick = () => zoomBy(1 / ZOOM_STEP);
  if (els.zoomFit) els.zoomFit.onclick = () => setView(FIT);

  els.drawMode.onclick = () => { mode = "draw"; refresh(); };
  els.editMode.onclick = () => { mode = "edit"; refresh(); };
  if (els.panMode) els.panMode.onclick = () => { mode = "pan"; refresh(); };
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
    // Display rounding must not alter an untouched field's source precision.
    const keys = ["x", "y", "r"];
    const numbers = values.map((value, index) => value === Number(c[keys[index]]).toFixed(2) ? c[keys[index]] : Number(value));
    const [x, y, r] = numbers;
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
    if (metadataLabel) metadataLabel.textContent = "512 × 512 px · (0, 0) là tâm điểm ảnh góc trên-trái" + (Number.isFinite(args.scale_m_per_px) ? ` · ${args.scale_m_per_px} m/px` : "");
    if (!state || state.image_id !== args.image_id || state.session_token !== args.session_token) {
      state = { image_id: args.image_id, session_token: args.session_token, data_kind: args.data_kind, revision: args.revision };
      pendingSave = null; saveResult = args.save_result || null;
      circles = clone(args.circles); selected = null; drag = null; history = []; loaded = false;
      view = { ...FIT }; panDrag = null; gesture = null; spaceHeld = false; touches.clear();
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
  try { if (typeof window.parent.addEventListener === "function" && window.frameElement) window.parent.addEventListener("resize", () => { fitStage(); paint(); }); } catch (_) { /* cross-origin host */ }
  new ResizeObserver(() => { fitStage(); paint(); refreshSavedPath(); frameHeight(); }).observe(document.body);
  fitStage();
  message("streamlit:componentReady", { apiVersion: 1 }); frameHeight();
})();
