"use strict";

// Deterministic component protocol checks. Not Chromium/layout proof.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const component = path.join(__dirname, "../src/crater_canvas");
const html = fs.readFileSync(path.join(component, "index.html"), "utf8");
const tags = [...html.matchAll(/<([a-z][a-z0-9]*)\b[^>]*\bid="([^"]+)"[^>]*>/gi)];
const ids = tags.map(match => match[2]);
assert.equal(new Set(ids).size, ids.length, "actual HTML must not duplicate IDs");
for (const id of ["craterCanvas", "editor", "saveAnswer", "saveLabel", "saveStatus",
                  "saveStatusText", "savedPath", "copySavedPath", "saveError", "downloadAnswer"]) {
  assert.ok(ids.includes(id), "actual HTML is missing " + id);
}

function boot() {
  const messages = [], images = [], listeners = {}, downloads = [], blobs = new Map(), copied = [];
  let nonceSequence = 0;
  class Element {
    constructor(tag = "div") {
      this.tagName = tag.toUpperCase(); this.attributes = {}; this.children = [];
      this.handlers = {}; this.disabled = false; this.hidden = false; this.value = "";
      this.textContent = ""; this.style = {}; this.dataset = {};
    }
    set value(value) { this._value = String(value); }
    get value() { return this._value; }
    set textContent(value) { this._text = String(value); }
    get textContent() { return this._text; }
    setAttribute(key, value) { this.attributes[key] = String(value); }
    getAttribute(key) { return this.attributes[key] ?? null; }
    addEventListener(name, handler) { this.handlers[name] = handler; }
    replaceChildren(...children) { this.children = children; }
    append(...children) { this.children.push(...children); }
    remove() {}
    click() {
      if (this.disabled) return;
      if (this.download) downloads.push({filename: this.download, value: JSON.parse(blobs.get(this.href).parts.join(""))});
      else this.onclick?.();
    }
    emit(name, event = {}) { this.handlers[name]?.({preventDefault() {}, ...event}); }
  }
  const elements = {};
  for (const match of tags) {
    const element = new Element(match[1]);
    element.disabled = /\bdisabled(?:\s|=|>|$)/.test(match[0]);
    element.hidden = /\bhidden(?:\s|=|>|$)/.test(match[0]);
    elements[match[2]] = element;
  }
  const canvas = elements.craterCanvas, captures = new Set();
  const rect = {left: 17, top: 31, width: 512, height: 512};
  canvas.getContext = () => new Proxy({}, {get: () => () => {}});
  canvas.getBoundingClientRect = () => rect;
  canvas.setPointerCapture = id => captures.add(id);
  canvas.hasPointerCapture = id => captures.has(id);
  canvas.releasePointerCapture = id => captures.delete(id);
  const parent = {postMessage: value => messages.push(value)};
  const window = {
    parent, crypto: {randomUUID: () => "mock-save-" + (++nonceSequence)},
    addEventListener: (name, handler) => { listeners[name] = handler; },
  };
  const body = new Element("body");
  body.getBoundingClientRect = () => ({height: 800});
  const context = {
    window, document: {getElementById: id => elements[id] ?? null, createElement: tag => new Element(tag), body},
    navigator: {clipboard: {writeText: async value => { copied.push(value); }}},
    Image: class {constructor() { images.push(this); }},
    ResizeObserver: class {observe() {}},
    Blob: class {constructor(parts, options) { this.parts = parts; this.type = options.type; }},
    URL: {
      createObjectURL(blob) { const id = "blob:save-test-" + blobs.size; blobs.set(id, blob); return id; },
      revokeObjectURL(id) { blobs.delete(id); },
    },
    setTimeout: () => 0,
  };
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(path.join(component, "geometry.js"), "utf8"), context);
  context.CraterGeometry = window.CraterGeometry;
  vm.runInContext(fs.readFileSync(path.join(component, "canvas.js"), "utf8"), context);
  const events = () => messages.filter(m => m.type === "streamlit:setComponentValue")
    .map(m => JSON.parse(JSON.stringify(m.value)));
  function render(args) { listeners.message({source: parent, data: {type: "streamlit:render", args}}); }
  // x, y are image coordinates; the pointer lands on that pixel's centre (+0.5 CSS px from its edge).
  function draw(x = 100, y = 120, r = 40) {
    canvas.emit("pointerdown", {button: 0, pointerId: 1, clientX: rect.left + x + 0.5, clientY: rect.top + y + 0.5});
    canvas.emit("pointermove", {pointerId: 1, clientX: rect.left + x + 0.5 + r, clientY: rect.top + y + 0.5});
    canvas.emit("pointerup", {pointerId: 1, clientX: rect.left + x + 0.5 + r, clientY: rect.top + y + 0.5});
  }
  function edit(x) {
    elements.centerX.value = x;
    elements.editor.emit("submit");
  }
  return {elements, canvas, images, render, draw, edit, events, downloads, copied, rect};
}

const initial = {
  image_id: "image_a", data_kind: "real", session_token: "session_a",
  revision: 0, circles: [], image_url: "data:image/png;base64,a", save_result: null,
};
function loaded() {
  const ui = boot(); ui.render(initial); ui.images.at(-1).onload(); return ui;
}
function success(request, changes = {}) {
  return {nonce: request.save_nonce, revision: request.revision, image_id: request.image_id,
    ok: true, count: request.circles.length, time: "19:47",
    path: "outputs/player_answers/" + request.save_nonce, ...changes};
}
function ack(ui, request, result) {
  ui.render({...initial, image_id: request.image_id, session_token: request.session_token,
    revision: request.revision, circles: request.circles, save_result: result});
}

let checks = 0;
function check(name, body) {
  body(); checks += 1; console.log("ok - " + name);
}

check("empty save submits explicit nonce at revision zero", () => {
  const ui = loaded();
  assert.equal(ui.elements.saveAnswer.disabled, false);
  ui.elements.saveAnswer.click();
  const request = ui.events().at(-1);
  assert.equal(request.revision, 0);
  assert.deepEqual(request.circles, []);
  assert.equal(request.image_id, "image_a");
  assert.equal(request.session_token, "session_a");
  assert.equal(typeof request.save_nonce, "string");
  assert.ok(request.save_nonce.length >= 1 && request.save_nonce.length <= 64);
  ack(ui, request, success(request));
  assert.equal(ui.elements.saveStatus.hidden, false);
  assert.equal(ui.elements.saveAnswer.disabled, false);
});

check("save submits latest committed snapshot before any edit ACK without incrementing revision", () => {
  const ui = loaded();
  ui.draw(320, 120, 20);
  ui.edit("300.5");
  const edit = ui.events().at(-1);
  assert.equal(edit.revision, 2);
  ui.elements.saveAnswer.click();
  const request = ui.events().at(-1);
  assert.equal(request.revision, edit.revision);
  assert.deepEqual(request.circles, [{crater_id: "U1", x: 300.5, y: 120, r: 20}]);
  assert.deepEqual(request.circles, edit.circles);
  assert.equal(ui.events().filter(e => e.save_nonce).length, 1);
  ui.elements.saveAnswer.onclick(); // Guard a second activation, even without native disabled handling.
  assert.equal(ui.events().filter(e => e.save_nonce).length, 1);
});

check("pending freezes every mutation while download remains current and available", () => {
  const ui = loaded();
  ui.draw(110, 120, 25);
  ui.elements.saveAnswer.click();
  const request = ui.events().at(-1), eventCount = ui.events().length;
  for (const id of ["drawMode", "editMode", "deleteCircle", "undo",
                    "centerX", "centerY", "radius", "applyEdit", "saveAnswer"]) {
    assert.equal(ui.elements[id].disabled, true, id + " must freeze while saving");
  }
  assert.ok(ui.elements.circles.children.every(row => row.disabled));
  assert.equal(ui.elements.downloadAnswer.disabled, false);
  ui.draw(300, 310, 30);
  ui.edit("400");
  ui.elements.deleteCircle.onclick();
  ui.elements.undo.onclick();
  ui.elements.circles.children[0].onclick();
  assert.equal(ui.events().length, eventCount, "pending must reject mutation handlers");
  ui.elements.downloadAnswer.click();
  assert.deepEqual(ui.downloads[0], {filename: "image_a_player.json",
    value: {schema_version: "1.0", data_kind: "real", image_id: "image_a",
      source: "player", reference_source: null,
      circles: [{crater_id: "U1", x: 110, y: 120, r: 25, confidence: null, votes: null}]}});
  ack(ui, request, success(request));
  assert.equal(ui.elements.centerX.disabled, false);
  assert.equal(ui.elements.saveAnswer.disabled, false);
  assert.equal(ui.elements.saveStatus.hidden, false);
});

check("equal-revision ACK shows saved path; a committed edit makes success dirty", () => {
  const ui = loaded();
  ui.draw();
  ui.elements.saveAnswer.click();
  const request = ui.events().at(-1);
  const result = success(request);
  ack(ui, request, result);
  assert.equal(ui.elements.saveStatus.hidden, false);
  assert.equal(ui.elements.saveError.hidden, true);
  assert.equal(ui.elements.savedPath.textContent, result.path);
  assert.match(ui.elements.saveStatusText.textContent, /1/);
  ui.elements.copySavedPath.click();
  assert.deepEqual(ui.copied, [result.path]);
  ui.edit("222.25");
  assert.equal(ui.events().at(-1).revision, request.revision + 1);
  assert.equal(ui.elements.saveStatus.hidden, true, "old saved result must not claim the edited draft is saved");
  ui.elements.downloadAnswer.click();
  assert.equal(ui.downloads.at(-1).value.circles[0].x, 222.25);
});

check("failed ACK unfreezes, shows no-overwrite error, and a new click retries with a new nonce", () => {
  const ui = loaded();
  ui.draw();
  ui.elements.saveAnswer.click();
  const first = ui.events().at(-1);
  const failure = {nonce: first.save_nonce, revision: first.revision, image_id: first.image_id,
    ok: false, error: "existing run cannot be overwritten"};
  ack(ui, first, failure);
  assert.equal(ui.elements.saveAnswer.disabled, false);
  assert.equal(ui.elements.centerX.disabled, false);
  assert.equal(ui.elements.saveStatus.hidden, true);
  assert.equal(ui.elements.saveError.hidden, false);
  assert.match(ui.elements.saveError.textContent, /overwritten/);
  ui.elements.saveAnswer.click();
  const second = ui.events().at(-1);
  assert.notEqual(second.save_nonce, first.save_nonce);
  assert.equal(second.revision, first.revision);
  assert.deepEqual(second.circles, first.circles);
  ack(ui, second, failure); // Old failed nonce must not settle the new pending click.
  assert.equal(ui.elements.saveAnswer.disabled, true);
  assert.equal(ui.elements.saveError.hidden, true);
  ack(ui, second, success(second));
  assert.equal(ui.elements.saveAnswer.disabled, false);
  assert.equal(ui.elements.saveError.hidden, true);
  assert.equal(ui.elements.saveStatus.hidden, false);
});

check("old render and unrelated ACK preserve pending snapshot and cannot unlock editing", () => {
  const ui = loaded();
  ui.draw(180, 190, 30);
  ui.elements.saveAnswer.click();
  const request = ui.events().at(-1);
  ui.render({...initial, save_result: success(request, {nonce: "unrelated-old-click"})});
  assert.equal(ui.elements.saveAnswer.disabled, true);
  assert.equal(ui.elements.centerX.disabled, true);
  assert.equal(ui.elements.saveStatus.hidden, true);
  ui.elements.downloadAnswer.click();
  assert.equal(ui.downloads.at(-1).value.circles[0].x, 180);
  ack(ui, request, success(request));
  assert.equal(ui.elements.saveAnswer.disabled, false);
  assert.equal(ui.elements.saveStatus.hidden, false);
});

check("switching image or session discards pending controls and isolates saved status", () => {
  const ui = loaded();
  ui.draw(90, 100, 15);
  ui.elements.saveAnswer.click();
  const requestA = ui.events().at(-1);
  const imageB = {...initial, image_id: "image_b", data_kind: "synthetic", image_url: "data:image/png;base64,b"};
  ui.render(imageB);
  assert.equal(ui.elements.downloadAnswer.disabled, true);
  ui.images.at(-1).onload();
  assert.equal(ui.elements.saveAnswer.disabled, false);
  assert.equal(ui.elements.saveStatus.hidden, true);
  ui.elements.downloadAnswer.click();
  assert.deepEqual(ui.downloads.at(-1).value.circles, []);
  assert.equal(ui.downloads.at(-1).value.image_id, "image_b");
  assert.equal(ui.downloads.at(-1).value.data_kind, "synthetic");
  ui.render({...initial, revision: requestA.revision, circles: requestA.circles,
    save_result: success(requestA)});
  ui.images.at(-1).onload();
  assert.equal(ui.elements.saveStatus.hidden, false);
  ui.render({...initial, session_token: "new-session"});
  ui.images.at(-1).onload();
  assert.equal(ui.elements.saveStatus.hidden, true);
  assert.equal(ui.elements.saveAnswer.disabled, false);
});

check("unloaded image and active drag cannot save; rejected numeric input never enters saved snapshot", () => {
  const ui = boot();
  ui.render(initial);
  ui.elements.saveAnswer.onclick();
  assert.equal(ui.events().length, 0);
  ui.images.at(-1).onload();
  ui.canvas.emit("pointerdown", {button: 0, pointerId: 1,
    clientX: ui.rect.left + 100, clientY: ui.rect.top + 100});
  ui.elements.saveAnswer.onclick();
  assert.equal(ui.events().length, 0);
  ui.canvas.emit("pointercancel", {pointerId: 1});
  ui.draw(120, 130, 10);
  const before = ui.events().at(-1);
  ui.edit("NaN");
  assert.match(ui.elements.error.textContent, /hữu hạn/);
  assert.deepEqual(ui.events().at(-1), before);
  ui.elements.saveAnswer.click();
  assert.deepEqual(ui.events().at(-1).circles, before.circles);
});


check("a result for another image is hidden even when its revision matches", () => {
  const ui = loaded();
  ui.draw(123, 145, 17);
  const draft = ui.events().at(-1);
  const request = {...draft, save_nonce: "foreign-result"};
  for (const result of [success(request, {image_id: "image_b"}),
                        {nonce: "foreign-result", revision: draft.revision, image_id: "image_b",
                         ok: false, error: "failure belongs to another image"}]) {
    ack(ui, request, result);
    assert.equal(ui.elements.saveStatus.hidden, true);
    assert.equal(ui.elements.saveError.hidden, true);
    ui.elements.downloadAnswer.click();
    assert.equal(ui.downloads.at(-1).value.image_id, "image_a");
    assert.equal(ui.downloads.at(-1).value.circles[0].x, 123);
  }
});

console.log("Canvas save acceptance checks passed (" + checks + " scenarios)");
