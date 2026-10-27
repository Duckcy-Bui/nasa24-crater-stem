/* Pure geometry shared by the local canvas and independent tests.
 *
 * Two units appear here. The view (pan/zoom) and screenToImage/imageToScreen use pixel edges:
 * the image spans [0, 512] and pixel i covers [i, i + 1). Circles follow the data contract
 * (docs/DINH_DANG_DU_LIEU.md): pixel i has its centre at the integer i, the same as Hough and
 * the labelling tool. canvasToImage, screenToPixel and pixelToScreen convert to and from that
 * centre convention by shifting PIXEL_CENTER = 0.5 px. */
(function (root) {
  "use strict";
  const PIXEL_CENTER = 0.5;
  function checkRect(rect, width, height) {
    if (![rect.left, rect.top, rect.width, rect.height, width, height].every(Number.isFinite) || rect.width <= 0 || rect.height <= 0 || width <= 0 || height <= 0) throw new Error("Kích thước hiển thị không hợp lệ.");
  }
  function canvasToImage(clientX, clientY, rect, width = 512, height = 512) {
    checkRect(rect, width, height);
    if (![clientX, clientY].every(Number.isFinite)) throw new Error("Tọa độ không hợp lệ.");
    return {
      x: Math.min(width - 1, Math.max(0, (clientX - rect.left) * width / rect.width - PIXEL_CENTER)),
      y: Math.min(height - 1, Math.max(0, (clientY - rect.top) * height / rect.height - PIXEL_CENTER)),
    };
  }
  function imageRadius(screenDx, screenDy, rect, width = 512, height = 512) {
    checkRect(rect, width, height);
    if (![screenDx, screenDy].every(Number.isFinite)) throw new Error("Bán kính không hợp lệ.");
    return Math.hypot(screenDx * width / rect.width, screenDy * height / rect.height);
  }
  function checkView(view, boundedZoom = true) {
    if (!view || ![view.z, view.x, view.y].every(Number.isFinite) || (boundedZoom && (view.z < 1 || view.z > 8))) throw new Error("Trạng thái xem không hợp lệ.");
  }
  function clampView(view, width = 512, height = 512) {
    checkView(view, false);
    if (![width, height].every(Number.isFinite) || width <= 0 || height <= 0) throw new Error("Kích thước ảnh không hợp lệ.");
    const z = Math.min(8, Math.max(1, view.z));
    return {
      z,
      x: Math.min(width - width / z, Math.max(0, view.x)),
      y: Math.min(height - height / z, Math.max(0, view.y)),
    };
  }
  function screenToImage(clientX, clientY, rect, view, width = 512, height = 512) {
    if (!rect) throw new Error("Kích thước hiển thị không hợp lệ.");
    checkRect(rect, width, height);
    checkView(view);
    if (![clientX, clientY].every(Number.isFinite)) throw new Error("Tọa độ không hợp lệ.");
    return {
      x: view.x + (clientX - rect.left) * width / (rect.width * view.z),
      y: view.y + (clientY - rect.top) * height / (rect.height * view.z),
    };
  }
  function imageToScreen(x, y, rect, view, width = 512, height = 512) {
    if (!rect) throw new Error("Kích thước hiển thị không hợp lệ.");
    checkRect(rect, width, height);
    checkView(view);
    if (![x, y].every(Number.isFinite)) throw new Error("Tọa độ không hợp lệ.");
    return {
      x: rect.left + (x - view.x) * rect.width * view.z / width,
      y: rect.top + (y - view.y) * rect.height * view.z / height,
    };
  }
  function screenToPixel(clientX, clientY, rect, view, width = 512, height = 512) {
    const edge = screenToImage(clientX, clientY, rect, view, width, height);
    return { x: edge.x - PIXEL_CENTER, y: edge.y - PIXEL_CENTER };
  }
  function pixelToScreen(x, y, rect, view, width = 512, height = 512) {
    if (![x, y].every(Number.isFinite)) throw new Error("Tọa độ không hợp lệ.");
    return imageToScreen(x + PIXEL_CENTER, y + PIXEL_CENTER, rect, view, width, height);
  }
  function zoomViewAt(view, newZ, clientX, clientY, rect, width = 512, height = 512) {
    const anchor = screenToImage(clientX, clientY, rect, view, width, height);
    if (!Number.isFinite(newZ)) throw new Error("Mức phóng to không hợp lệ.");
    const z = Math.min(8, Math.max(1, newZ));
    return clampView({
      z,
      x: anchor.x - (clientX - rect.left) * width / (rect.width * z),
      y: anchor.y - (clientY - rect.top) * height / (rect.height * z),
    }, width, height);
  }
  root.CraterGeometry = Object.freeze({ PIXEL_CENTER, canvasToImage, imageRadius, clampView, screenToImage, imageToScreen,
    screenToPixel, pixelToScreen, zoomViewAt });
})(typeof window !== "undefined" ? window : globalThis);
