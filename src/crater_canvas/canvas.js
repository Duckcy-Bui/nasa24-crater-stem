(function () {
  "use strict";
  const canvas = document.getElementById("craterCanvas"), ctx = canvas.getContext("2d");
  const els = Object.fromEntries(["drawMode", "editMode", "deleteCircle", "undo", "status", "centerX", "centerY", "radius", "applyEdit", "error", "circles", "downloadAnswer"].map(id => [id, document.getElementById(id)]));
  let image = new Image(), loaded = false, state = null, circles = [], selected = null, mode = "draw", drag = null, history = [];
  const clone = value => JSON.parse(JSON.stringify(value));
  function message(type, values) { window.parent.postMessage({ isStreamlitMessage: true, type, ...values }, "*"); }
  function frameHeight() { message("streamlit:setFrameHeight", { height: Math.ceil(document.body.getBoundingClientRect().height) + 8 }); }
  function chosen() { return circles.find(c => c.crater_id === selected); }
  function point(event) { return CraterGeometry.canvasToImage(event.clientX, event.clientY, canvas.getBoundingClientRect()); }
  function nextId() { let n = 1; while (circles.some(c => c.crater_id === "U" + n)) n++; return "U" + n; }
  function commit(previous, remember = true) {
    if (remember) { history.push(clone(previous)); if (history.length > 50) history.shift(); }
    state.revision += 1;
    message("streamlit:setComponentValue", { dataType: "json", value: { image_id: state.image_id, session_token: state.session_token, revision: state.revision, circles: clone(circles) } });
    refresh();
  }
  function paint() {
    ctx.clearRect(0, 0, 512, 512);
    if (loaded) ctx.drawImage(image, 0, 0, 512, 512);
    for (const c of circles.concat(drag?.kind === "draw" ? [drag.circle] : [])) {
      const active = c.crater_id === selected;
      ctx.strokeStyle = active ? "#ffe16b" : "#66e7ff"; ctx.lineWidth = active ? 2.5 : 1.8;
      ctx.beginPath(); ctx.arc(c.x, c.y, c.r, 0, Math.PI * 2); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(c.x - 4, c.y); ctx.lineTo(c.x + 4, c.y); ctx.moveTo(c.x, c.y - 4); ctx.lineTo(c.x, c.y + 4); ctx.stroke();
      ctx.font = "12px sans-serif"; ctx.fillStyle = ctx.strokeStyle; ctx.fillText(c.crater_id, Math.min(478, c.x + 6), Math.max(13, c.y - 6));
      if (active) ctx.fillRect(c.x + c.r - 3, c.y - 3, 6, 6);
    }
  }
  function refresh() {
    const c = chosen();
    els.drawMode.setAttribute("aria-pressed", String(mode === "draw"));
    els.editMode.setAttribute("aria-pressed", String(mode === "edit"));
    els.deleteCircle.disabled = !c; els.undo.disabled = !history.length;
    els.downloadAnswer.disabled = !state || !loaded || !!drag;
    for (const [field, key] of [["centerX", "x"], ["centerY", "y"], ["radius", "r"]]) { els[field].disabled = !c; els[field].value = c ? c[key] : ""; }
    els.applyEdit.disabled = !c;
    els.status.textContent = `${circles.length} vòng tròn${c ? " · Đã chọn " + c.crater_id : ""} · Tọa độ tính theo ảnh gốc 512 × 512 px`;
    els.circles.replaceChildren();
    for (const circle of circles) {
      const button = document.createElement("button"); button.type = "button"; button.className = "circleRow";
      button.setAttribute("aria-pressed", String(circle.crater_id === selected));
      button.textContent = `${circle.crater_id} — x: ${circle.x.toFixed(2)} · y: ${circle.y.toFixed(2)} · r: ${circle.r.toFixed(2)} px`;
      button.onclick = () => { selected = circle.crater_id; mode = "edit"; els.error.textContent = ""; refresh(); };
      els.circles.append(button);
    }
    paint(); frameHeight();
  }
  canvas.addEventListener("pointerdown", event => {
    if (!loaded || !state || event.button !== 0) return;
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
    if (!chosen() || drag) return;
    const previous = clone(circles); circles = circles.filter(c => c.crater_id !== selected); selected = null; commit(previous);
  };
  els.undo.onclick = () => {
    if (!history.length || drag) return;
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
  document.getElementById("editor").addEventListener("submit", event => {
    event.preventDefault(); const c = chosen(); if (!c || drag) return;
    const values = [els.centerX.value, els.centerY.value, els.radius.value], [x, y, r] = values.map(Number);
    if (values.some(value => value.trim() === "") || ![x, y, r].every(Number.isFinite) || x < 0 || x > 511 || y < 0 || y > 511 || r <= 0) {
      els.error.textContent = "Tâm x, y phải trong 0–511; bán kính phải hữu hạn và lớn hơn 0."; return;
    }
    const previous = clone(circles); Object.assign(c, { x, y, r }); els.error.textContent = "";
    if (JSON.stringify(previous) !== JSON.stringify(circles)) commit(previous); else refresh();
  });
  window.addEventListener("message", event => {
    if (event.source !== window.parent || event.data?.type !== "streamlit:render") return;
    const args = event.data.args;
    if (!args || typeof args.image_id !== "string" || !Array.isArray(args.circles)) return;
    if (!state || state.image_id !== args.image_id || state.session_token !== args.session_token) {
      state = { image_id: args.image_id, session_token: args.session_token, data_kind: args.data_kind, revision: args.revision };
      circles = clone(args.circles); selected = null; drag = null; history = []; loaded = false;
      const nextImage = new Image(); image = nextImage;
      const currentImage = () => image === nextImage && state.image_id === args.image_id && state.session_token === args.session_token;
      nextImage.onload = () => { if (currentImage()) { loaded = true; refresh(); } };
      nextImage.onerror = () => { if (currentImage()) { loaded = false; els.error.textContent = "Không mở được ảnh; thử chọn lại ảnh hoặc kiểm tra bộ dữ liệu."; frameHeight(); } };
      nextImage.src = args.image_url;
      refresh();
    } else if (args.revision > state.revision) {
      state.revision = args.revision; circles = clone(args.circles); drag = null; history = []; if (!chosen()) selected = null;
      refresh();
    }
  });
  new ResizeObserver(frameHeight).observe(document.body);
  message("streamlit:componentReady", { apiVersion: 1 }); frameHeight();
})();
