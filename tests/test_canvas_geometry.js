"use strict";

// Independent known-coordinate oracles; no Streamlit or browser mocks are needed.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const context = {window: {}};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname, "../src/crater_canvas/geometry.js"), "utf8"), context);
const geometry = context.window.CraterGeometry;

function near(actual, expected, message) {
  assert.ok(Math.abs(actual - expected) < 1e-9, `${message}: expected ${expected}, received ${actual}`);
}

for (const displaySize of [192, 256, 512, 768, 1024]) {
  const rect = {left: 37.25, top: 61.5, width: displaySize, height: displaySize};
  // Quarter and three-quarter of the display are pixel edges 128 and 384. With integer pixel centres
  // (data contract) those edges are 127.5 and 383.5.
  const point = geometry.canvasToImage(rect.left + displaySize / 4, rect.top + displaySize * 3 / 4, rect);
  near(point.x, 127.5, `quarter x at width ${displaySize}`);
  near(point.y, 383.5, `three-quarter y at width ${displaySize}`);
  const centre = geometry.canvasToImage(rect.left + 200.5 * displaySize / 512, rect.top + 100.5 * displaySize / 512, rect);
  near(centre.x, 200, `middle of pixel 200 at width ${displaySize}`);
  near(centre.y, 100, `middle of pixel 100 at width ${displaySize}`);
  near(geometry.imageRadius(displaySize * 3 / 16, displaySize / 4, rect), 160, `3-4-5 radius at width ${displaySize}`);

  // Display resizing must preserve arbitrary original image coordinates and radii.
  // A circle centre x sits on screen at (x + 0.5) display px per image px from the left edge.
  for (const circle of [
    {x: 0, y: 0, r: 6.5}, {x: 511, y: 511, r: 150},
    {x: 255.5, y: 88.25, r: 34.125},
  ]) {
    const restored = geometry.canvasToImage(rect.left + (circle.x + 0.5) * displaySize / 512,
      rect.top + (circle.y + 0.5) * displaySize / 512, rect);
    near(restored.x, circle.x, `preserved x at width ${displaySize}`);
    near(restored.y, circle.y, `preserved y at width ${displaySize}`);
    near(geometry.imageRadius(circle.r * displaySize / 512, 0, rect), circle.r,
      `preserved radius at width ${displaySize}`);
  }

  const low = geometry.canvasToImage(rect.left - displaySize, rect.top - displaySize, rect);
  near(low.x, 0, "outside left is clamped");
  near(low.y, 0, "outside top is clamped");
  const high = geometry.canvasToImage(rect.left + displaySize, rect.top + displaySize, rect);
  near(high.x, 511, "right boundary is a valid image centre");
  near(high.y, 511, "bottom boundary is a valid image centre");
}

// Defensive geometry accepts separate axis scales even though the UI stays square.
const stretched = {left: 10, top: 20, width: 256, height: 1024};
const middle = geometry.canvasToImage(138, 532, stretched);
near(middle.x, 255.5, "non-square x scale");
near(middle.y, 255.5, "non-square y scale");
near(geometry.imageRadius(15, 80, stretched), 50, "non-square displacement in image coordinates");

for (const rect of [
  {left: 0, top: 0, width: 0, height: 512},
  {left: 0, top: 0, width: 512, height: -1},
  {left: NaN, top: 0, width: 512, height: 512},
]) {
  assert.throws(() => geometry.canvasToImage(10, 20, rect), /không hợp lệ/);
  assert.throws(() => geometry.imageRadius(10, 20, rect), /không hợp lệ/);
}
const validRect = {left: 0, top: 0, width: 512, height: 512};
for (const value of [NaN, Infinity, -Infinity]) {
  assert.throws(() => geometry.canvasToImage(value, 20, validRect), /không hợp lệ/);
  assert.throws(() => geometry.imageRadius(10, value, validRect), /không hợp lệ/);
}
console.log("Canvas geometry acceptance checks passed");
