/* music-client.js (客户端识别纯函数) 的 node --test 单元测试。
   覆盖: ?ui= 覆写最优先、覆写乱写不算数、主指针粗细优先 (触屏手机/
   平板 coarse, iPad 桌面模式伪装 Mac 也拦得住)、UA 兜底判手机/桌面。 */
import test from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const dir = path.join(path.dirname(fileURLToPath(import.meta.url)), "../../app/music/static/js");
const { classifyClient } = require(path.join(dir, "music-client.js"));

test("classifyClient: ?ui= 覆写最优先 (真机预览另一端的样子)", () => {
  assert.equal(classifyClient(true, "Mozilla/5.0 (Macintosh)", "desktop"), "desktop");
  assert.equal(classifyClient(false, "Mozilla/5.0 (iPhone)", "mobile"), "mobile");
});

test("classifyClient: 覆写参数乱写不算数, 当没有处理", () => {
  assert.equal(classifyClient(true, "UA", "pc"), "mobile");
  assert.equal(classifyClient(true, "UA", ""), "mobile");
  assert.equal(classifyClient(false, "Mozilla/5.0 (Macintosh)", "任意"), "desktop");
});

test("classifyClient: 主指针粗细优先 (带鼠标的桌面才是 fine)", () => {
  assert.equal(classifyClient(true, "Mozilla/5.0 (Macintosh; Intel Mac OS X)"), "mobile");
  assert.equal(classifyClient(true, ""), "mobile");
  assert.equal(classifyClient(false, "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"), "desktop");
});

test("classifyClient: UA 兜底 (fine 指针但 UA 是手机)", () => {
  assert.equal(classifyClient(false, "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)"), "mobile");
  assert.equal(classifyClient(false, "Mozilla/5.0 (Linux; Android 14; Pixel 8)"), "mobile");
  assert.equal(classifyClient(false, "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"), "desktop");
});
