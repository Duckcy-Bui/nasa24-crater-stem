"use strict";

// Independent R2 checks with the actual component scripts and DOM IDs.
// These deterministic mocks verify geometry/state/protocol, not browser layout.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const component = path.join(__dirname, "../src/crater_canvas");
const html = fs.readFileSync(path.join(component, "index.html"), "utf8");
const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]);
const near = (actual, expected, message = "") => assert.ok(Math.abs(actual - expected) < 1e-9,
  `${message}: expected ${expected}, got ${actual}`);

function boot(circles = [], options = {}) {
  const messages = [], images = [], downloads = [], blobs = new Map(), calls = [], properties = {};
  const windowHandlers = {}, documentHandlers = {}, registered = [];
  let nonce = 0, document;
  class Element {
    constructor(tag = "div") {
      this.tagName = tag.toUpperCase(); this.attributes = {}; this.children = [];
      this.handlers = {}; this.disabled = false; this.hidden = false; this.value = "";
      this.textContent = ""; this.style = {}; this.dataset = {}; this.parentElement = {dataset: {}};
      const classes = new Set();
      this.classList = {add: (...names) => names.forEach(name => classes.add(name)),
        remove: (...names) => names.forEach(name => classes.delete(name)),
        toggle: (name, force) => {const enabled = force ?? !classes.has(name); if (enabled) classes.add(name); else classes.delete(name); return enabled;},
        contains: name => classes.has(name)};
    }
    set value(value) { this._value = String(value); }
    get value() { return this._value; }
    setAttribute(key, value) { this.attributes[key] = String(value); }
    getAttribute(key) { return this.attributes[key] ?? null; }
    addEventListener(name, handler, settings) {
      (this.handlers[name] ??= []).push(handler); registered.push({element: this, name, settings});
    }
    removeEventListener(name, handler) { this.handlers[name] = (this.handlers[name] || []).filter(item => item !== handler); }
    replaceChildren(...children) { this.children = children; }
    append(...children) { this.children.push(...children); }
    remove() {}
    focus() { document.activeElement = this; }
    click() {
      if (this.disabled) return;
      if (this.download) downloads.push({filename: this.download, value: JSON.parse(blobs.get(this.href).parts.join(""))});
      else this.onclick?.();
    }
    emit(name, values = {}) {
      const event = {target: this, currentTarget: this, defaultPrevented: false,
        preventDefault() { this.defaultPrevented = true; }, stopPropagation() {}, ...values};
      for (const handler of this.handlers[name] || []) handler(event);
      return event;
    }
  }
  const elements = Object.fromEntries(ids.map(id => [id, new Element()]));
  const canvas = elements.craterCanvas, captures = new Set();
  const rect = {left: 17, top: 31, width: options.width || 512, height: options.width || 512};
  const ctx = new Proxy(properties, {
    get(target, key) { return key in target ? target[key] : (...args) => {calls.push({name: key, args,
      lineWidth: target.lineWidth, font: target.font, imageSmoothingEnabled: target.imageSmoothingEnabled});}; },
    set(target, key, value) { target[key] = value; return true; },
  });
  canvas.getContext = () => ctx;
  canvas.getBoundingClientRect = () => rect;
  canvas.setPointerCapture = id => captures.add(id);
  canvas.hasPointerCapture = id => captures.has(id);
  canvas.releasePointerCapture = id => captures.delete(id);
  if (elements.canvasWrap) elements.canvasWrap.getBoundingClientRect = () => rect;
  const parent = {postMessage: value => messages.push(value)};
  const window = {parent, crypto: {randomUUID: () => "zoom-save-" + (++nonce)},
    devicePixelRatio: options.dpr || 1,
    addEventListener: (name, handler) => {(windowHandlers[name] ??= []).push(handler);},
    removeEventListener() {}, requestAnimationFrame: callback => {callback(); return 0;}};
  const body = new Element("body"); body.getBoundingClientRect = () => ({height: 900});
  document = {getElementById: id => elements[id] ?? null, createElement: tag => new Element(tag),
    body, activeElement: body,
    addEventListener: (name, handler) => {(documentHandlers[name] ??= []).push(handler);}};
  const context = {window, document, devicePixelRatio: window.devicePixelRatio,
    Image: class {constructor() {images.push(this);}}, ResizeObserver: class {observe() {}},
    Blob: class {constructor(parts) {this.parts = parts;}},
    URL: {createObjectURL(blob) {const id = "blob:zoom-" + blobs.size; blobs.set(id, blob); return id;},
      revokeObjectURL(id) {blobs.delete(id);}},
    setTimeout: () => 0, requestAnimationFrame: window.requestAnimationFrame,
  };
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(path.join(component, "geometry.js"), "utf8"), context);
  context.CraterGeometry = window.CraterGeometry;
  vm.runInContext(fs.readFileSync(path.join(component, "canvas.js"), "utf8"), context);
  const initial = {image_id: "zoom_demo", data_kind: "real", session_token: "zoom-session", revision: 0,
    circles, image_url: "data:image/png;base64,test", save_result: null};
  function render(args = {}) {
    for (const handler of windowHandlers.message || []) handler({source: parent,
      data: {type: "streamlit:render", args: {...initial, ...args}}});
  }
  render(); images.at(-1).onload();
  const events = () => messages.filter(message => message.type === "streamlit:setComponentValue")
    .map(message => JSON.parse(JSON.stringify(message.value)));
  const view = () => {
    const draw = calls.filter(call => call.name === "drawImage").at(-1);
    assert.ok(draw, "image must be painted");
    if (draw.args.length === 5) return {z: 1, x: 0, y: 0};
    assert.equal(draw.args.length, 9, "zoom uses the image source crop, never CSS scaling of labels");
    return {x: draw.args[1], y: draw.args[2], z: 512 / draw.args[3]};
  };
  function pointer(type, x, y, id = 1, more = {}) {
    return canvas.emit(type, {button: 0, buttons: type === "pointerup" ? 0 : 1, pointerId: id,
      pointerType: "mouse", clientX: rect.left + x, clientY: rect.top + y, ...more});
  }
  function draw(x, y, radius) {
    pointer("pointerdown", x, y); pointer("pointermove", x + radius, y); pointer("pointerup", x + radius, y);
  }
  function pan(dx, dy, more = {}) {
    pointer("pointerdown", rect.width / 2, rect.height / 2, 1, more);
    pointer("pointermove", rect.width / 2 + dx, rect.height / 2 + dy, 1, more);
    pointer("pointerup", rect.width / 2 + dx, rect.height / 2 + dy, 1, more);
  }
  function pinch(factor = 4) {
    const cx = rect.width / 2, cy = rect.height / 2, half = rect.width / 10;
    pointer("pointerdown", cx - half, cy, 10, {pointerType: "touch"});
    pointer("pointerdown", cx + half, cy, 11, {pointerType: "touch"});
    pointer("pointermove", cx - half * factor, cy, 10, {pointerType: "touch"});
    pointer("pointermove", cx + half * factor, cy, 11, {pointerType: "touch"});
    pointer("pointerup", cx - half * factor, cy, 10, {pointerType: "touch"});
    pointer("pointerup", cx + half * factor, cy, 11, {pointerType: "touch"});
  }
  function download() {elements.downloadAnswer.click(); return downloads.at(-1).value;}
  return {elements, canvas, rect, ctx, calls, properties, initial, events, render, images,
    view, pointer, draw, pan, pinch, download, registered, windowHandlers, documentHandlers};
}
let checks = 0;
function check(name, run) {run(); checks++; console.log("ok - " + name);}
function assertView(ui, expected) {const actual = ui.view(); for (const key of ["z", "x", "y"]) near(actual[key], expected[key], key);}
function assertPlainSnapshot(snapshot) {
  assert.equal("view" in snapshot, false); assert.equal("zoom" in snapshot, false);
  for (const circle of snapshot.circles) assert.equal("view" in circle, false);
}

check("actual DOM has accessible local zoom controls and a focusable canvas", () => {
  for (const id of ["panMode", "zoomOut", "zoomIn", "zoomFit", "zoomLevel"]) assert.ok(ids.includes(id), id);
  assert.match(html, /<output\b[^>]*id="zoomLevel"[^>]*aria-live="polite"|<output\b[^>]*aria-live="polite"[^>]*id="zoomLevel"/);
  assert.match(html, /<canvas\b[^>]*tabindex="0"/i);
});
check("wheel is non-passive, anchored under the cursor, bounded, and view-only", () => {
  const ui = boot(), registration = ui.registered.find(item => item.element === ui.canvas && item.name === "wheel");
  assert.ok(registration, "canvas wheel listener exists"); assert.equal(registration.settings?.passive, false);
  assert.equal(ui.elements.zoomOut.disabled, true); assert.equal(ui.elements.zoomFit.disabled, true);
  const event = ui.canvas.emit("wheel", {deltaY: -100, clientX: ui.rect.left + 128, clientY: ui.rect.top + 384});
  assert.equal(event.defaultPrevented, true);
  assertView(ui, {z: 1.25, x: 25.6, y: 76.8});
  assert.equal(ui.events().length, 0); assert.equal(ui.elements.undo.disabled, true);
  for (let i = 0; i < 30; i++) ui.elements.zoomIn.click();
  near(ui.view().z, 8); assert.equal(ui.elements.zoomIn.disabled, true);
  for (let i = 0; i < 30; i++) ui.elements.zoomOut.click();
  assertView(ui, {z: 1, x: 0, y: 0}); assert.equal(ui.elements.zoomOut.disabled, true);
  assert.equal(ui.events().length, 0);
});
check("pinch to exact 4x and pan yield original-image draw, JSON and nonce save coordinates", () => {
  const ui = boot(); ui.pinch(4); assertView(ui, {z: 4, x: 192, y: 192});
  ui.elements.panMode.click(); ui.pan(-128, -64); assertView(ui, {z: 4, x: 224, y: 208});
  assert.equal(ui.events().length, 0, "touch starts and pans do not commit a ghost ring");
  // Screen (144, 128) at 4x over view (224, 208) is pixel edge (260, 240), i.e. centre coordinate (259.5, 239.5).
  ui.elements.drawMode.click(); ui.draw(144, 128, 20);
  const circle = {crater_id: "U1", x: 259.5, y: 239.5, r: 5};
  assert.deepEqual(ui.events().at(-1).circles, [circle]); assert.equal(ui.events().at(-1).revision, 1);
  const downloaded = ui.download(); assertPlainSnapshot(downloaded);
  assert.deepEqual(downloaded.circles, [{...circle, confidence: null, votes: null}]);
  ui.elements.saveAnswer.click(); const saved = ui.events().at(-1); assertPlainSnapshot(saved);
  assert.deepEqual(saved.circles, [circle]); assert.equal(saved.revision, 1); assert.match(saved.save_nonce, /^zoom-save-/);
});
check("tiny radius-3 ring is picked and moved at 8x with screen-space tolerance", () => {
  const tiny = {crater_id: "U1", x: 256, y: 256, r: 3};
  const ui = boot([tiny]); ui.pinch(8); assertView(ui, {z: 8, x: 224, y: 224});
  ui.elements.editMode.click(); ui.pointer("pointerdown", 256, 256); ui.pointer("pointermove", 272, 264); ui.pointer("pointerup", 272, 264);
  assert.deepEqual(ui.events().at(-1).circles, [{...tiny, x: 258, y: 257}]);
});
check("zoom and pan do not enter undo history or change revision or persisted schema", () => {
  const ui = boot(); ui.draw(120, 130, 20); assert.equal(ui.events().length, 1);
  ui.pinch(4); ui.elements.panMode.click(); ui.pan(-400, -100);
  assert.equal(ui.events().length, 1); assertPlainSnapshot(ui.download());
  ui.elements.undo.click(); assert.equal(ui.events().length, 2);
  assert.equal(ui.events().at(-1).revision, 2); assert.deepEqual(ui.events().at(-1).circles, []);
  near(ui.view().z, 4, "Undo must not undo zoom"); assert.equal(ui.elements.undo.disabled, true);
});
check("ordinary Python ACK preserves the view while the event contract excludes view state", () => {
  const ui = boot(); ui.draw(200, 220, 30); const draft = ui.events().at(-1);
  ui.pinch(4); ui.elements.panMode.click(); ui.pan(-64, -32);
  const savedView = ui.view(); ui.render({revision: draft.revision, circles: draft.circles});
  assertView(ui, savedView); assert.equal(ui.events().length, 1);
  ui.elements.saveAnswer.click(); const save = ui.events().at(-1);
  assert.deepEqual(Object.keys(save).sort(), ["circles", "image_id", "revision", "save_nonce", "session_token"]);
  assert.equal(save.revision, draft.revision); assert.deepEqual(save.circles, draft.circles);
  ui.render({revision: save.revision, circles: save.circles, save_result: {
    nonce: save.save_nonce, revision: save.revision, image_id: save.image_id, ok: true,
    count: 1, time: "20:00", path: "outputs/player_answers/zoom-run"}});
  assertView(ui, savedView); assert.equal(ui.elements.saveStatus.hidden, false);
});
check("pan clamps to image bounds, fit returns full image, and image/session switch resets view", () => {
  const ui = boot(); ui.pinch(4); ui.elements.panMode.click();
  ui.pan(-10000, -10000); assertView(ui, {z: 4, x: 384, y: 384});
  ui.pan(10000, 10000); assertView(ui, {z: 4, x: 0, y: 0});
  ui.elements.zoomFit.click(); assertView(ui, {z: 1, x: 0, y: 0});
  ui.pan(-100, -100); assertView(ui, {z: 1, x: 0, y: 0});
  ui.pinch(4); ui.render({image_id: "another-image", image_url: "data:image/png;base64,other"});
  ui.images.at(-1).onload(); assertView(ui, {z: 1, x: 0, y: 0});
  ui.pinch(4); ui.render({image_id: "another-image", session_token: "another-session"});
  ui.images.at(-1).onload(); assertView(ui, {z: 1, x: 0, y: 0});
  assert.equal(ui.events().length, 0);
});
check("keyboard zoom is local; Space and middle-button pan are temporary without changing draw mode", () => {
  const ui = boot();
  assert.equal((ui.windowHandlers.keydown || []).length, 0, "no global window keyboard shortcuts");
  assert.equal((ui.documentHandlers.keydown || []).length, 0, "no global document keyboard shortcuts");
  ui.canvas.focus(); const event = ui.canvas.emit("keydown", {key: "+", code: "Equal"});
  assert.equal(event.defaultPrevented, true); near(ui.view().z, 1.25);
  ui.canvas.emit("keydown", {key: "0", code: "Digit0"}); assertView(ui, {z: 1, x: 0, y: 0});
  ui.pinch(4); ui.canvas.emit("keydown", {key: " ", code: "Space"});
  ui.pan(-128, -64); ui.canvas.emit("keyup", {key: " ", code: "Space"});
  assertView(ui, {z: 4, x: 224, y: 208});
  ui.pan(64, 32, {button: 1, buttons: 4}); assertView(ui, {z: 4, x: 208, y: 200});
  assert.equal(ui.events().length, 0); ui.draw(192, 224, 20);
  assert.deepEqual(ui.events().at(-1).circles, [{crater_id: "U1", x: 255.5, y: 255.5, r: 5}]);
});
check("two-finger movement pans and pointercancel rolls back an unfinished annotation", () => {
  const ui = boot(); ui.pinch(4);
  ui.pointer("pointerdown", 200, 256, 10, {pointerType: "touch"});
  ui.pointer("pointerdown", 300, 256, 11, {pointerType: "touch"});
  ui.pointer("pointermove", 160, 236, 10, {pointerType: "touch"});
  ui.pointer("pointermove", 260, 236, 11, {pointerType: "touch"});
  ui.pointer("pointerup", 160, 236, 10, {pointerType: "touch"});
  ui.pointer("pointerup", 260, 236, 11, {pointerType: "touch"});
  assertView(ui, {z: 4, x: 202, y: 197}); assert.equal(ui.events().length, 0);
  ui.pointer("pointerdown", 216, 236); ui.pointer("pointermove", 256, 236);
  ui.pointer("pointercancel", 256, 236); assert.equal(ui.events().length, 0); assert.deepEqual(ui.download().circles, []);
});
check("adding a second finger rolls back an unfinished circle edit before entering the view gesture", () => {
  const original = {crater_id: "U1", x: 256, y: 256, r: 20};
  const ui = boot([original]); ui.elements.editMode.click();
  ui.pointer("pointerdown", 256, 256, 10, {pointerType: "touch"});
  ui.pointer("pointermove", 266, 256, 10, {pointerType: "touch"});
  ui.pointer("pointerdown", 366, 256, 11, {pointerType: "touch"});
  ui.pointer("pointermove", 406, 256, 11, {pointerType: "touch"});
  ui.pointer("pointercancel", 266, 256, 10, {pointerType: "touch"});
  ui.pointer("pointerup", 406, 256, 11, {pointerType: "touch"});
  assert.equal(ui.events().length, 0);
  assert.deepEqual(ui.download().circles, [{...original, confidence: null, votes: null}]);
});
check("DPR backing store, label font, strokes and pixel smoothing use screen dimensions", () => {
  const ui = boot([{crater_id: "U1", x: 256, y: 256, r: 3}], {width: 358, dpr: 2});
  assert.equal(ui.canvas.width, 716); assert.equal(ui.canvas.height, 716);
  const before = ui.calls.filter(call => call.name === "fillText").at(-1);
  assert.match(before.font, /\b11px\b/);
  const beforeStroke = ui.calls.filter(call => call.name === "stroke").at(-1).lineWidth;
  ui.pinch(8);
  const after = ui.calls.filter(call => call.name === "fillText").at(-1);
  assert.equal(after.font, before.font);
  assert.equal(ui.calls.filter(call => call.name === "stroke").at(-1).lineWidth, beforeStroke);
  assert.equal(ui.properties.imageSmoothingEnabled, false);
  ui.elements.zoomFit.click(); assert.equal(ui.properties.imageSmoothingEnabled, true);
});
check("rings are painted around pixel centres at fit and when zoomed", () => {
  // Image x is the centre of pixel x, so on screen it sits (x + 0.5) image px from the visible edge.
  const ui = boot([{crater_id: "U1", x: 256, y: 200, r: 10}]);
  let arc = ui.calls.filter(call => call.name === "arc").at(-1);
  near(arc.args[0], 256.5, "fit x"); near(arc.args[1], 200.5, "fit y"); near(arc.args[2], 10, "fit radius");
  const before = ui.calls.length;
  ui.pinch(4); assertView(ui, {z: 4, x: 192, y: 192});
  arc = ui.calls.slice(before).filter(call => call.name === "arc").at(-1);
  near(arc.args[0], (256.5 - 192) * 4, "4x x"); near(arc.args[1], (200.5 - 192) * 4, "4x y"); near(arc.args[2], 40, "4x radius");
  const small = boot([{crater_id: "U1", x: 0, y: 511, r: 4}], {width: 358});
  arc = small.calls.filter(call => call.name === "arc").at(-1);
  near(arc.args[0], 0.5 * 358 / 512, "first pixel centre at 358 px"); near(arc.args[1], 511.5 * 358 / 512, "last pixel centre at 358 px");
});
console.log("Canvas zoom acceptance checks passed (" + checks + " scenarios)");
