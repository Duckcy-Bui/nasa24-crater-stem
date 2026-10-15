"use strict";

// Real Chromium checks and captures; the circles below are UI interaction demos,
// never NASA ground truth. Requires Playwright with its Chromium installed.
const {chromium} = require(process.env.NASA24_PLAYWRIGHT_MODULE || "playwright");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const ROOT = path.resolve(__dirname, "..");
const OUTPUT = path.resolve(ROOT, process.env.NASA24_UI_R1_OUTPUT || "outputs/s109_ui_r1");
const URL = process.env.NASA24_UI_R1_URL || "http://127.0.0.1:8501";
const IMAGE = "moon_ap16_m113853974r_c01";
const demoCircles = [
  [105.42, 200.18, 108.64], [178.31, 211.77, 31.52],
  [433.04, 35.21, 7.38], [406.12, 340.26, 8.81],
  [243.2, 183.47, 6.09], [383.4, 280.63, 5.62],
  [313.0, 272.4, 5.2], [448.58, 410.16, 5.43],
];

(async () => {
  fs.mkdirSync(OUTPUT, {recursive: true});
  const browser = await chromium.launch({headless: true});
  const errors = [], blockedExternal = [], checks = [], captures = [];
  const report = {status: "RUNNING", checks, captures, errors, blockedExternal};
  try {
    for (const width of [1440, 390]) {
      const context = await browser.newContext({viewport: {width, height: 900}, acceptDownloads: true});
      await context.route("**/*", route => {
        const requestUrl = route.request().url();
        if (/^https?:/.test(requestUrl) && new globalThis.URL(requestUrl).origin !== new globalThis.URL(URL).origin) {
          blockedExternal.push(requestUrl); return route.abort();
        }
        return route.continue();
      });
      const page = await context.newPage();
      page.on("pageerror", error => errors.push(error.message));
      await page.goto(URL);
      const canvasFrame = page.frameLocator('iframe').first();
      const child = () => page.frames().find(item => item.url().includes("/component/"));
      await canvasFrame.locator("#craterCanvas").waitFor();
      const picker = page.getByRole("combobox");
      await picker.fill(IMAGE); await picker.press("ArrowDown");
      await page.getByRole("option").filter({hasText: IMAGE}).click();
      await canvasFrame.locator("#imageMeta").filter({hasText: "2 m/px"}).waitFor();
      await canvasFrame.locator("#saveAnswer:not([disabled])").waitFor();
      await child().waitForFunction(() => document.getElementById("craterCanvas").getContext("2d").getImageData(256,256,1,1).data[0] > 0);

      async function settle() {
        await child().waitForFunction(() => Math.abs(innerHeight - Math.ceil(document.body.getBoundingClientRect().height) - 8) < 2);
      }
      async function capture(state) {
        await settle();
        if (width === 390) {
          const contentHeight = await page.getByTestId("stMain").evaluate(element => element.scrollHeight);
          await page.setViewportSize({width, height: Math.max(900, contentHeight)});
          await settle();
        }
        await page.getByRole("heading", {name: "Khoanh hố Mặt Trăng", exact: true}).scrollIntoViewIfNeeded();
        const file = `${width}_${state}.png`;
        await page.screenshot({path: path.join(OUTPUT, file), fullPage: width === 390, animations: "disabled"});
        captures.push(file);
      }
      async function download(name, expectedImage = IMAGE) {
        const pending = page.waitForEvent("download");
        await canvasFrame.locator("#downloadAnswer").click();
        const result = await pending;
        assert.equal(result.suggestedFilename(), `${expectedImage}_player.json`);
        const destination = path.join(OUTPUT, `${width}_${name}.json`);
        await result.saveAs(destination);
        return JSON.parse(fs.readFileSync(destination));
      }
      async function draw(x, y, r) {
        await canvasFrame.locator("#drawMode").click();
        await page.getByRole("heading", {name: "Khoanh hố Mặt Trăng", exact: true}).scrollIntoViewIfNeeded();
        const box = await canvasFrame.locator("#craterCanvas").boundingBox();
        await page.mouse.move(box.x + x * box.width / 512, box.y + y * box.height / 512);
        await page.mouse.down();
        await page.mouse.move(box.x + (x + r) * box.width / 512, box.y + y * box.height / 512, {steps: 8});
        await page.mouse.up();
      }
      async function layout(state) {
        await settle();
        const data = await child().evaluate(() => {
          const rect = id => {
            const box = document.getElementById(id).getBoundingClientRect();
            return {x: box.x, y: box.y, width: box.width, height: box.height, bottom: box.bottom};
          };
          const buttons = [...document.querySelectorAll("button")].filter(button => button.getBoundingClientRect().height > 0);
          const inputWidths = [...document.querySelectorAll(".field input")].map(input => {
            const style = getComputedStyle(input), text = document.createElement("canvas").getContext("2d");
            text.font = `${style.fontWeight} ${style.fontSize} ${style.fontFamily}`;
            return {id: input.id, available: input.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight) - 18, required: text.measureText("511.00").width};
          });
          const ghost = getComputedStyle(document.getElementById("undo"));
          return {
            width: innerWidth, scrollWidth: document.documentElement.scrollWidth,
            toolbar: document.querySelector(".toolbar").getBoundingClientRect().toJSON(),
            canvas: rect("craterCanvas"), meta: rect("imageMeta"), draw: rect("drawMode"), edit: rect("editMode"), undo: rect("undo"), remove: rect("deleteCircle"), save: rect("saveAnswer"),
            buttonSizes: buttons.map(button => ({id: button.id, width: button.getBoundingClientRect().width, height: button.getBoundingClientRect().height})),
            inputWidths, fontPxOnScreen: parseFloat(document.getElementById("craterCanvas").getContext("2d").font.split(" ").find(token => token.endsWith("px"))) * rect("craterCanvas").width / 512,
            ghost: {background: ghost.backgroundColor, border: ghost.borderColor, opacity: ghost.opacity},
            background: getComputedStyle(document.body).backgroundColor,
            statusClipped: getComputedStyle(document.getElementById("status")).clip,
          };
        });
        report.lastLayout = {viewport: width, state, ...data};
        assert.ok(data.scrollWidth <= data.width, "component must not overflow horizontally");
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), "page must not overflow horizontally");
        assert.equal(data.background, "rgb(10, 12, 15)");
        assert.notEqual(data.statusClipped, "auto");
        if (width === 1440) {
          assert.ok(Math.abs(data.toolbar.x - data.canvas.x) <= 1.1, "toolbar and canvas align left");
          assert.ok(Math.abs(data.meta.x - data.canvas.x) <= 1.1, "meta and canvas align left");
          const mainSize = await page.getByTestId("stMain").evaluate(element => ({height: element.clientHeight, scrollHeight: element.scrollHeight}));
          assert.ok(mainSize.scrollHeight <= mainSize.height + 2, "desktop must not scroll: " + JSON.stringify(mainSize));
        } else {
          assert.ok(Math.abs(data.draw.y - data.undo.y) <= 5 && Math.abs(data.edit.y - data.remove.y) <= 5, "mobile toolbar is one row");
          assert.equal(Math.round(data.undo.width), 44); assert.equal(Math.round(data.remove.width), 44);
          assert.ok(data.buttonSizes.every(button => button.height >= 44), "every mobile component button is at least44px");
          assert.equal(await canvasFrame.locator("#undo .action-label").isVisible(), false);
          assert.equal(await canvasFrame.locator("#drawMode .mobile-label").isVisible(), true);
        }
        if (state === "empty") {
          assert.equal(await canvasFrame.locator("#listHead").isVisible(), false);
          assert.equal(data.ghost.background, "rgba(0, 0, 0, 0)");
          assert.equal(data.ghost.border, "rgba(0, 0, 0, 0)");
          assert.equal(data.ghost.opacity, "0.42");
        } else {
          assert.ok(data.inputWidths.every(input => input.available >= input.required), "511.00 fits each numeric input with native spin controls");
          assert.ok(Math.abs(data.fontPxOnScreen - 11) < 0.01, "canvas ID font stays11 CSSpx");
        }
        checks.push({viewport: width, state, status: "PASS", layout: data});
      }

      await layout("empty"); await capture("empty");
      // Mouse-generated fractional source precision, not an injected answer.
      await draw(178.304057816, 211.774167314, 31.527319817);
      const before = await download("precision_before");
      const original = before.circles[0];
      for (const [id, key] of [["centerX", "x"], ["centerY", "y"], ["radius", "r"]]) assert.equal(await canvasFrame.locator(`#${id}`).inputValue(), original[key].toFixed(2));
      await canvasFrame.locator("#applyEdit").click();
      assert.deepEqual(await download("precision_after"), before, "untouched rounded fields preserve raw JSON");
      await canvasFrame.locator("#centerX").fill("200.123456789");
      await canvasFrame.locator("#applyEdit").click();
      const edited = await download("precision_edited");
      assert.equal(edited.circles[0].x, 200.123456789);
      assert.equal(edited.circles[0].y, original.y); assert.equal(edited.circles[0].r, original.r);
      await canvasFrame.locator("#saveAnswer").click(); await canvasFrame.locator("#saveStatus").waitFor({state: "visible"});
      const precisionPath = await canvasFrame.locator("#savedPath").getAttribute("title");
      assert.deepEqual(JSON.parse(fs.readFileSync(path.join(ROOT, precisionPath, "craters.json"))), edited, "save_nonce preserves raw source precision");
      await canvasFrame.locator("#centerX").fill(String(original.x)); await canvasFrame.locator("#applyEdit").click();
      await canvasFrame.locator("#saveStatus").waitFor({state: "hidden"});
      await canvasFrame.locator("#radius").fill("-4"); await canvasFrame.locator("#applyEdit").click();
      assert.equal(await canvasFrame.locator("#radius").getAttribute("aria-invalid"), "true");
      assert.deepEqual(await download("invalid_unchanged"), before);
      await canvasFrame.locator("#editMode").click(); // preserve invalid input for the required capture below
      await canvasFrame.locator("#radius").fill("-4"); await canvasFrame.locator("#applyEdit").click();
      await layout("one_error"); await capture("one_error");

      await canvasFrame.locator("#deleteCircle").click();
      for (const circle of demoCircles) await draw(...circle);
      await canvasFrame.locator(".circleRow").nth(1).click();
      await canvasFrame.locator("#saveAnswer").click(); await canvasFrame.locator("#saveStatus").waitFor({state: "visible"});
      const saved = await canvasFrame.locator("#savedPath").getAttribute("title");
      const text = await canvasFrame.locator("#savedPath").innerText();
      assert.ok(saved.startsWith("outputs/player_answers/player_"));
      assert.ok(text.startsWith("out") && text.includes("…") && text.includes("player_") && text.endsWith(saved.slice(-12)), "middle truncation preserves directory/filename/hash");
      const answer = await download("many_saved");
      assert.equal(answer.circles.length, 8);
      assert.deepEqual(JSON.parse(fs.readFileSync(path.join(ROOT, saved, "craters.json"))), answer);
      // Trigger a rerun and require a stable selection and count in its label.
      await canvasFrame.locator("#saveAnswer").click();
      await child().waitForFunction(oldPath => document.getElementById("savedPath").title !== oldPath && !document.getElementById("saveStatus").hidden, saved);
      const pickerText = await page.getByTestId("stSelectbox").innerText();
      const pickerValue = await picker.inputValue();
      const selectedLabel = pickerText + pickerValue;
      assert.ok(selectedLabel.includes(IMAGE) && selectedLabel.includes("8 vòng"), "picker keeps selected image and draft count");
      await layout("many_saved"); await capture("many_saved");
      // Labels change with counts, but switching images must still follow intent.
      for (const id of ["moon_ap15_hia_c02", IMAGE]) {
        await picker.fill(id); await picker.press("ArrowDown");
        await page.getByRole("option").filter({hasText: id}).click();
        await canvasFrame.locator("#circleCount").filter({hasText: id === IMAGE ? /^8$/ : /^0$/}).waitFor();
        const returned = await download(id === IMAGE ? "restored_image" : "other_image", id);
        assert.equal(returned.image_id, id);
        if (id === IMAGE) assert.deepEqual(returned, answer);
        else assert.equal(returned.circles.length, 0);
      }
      // Test actual resize repaint without changing circles or receiving a new revision.
      await page.setViewportSize({width: width === 1440 ? 390 : 1440, height: 900});
      await child().waitForFunction(() => {
        const canvas = document.getElementById("craterCanvas"), size = parseFloat(canvas.getContext("2d").font.split(" ").find(token => token.endsWith("px")));
        return Math.abs(size * canvas.getBoundingClientRect().width / 512 - 11) < 0.01;
      });
      checks.push({viewport: width, state: "precision_and_resize", status: "PASS", precisionSave: precisionPath, saved, displayedPath: text});
      await context.close();
    }
    assert.deepEqual(errors, []); assert.deepEqual(blockedExternal, []);
    assert.equal(captures.length, 6);
    report.status = "PASS";
  } catch (error) {
    report.status = "FAIL"; report.failure = error.stack; throw error;
  } finally {
    report.recorded_at_utc = new Date().toISOString();
    fs.writeFileSync(path.join(OUTPUT, "browser_checks.json"), JSON.stringify(report, null, 2) + "\n");
    await browser.close();
    console.log(JSON.stringify({status: report.status, captures, checkGroups: checks.length, errors}));
  }
})().catch(error => {console.error(error.stack); process.exitCode = 1;});
