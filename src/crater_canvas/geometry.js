/* Pure geometry shared by the local canvas and independent tests. */
(function (root) {
  "use strict";
  function checkRect(rect, width, height) {
    if (![rect.left, rect.top, rect.width, rect.height, width, height].every(Number.isFinite) || rect.width <= 0 || rect.height <= 0 || width <= 0 || height <= 0) throw new Error("Kích thước hiển thị không hợp lệ.");
  }
  function canvasToImage(clientX, clientY, rect, width = 512, height = 512) {
    checkRect(rect, width, height);
    if (![clientX, clientY].every(Number.isFinite)) throw new Error("Tọa độ không hợp lệ.");
    return { x: Math.min(width - 1, Math.max(0, (clientX - rect.left) * width / rect.width)), y: Math.min(height - 1, Math.max(0, (clientY - rect.top) * height / rect.height)) };
  }
  function imageRadius(screenDx, screenDy, rect, width = 512, height = 512) {
    checkRect(rect, width, height);
    if (![screenDx, screenDy].every(Number.isFinite)) throw new Error("Bán kính không hợp lệ.");
    return Math.hypot(screenDx * width / rect.width, screenDy * height / rect.height);
  }
  root.CraterGeometry = Object.freeze({ canvasToImage, imageRadius });
})(typeof window !== "undefined" ? window : globalThis);
