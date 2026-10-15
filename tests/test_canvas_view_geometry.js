"use strict";

// Independent algebraic oracles for viewport transforms. The old geometry APIs
// remain covered by test_canvas_geometry.js, without changing their contracts.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const context = {window: {}};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname, "../src/crater_canvas/geometry.js"), "utf8"), context);
const geometry = context.window.CraterGeometry;
let checks = 0;

function near(actual, expected, message) {
  assert.ok(Math.abs(actual - expected) < 1e-9, `${message}: expected ${expected}, received ${actual}`);
  checks += 1;
}
function viewNear(actual, expected, message) {
  for (const axis of ["z", "x", "y"]) near(actual[axis], expected[axis], `${message} ${axis}`);
}
function invalid(action) {
  assert.throws(action, /không hợp lệ/);
  checks += 1;
}

// Nonzero offsets at 1x are deliberately allowed in conversion functions: they
// are affine transforms, whereas clampView enforces the visible-image bounds.
for (const z of [1, 2.5, 8]) {
  const view = {z, x: 23.125, y: 57.375};
  for (const display of [358, 512, 840]) {
    const rect = {left: 37.25, top: 61.5, width: display, height: display};
    for (const point of [{x: 0, y: 0}, {x: 127.625, y: 333.125}, {x: 511, y: 511}, {x: -8.75, y: 600.5}]) {
      const screen = geometry.imageToScreen(point.x, point.y, rect, view);
      near(screen.x, rect.left + (point.x - view.x) * display * z / 512, `forward x ${z}x at ${display}`);
      near(screen.y, rect.top + (point.y - view.y) * display * z / 512, `forward y ${z}x at ${display}`);
      const restored = geometry.screenToImage(screen.x, screen.y, rect, view);
      near(restored.x, point.x, `roundtrip image x ${z}x at ${display}`);
      near(restored.y, point.y, `roundtrip image y ${z}x at ${display}`);
    }
    for (const point of [{x: -33.5, y: -12.75}, {x: rect.left + display / 4, y: rect.top + display * 3 / 4}, {x: 2048.125, y: 2048.75}]) {
      const image = geometry.screenToImage(point.x, point.y, rect, view);
      const restored = geometry.imageToScreen(image.x, image.y, rect, view);
      near(restored.x, point.x, `roundtrip screen x ${z}x at ${display}`);
      near(restored.y, point.y, `roundtrip screen y ${z}x at ${display}`);
    }
  }
}

// A non-square viewport and custom source dimensions need separate axis scales.
const customRect = {left: 10, top: 20, width: 640, height: 360};
const customView = {z: 2.5, x: 100, y: 200};
const customPoint = geometry.screenToImage(330, 290, customRect, customView, 1024, 768);
near(customPoint.x, 304.8, "custom source width and viewport width");
near(customPoint.y, 430.4, "custom source height and viewport height");
const customRestored = geometry.imageToScreen(customPoint.x, customPoint.y, customRect, customView, 1024, 768);
near(customRestored.x, 330, "custom x roundtrip");
near(customRestored.y, 290, "custom y roundtrip");

viewNear(geometry.clampView({z: 1, x: 200, y: -5}), {z: 1, x: 0, y: 0}, "fit frame has no translation");
viewNear(geometry.clampView({z: 0.25, x: 200, y: 200}), {z: 1, x: 0, y: 0}, "zoom lower limit");
viewNear(geometry.clampView({z: 20, x: 600, y: 700}), {z: 8, x: 448, y: 448}, "zoom upper limit and bottom right bounds");
viewNear(geometry.clampView({z: 4, x: -1, y: -99}), {z: 4, x: 0, y: 0}, "top left bounds");
viewNear(geometry.clampView({z: 2.5, x: 500, y: 500}), {z: 2.5, x: 307.2, y: 307.2}, "fractional zoom bounds");
viewNear(geometry.clampView({z: 4, x: 1000, y: 1000}, 1024, 768), {z: 4, x: 768, y: 576}, "custom source bounds");

const rect = {left: 30, top: 70, width: 840, height: 840};
for (const anchor of [{x: 240, y: 490}, {x: 660, y: 280}]) {
  const original = {z: 2, x: 80, y: 96};
  const before = geometry.screenToImage(anchor.x, anchor.y, rect, original);
  const zoomed = geometry.zoomViewAt(original, 4, anchor.x, anchor.y, rect);
  const after = geometry.screenToImage(anchor.x, anchor.y, rect, zoomed);
  near(after.x, before.x, "zoom in preserves pointer image x");
  near(after.y, before.y, "zoom in preserves pointer image y");
  viewNear(geometry.zoomViewAt(zoomed, 2, anchor.x, anchor.y, rect), original, "zoom in and out reversibility away from boundaries");
}

// Known edge anchors both exercise clamping and avoid accidental pan drift.
viewNear(geometry.zoomViewAt({z: 1, x: 0, y: 0}, 8, rect.left, rect.top, rect), {z: 8, x: 0, y: 0}, "top left pointer anchor");
viewNear(geometry.zoomViewAt({z: 1, x: 0, y: 0}, 8, rect.left + rect.width, rect.top + rect.height, rect), {z: 8, x: 448, y: 448}, "bottom right pointer anchor");
viewNear(geometry.zoomViewAt({z: 8, x: 448, y: 448}, -3, rect.left + 200, rect.top + 100, rect), {z: 1, x: 0, y: 0}, "fit frame clamps out of bounds offset");
viewNear(geometry.zoomViewAt({z: 1, x: 0, y: 0}, 100, rect.left + 420, rect.top + 420, rect), {z: 8, x: 224, y: 224}, "new zoom upper limit");
const untouched = {z: 4, x: 33, y: 44};
geometry.clampView(untouched);
geometry.zoomViewAt(untouched, 8, 120, 200, rect);
assert.deepEqual(untouched, {z: 4, x: 33, y: 44});
checks += 1;

for (const value of [NaN, Infinity, -Infinity]) {
  invalid(() => geometry.clampView({z: value, x: 0, y: 0}));
  invalid(() => geometry.clampView({z: 1, x: value, y: 0}));
  invalid(() => geometry.clampView({z: 1, x: 0, y: value}));
  invalid(() => geometry.screenToImage(value, 0, rect, {z: 1, x: 0, y: 0}));
  invalid(() => geometry.imageToScreen(0, value, rect, {z: 1, x: 0, y: 0}));
  invalid(() => geometry.zoomViewAt({z: 1, x: 0, y: 0}, value, 120, 200, rect));
}
for (const badView of [null, {}, {z: 0, x: 0, y: 0}, {z: 9, x: 0, y: 0}, {z: 2, x: Infinity, y: 0}]) {
  invalid(() => geometry.screenToImage(10, 20, rect, badView));
  invalid(() => geometry.imageToScreen(10, 20, rect, badView));
  invalid(() => geometry.zoomViewAt(badView, 2, 10, 20, rect));
}
for (const badRect of [
  null,
  undefined,
  {left: NaN, top: 0, width: 512, height: 512},
  {left: 0, top: Infinity, width: 512, height: 512},
  {left: 0, top: 0, width: 0, height: 512},
  {left: 0, top: 0, width: 512, height: -1},
]) {
  invalid(() => geometry.screenToImage(10, 20, badRect, {z: 1, x: 0, y: 0}));
  invalid(() => geometry.imageToScreen(10, 20, badRect, {z: 1, x: 0, y: 0}));
  invalid(() => geometry.zoomViewAt({z: 1, x: 0, y: 0}, 2, 10, 20, badRect));
}
for (const dimensions of [[0, 512], [512, -1], [NaN, 512], [512, Infinity]]) {
  invalid(() => geometry.clampView({z: 1, x: 0, y: 0}, ...dimensions));
  invalid(() => geometry.screenToImage(10, 20, rect, {z: 1, x: 0, y: 0}, ...dimensions));
  invalid(() => geometry.imageToScreen(10, 20, rect, {z: 1, x: 0, y: 0}, ...dimensions));
  invalid(() => geometry.zoomViewAt({z: 1, x: 0, y: 0}, 2, 10, 20, rect, ...dimensions));
}
console.log(`Canvas view geometry: ${checks} acceptance assertions passed`);
