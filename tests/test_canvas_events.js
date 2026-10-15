"use strict";

// Deterministic event regressions. These do not replace the real browser checks.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function boot() {
  const messages = [], images = [], listeners = {}, downloads = [], blobs = new Map();
  const elements = {};
  class Element {
    constructor() { this.attributes = {}; this.children = []; this.handlers = {}; this.value = ""; }
    set value(value) { this._value = String(value); }
    get value() { return this._value; }
    setAttribute(key, value) { this.attributes[key] = String(value); }
    addEventListener(name, handler) { this.handlers[name] = handler; }
    replaceChildren() { this.children = []; }
    append(child) { this.children.push(child); }
    click() {
      if (this.download) downloads.push({filename: this.download, value: JSON.parse(blobs.get(this.href).parts.join(""))});
      else this.onclick?.();
    }
    remove() {}
    emit(name, event = {}) { this.handlers[name]?.({preventDefault() {}, ...event}); }
  }
  for (const id of ["craterCanvas", "drawMode", "editMode", "deleteCircle", "undo", "status", "centerX", "centerY", "radius", "applyEdit", "error", "circles", "editor", "downloadAnswer"]) elements[id] = new Element();
  const canvas = elements.craterCanvas, captures = new Set();
  canvas.getContext = () => new Proxy({}, {get: () => () => {}});
  canvas.getBoundingClientRect = () => ({left: 0, top: 0, width: 512, height: 512});
  canvas.setPointerCapture = id => captures.add(id);
  canvas.hasPointerCapture = id => captures.has(id);
  canvas.releasePointerCapture = id => captures.delete(id);
  const parent = {postMessage: value => messages.push(value)};
  const window = {parent, addEventListener: (name, handler) => {listeners[name] = handler;}};
  const body = new Element();
  body.scrollHeight = 800;
  body.getBoundingClientRect = () => ({height: 800});
  const context = {
    window,
    document: {getElementById: id => elements[id], createElement: () => new Element(),
      body},
    Image: class {constructor() { images.push(this); }},
    ResizeObserver: class {observe() {}},
    Blob: class {constructor(parts, options) { this.parts = parts; this.type = options.type; }},
    URL: {
      createObjectURL(blob) { const id = `blob:test-${blobs.size}`; blobs.set(id, blob); return id; },
      revokeObjectURL(id) { blobs.delete(id); },
    },
    setTimeout: () => 0,
  };
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(path.join(__dirname, "../src/crater_canvas/geometry.js"), "utf8"), context);
  context.CraterGeometry = window.CraterGeometry;
  vm.runInContext(fs.readFileSync(path.join(__dirname, "../src/crater_canvas/canvas.js"), "utf8"), context);
  function render(args) { listeners.message({source: parent, data: {type: "streamlit:render", args}}); }
  function draw(x = 100, y = 100, r = 40) {
    canvas.emit("pointerdown", {button: 0, pointerId: 1, clientX: x, clientY: y});
    canvas.emit("pointermove", {pointerId: 1, clientX: x + r, clientY: y});
    canvas.emit("pointerup", {pointerId: 1, clientX: x + r, clientY: y});
  }
  const events = () => messages.filter(value => value.type === "streamlit:setComponentValue").map(value => JSON.parse(JSON.stringify(value.value)));
  return {elements, images, render, draw, events, downloads};
}

const args = {image_id: "image_a", data_kind: "real", session_token: "session_1", revision: 0, circles: [], image_url: "data:image/png;base64,a"};

// A delayed image callback cannot enable editing while a newer image is pending.
{
  const ui = boot();
  ui.render(args);
  const imageA = ui.images.at(-1);
  ui.render({...args, image_id: "image_b", image_url: "data:image/png;base64,b"});
  const imageB = ui.images.at(-1);
  imageA.onload();
  ui.draw();
  assert.equal(ui.events().length, 0, "stale image load must not enable drawing on the new image");
  imageB.onload();
  ui.draw(80, 90, 30);
  assert.equal(ui.events().length, 1);
  assert.equal(ui.events()[0].image_id, "image_b");
  assert.equal(ui.events()[0].circles[0].x, 80);
}

// A Streamlit acknowledgement may arrive while the player edits numeric fields.
{
  const ui = boot();
  ui.render(args);
  ui.images.at(-1).onload();
  ui.draw();
  const latest = ui.events().at(-1);
  ui.elements.centerX.value = "123.456789";
  ui.render({...args, revision: latest.revision, circles: latest.circles});
  assert.equal(ui.elements.centerX.value, "123.456789", "equal-revision ACK must preserve the unfinished numeric edit");
  ui.render(args);
  assert.equal(ui.elements.centerX.value, "123.456789", "older render must preserve the unfinished numeric edit");
  ui.elements.editor.emit("submit");
  assert.equal(ui.events().at(-1).circles[0].x, 123.456789);
}

// Undo/delete/edit generate newer full drafts without renumbering survivors.
{
  const ui = boot();
  ui.render(args);
  ui.images.at(-1).onload();
  ui.draw(100, 120, 20);
  ui.draw(300, 320, 30);
  assert.equal(ui.events().at(-1).revision, 2);
  ui.elements.deleteCircle.onclick();
  assert.deepEqual(ui.events().at(-1).circles.map(circle => circle.crater_id), ["U1"]);
  ui.elements.undo.onclick();
  assert.deepEqual(ui.events().at(-1).circles.map(circle => circle.crater_id), ["U1", "U2"]);
  assert.equal(ui.events().at(-1).revision, 4);
  ui.elements.circles.children[0].onclick();
  ui.elements.centerX.value = "255.5";
  ui.elements.centerY.value = "511";
  ui.elements.radius.value = "150";
  ui.elements.editor.emit("submit");
  const circle = ui.events().at(-1).circles[0];
  assert.deepEqual(circle, {crater_id: "U1", x: 255.5, y: 511, r: 150});
  assert.equal(ui.events().at(-1).revision, 5);
}

// Download reads the latest committed local draft before any server ACK arrives.
{
  const ui = boot();
  ui.render(args);
  ui.images.at(-1).onload();
  ui.draw(320, 120, 20);
  ui.elements.centerX.value = "300.5";
  ui.elements.editor.emit("submit");
  ui.elements.downloadAnswer.onclick();
  assert.equal(ui.downloads.length, 1);
  assert.deepEqual(ui.downloads[0], {
    filename: "image_a_player.json",
    value: {schema_version: "1.0", data_kind: "real", image_id: "image_a", source: "player", reference_source: null,
      circles: [{crater_id: "U1", x: 300.5, y: 120, r: 20, confidence: null, votes: null}]},
  });
  ui.elements.centerX.value = "NaN";
  ui.elements.editor.emit("submit");
  ui.elements.downloadAnswer.onclick();
  assert.equal(ui.downloads.at(-1).value.circles[0].x, 300.5, "rejected numeric input must not corrupt the exported draft");

  ui.render({...args, image_id: "image_b", data_kind: "synthetic", image_url: "data:image/png;base64,b"});
  ui.images.at(-1).onload();
  ui.elements.downloadAnswer.onclick();
  assert.deepEqual(ui.downloads.at(-1), {
    filename: "image_b_player.json",
    value: {schema_version: "1.0", data_kind: "synthetic", image_id: "image_b", source: "player", reference_source: null, circles: []},
  });
}

// Small circles must be movable by their centre even within the rim tolerance.
{
  const ui = boot();
  ui.render(args);
  ui.images.at(-1).onload();
  ui.draw(200, 201, 1);
  ui.elements.editMode.onclick();
  ui.draw(200, 201, 40);
  const circle = ui.events().at(-1).circles[0];
  assert.equal(circle.x, 240);
  assert.equal(circle.y, 201);
  assert.equal(circle.r, 1, "moving a small circle cannot accidentally resize it");
}

// The explicitly selected circle retains edit priority when circles overlap.
{
  const ui = boot();
  ui.render(args);
  ui.images.at(-1).onload();
  ui.draw(100, 120, 40);
  ui.draw(100, 120, 20);
  ui.elements.circles.children[0].onclick();
  ui.draw(100, 120, 30);
  let circles = ui.events().at(-1).circles;
  assert.deepEqual(circles[0], {crater_id: "U1", x: 130, y: 120, r: 40});
  assert.deepEqual(circles[1], {crater_id: "U2", x: 100, y: 120, r: 20});
  ui.draw(170, 120, 20);
  circles = ui.events().at(-1).circles;
  assert.deepEqual(circles[0], {crater_id: "U1", x: 130, y: 120, r: 60});
  assert.deepEqual(circles[1], {crater_id: "U2", x: 100, y: 120, r: 20});
}

console.log("Canvas event acceptance checks passed");
