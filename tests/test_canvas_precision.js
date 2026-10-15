"use strict";

// Numeric display regression checks using the real component scripts and DOM IDs.
// These deterministic mocks verify state/protocol behavior, not browser layout.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const component = path.join(__dirname, "../src/crater_canvas");
const html = fs.readFileSync(path.join(component, "index.html"), "utf8");
const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]);
const fields = {x: "centerX", y: "centerY", r: "radius"};

function boot(circle) {
  const messages = [], images = [], listeners = {}, downloads = [], blobs = new Map();
  class Element {
    constructor() {
      this.attributes = {}; this.children = []; this.handlers = {};
      this.disabled = false; this.hidden = false; this.value = "";
      this.textContent = ""; this.style = {}; this.dataset = {};
      this.parentElement = {dataset: {}};
    }
    set value(value) { this._value = String(value); }
    get value() { return this._value; }
    setAttribute(key, value) { this.attributes[key] = String(value); }
    getAttribute(key) { return this.attributes[key] ?? null; }
    addEventListener(name, handler) { this.handlers[name] = handler; }
    replaceChildren(...children) { this.children = children; }
    append(...children) { this.children.push(...children); }
    remove() {}
    click() {
      if (this.disabled) return;
      if (this.download) downloads.push({filename: this.download,
        value: JSON.parse(blobs.get(this.href).parts.join(""))});
      else this.onclick?.();
    }
    emit(name) { this.handlers[name]?.({preventDefault() {}}); }
  }
  const elements = Object.fromEntries(ids.map(id => [id, new Element()]));
  elements.craterCanvas.getContext = () => new Proxy({}, {get: () => () => {}});
  elements.craterCanvas.getBoundingClientRect = () => ({left: 0, top: 0, width: 512, height: 512});
  const parent = {postMessage: value => messages.push(value)};
  const window = {parent, crypto: {randomUUID: () => "precision-save-1"},
    addEventListener: (name, handler) => { listeners[name] = handler; }};
  const body = new Element();
  body.getBoundingClientRect = () => ({height: 800});
  const context = {
    window, document: {getElementById: id => elements[id] ?? null,
      createElement: () => new Element(), body},
    Image: class {constructor() { images.push(this); }},
    ResizeObserver: class {observe() {}},
    Blob: class {constructor(parts) { this.parts = parts; }},
    URL: {
      createObjectURL(blob) { const id = "blob:precision-" + blobs.size; blobs.set(id, blob); return id; },
      revokeObjectURL(id) { blobs.delete(id); },
    },
    setTimeout: () => 0,
  };
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(path.join(component, "geometry.js"), "utf8"), context);
  context.CraterGeometry = window.CraterGeometry;
  vm.runInContext(fs.readFileSync(path.join(component, "canvas.js"), "utf8"), context);
  const args = {image_id: "precision_demo", data_kind: "real", session_token: "precision-session",
    revision: 7, circles: [circle], image_url: "data:image/png;base64,test", save_result: null};
  listeners.message({source: parent, data: {type: "streamlit:render", args}});
  images.at(-1).onload();
  elements.circles.children[0].click();
  const events = () => messages.filter(message => message.type === "streamlit:setComponentValue")
    .map(message => JSON.parse(JSON.stringify(message.value)));
  const apply = () => elements.editor.emit("submit");
  function download() { elements.downloadAnswer.click(); return downloads.at(-1); }
  function save() { elements.saveAnswer.click(); return events().at(-1); }
  return {elements, args, events, apply, download, save};
}

// Deliberately non-rounded interaction fixture; not scientific crater labels.
const original = {crater_id: "U1", x: 178.304057816, y: 211.786537291, r: 31.525366917};
function assertDownload(ui, circle) {
  assert.deepEqual(ui.download(), {filename: "precision_demo_player.json", value: {
    schema_version: "1.0", data_kind: "real", image_id: "precision_demo", source: "player",
    reference_source: null, circles: [{...circle, confidence: null, votes: null}],
  }});
}
function assertSave(ui, circle, revision) {
  const request = ui.save();
  assert.deepEqual(request, {image_id: "precision_demo", session_token: "precision-session",
    revision, circles: [circle], save_nonce: "precision-save-1"});
}
let checks = 0;
function check(name, body) { body(); checks += 1; console.log("ok - " + name); }

check("two-decimal inputs and list are display-only; unchanged Apply preserves full precision", () => {
  const ui = boot(original);
  for (const [key, id] of Object.entries(fields)) {
    assert.equal(ui.elements[id].value, original[key].toFixed(2));
  }
  assert.deepEqual(ui.elements.circles.children[0].children.map(cell => cell.textContent),
    ["U1", "178.30", "211.79", "31.53"]);
  ui.apply(); ui.apply();
  assert.equal(ui.events().length, 0, "unchanged Apply cannot create a rounded draft or history entry");
  assertDownload(ui, original);
  assertSave(ui, original, 7);
});

for (const [key, id] of Object.entries(fields)) {
  check("editing only " + key + " preserves untouched full-precision values in download and save", () => {
    const ui = boot(original), changed = {...original, [key]: 123.456789125};
    ui.elements[id].value = "123.456789125";
    ui.apply();
    assert.equal(ui.events().length, 1);
    assert.deepEqual(ui.events()[0].circles, [changed]);
    assert.equal(ui.events()[0].revision, 8);
    assert.equal(ui.elements[id].value, "123.46");
    ui.apply();
    assert.equal(ui.events().length, 1, "the rounded display after commit must remain a no-op");
    assertDownload(ui, changed);
    assertSave(ui, changed, 8);
    assert.equal(ui.events().length, 2, "Save adds a nonce, not another numeric mutation");
  });
}

check("valid sub-centipixel radius survives displayed 0.00 and editing another field", () => {
  const tiny = {...original, x: 510.999999999, y: 0.000000003, r: 0.004};
  const ui = boot(tiny);
  assert.equal(ui.elements.centerX.value, "511.00");
  assert.equal(ui.elements.centerY.value, "0.00");
  assert.equal(ui.elements.radius.value, "0.00");
  ui.apply();
  assert.equal(ui.events().length, 0);
  assert.equal(ui.elements.radius.getAttribute("aria-invalid"), "false",
    "validation must use the original positive radius when its display is unchanged");
  ui.elements.centerX.value = "500.123456789";
  ui.apply();
  const changed = {...tiny, x: 500.123456789};
  assert.deepEqual(ui.events()[0].circles, [changed]);
  assertDownload(ui, changed);
  assertSave(ui, changed, 8);
});

check("a deliberately changed string is parsed even if numerically equal to the displayed value", () => {
  const ui = boot(original), changed = {...original, x: 178.3};
  ui.elements.centerX.value = "178.3";
  ui.apply();
  assert.deepEqual(ui.events()[0].circles, [changed]);
  assertDownload(ui, changed);
  assertSave(ui, changed, 8);
});

const invalidInputs = [
  ["x", ""], ["x", "NaN"], ["x", "Infinity"], ["x", "-0.01"], ["x", "511.01"],
  ["y", "512"], ["r", "0"], ["r", "-0.004"], ["r", "Infinity"], ["r", "   "],
];
for (const [key, value] of invalidInputs) {
  check("invalid " + key + "=" + JSON.stringify(value) + " rejects atomically without rounding other fields", () => {
    const ui = boot(original), id = fields[key];
    ui.elements[id].value = value;
    ui.apply();
    assert.equal(ui.events().length, 0);
    assert.equal(ui.elements[id].getAttribute("aria-invalid"), "true");
    assert.equal(ui.elements[id].parentElement.dataset.invalid, "true");
    assert.match(ui.elements.error.textContent, /hữu hạn/);
    assertDownload(ui, original);
    assertSave(ui, original, 7);
  });
}

check("one invalid field rejects all edits; correcting it preserves the other untouched original", () => {
  const ui = boot(original);
  ui.elements.centerX.value = "600";
  ui.elements.centerY.value = "100.123456789";
  ui.apply();
  assert.equal(ui.events().length, 0);
  assertDownload(ui, original);
  ui.elements.centerX.value = "178.30";
  ui.apply();
  const changed = {...original, y: 100.123456789};
  assert.deepEqual(ui.events()[0].circles, [changed]);
  assert.equal(ui.elements.centerX.getAttribute("aria-invalid"), "false");
  assert.equal(ui.elements.error.textContent, "");
  assertDownload(ui, changed);
  assertSave(ui, changed, 8);
});

check("Undo restores original precision and a subsequent unchanged Apply remains a no-op", () => {
  const ui = boot(original);
  ui.elements.radius.value = "40.123456789";
  ui.apply();
  ui.elements.undo.click();
  assert.equal(ui.events().length, 2);
  assert.deepEqual(ui.events().at(-1).circles, [original]);
  ui.apply();
  assert.equal(ui.events().length, 2);
  assertDownload(ui, original);
  assertSave(ui, original, 9);
});

console.log("Canvas precision acceptance checks passed (" + checks + " scenarios)");
