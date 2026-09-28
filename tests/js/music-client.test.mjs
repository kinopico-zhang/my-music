/* music-client.js (客户端识别双轴纯函数) 的 node --test 单元测试。
   1.8.103 起 mobile/desktop 单轴拆成两条正交轴 (用户点名「按屏幕尺寸分
   手机小/PC 大只管布局, 按操作逻辑分键鼠/触摸」): 布局轴 classifySize
   只认视口宽与 phone/pc 覆写; 操作轴 classifyInput 覆写最优先 → 主指针
   粗细 → UA 兜底。覆盖: 各轴覆写、乱写不算数、iPad 桌面模式 (fine 指针
   伪装 Mac UA 仍 coarse 拦得住)、旧 ?ui= 值归一。 */
import test from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const dir = path.join(path.dirname(fileURLToPath(import.meta.url)), "../../app/music/static/js");
const { classifyInput, classifySize, normalizeOverride } = require(path.join(dir, "music-client.js"));

test("classifySize: 布局轴只认视口宽与 phone/pc 覆写", () => {
  assert.equal(classifySize(true, ""), "large");
  assert.equal(classifySize(false, ""), "small");
  assert.equal(classifySize(true, "phone"), "small");   // ?ui=phone 强制小屏
  assert.equal(classifySize(false, "pc"), "large");     // ?ui=pc 强制大屏
  assert.equal(classifySize(true, "任意"), "large");     // 乱写不算数
  assert.equal(classifySize(false, "任意"), "small");
});

test("classifySize: touch/keymouse 只管操作轴, 不碰布局", () => {
  assert.equal(classifySize(true, "touch"), "large");     // PC 预览 iPad 形态
  assert.equal(classifySize(false, "keymouse"), "small");
});

test("classifyInput: ?ui= 覆写最优先 (真机预览另一端的样子)", () => {
  assert.equal(classifyInput(true, "Mozilla/5.0 (Macintosh)", "keymouse"), "keymouse");
  assert.equal(classifyInput(false, "Mozilla/5.0 (iPhone)", "touch"), "touch");
  assert.equal(classifyInput(true, "UA", "pc"), "keymouse");
  assert.equal(classifyInput(false, "UA", "phone"), "touch");
  assert.equal(classifyInput(true, "UA", "乱写"), "touch");   // 乱写不算数
});

test("classifyInput: 主指针粗细优先 (带鼠标的桌面才是 fine)", () => {
  assert.equal(classifyInput(true, "Mozilla/5.0 (Macintosh; Intel Mac OS X)"), "touch");
  assert.equal(classifyInput(true, ""), "touch");
  assert.equal(classifyInput(false, "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"), "keymouse");
});

test("classifyInput: UA 兜底 (fine 指针但 UA 是手机)", () => {
  assert.equal(classifyInput(false, "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)"), "touch");
  assert.equal(classifyInput(false, "Mozilla/5.0 (Linux; Android 14; Pixel 8)"), "touch");
  assert.equal(classifyInput(false, "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"), "keymouse");
});

test("normalizeOverride: 旧 ?ui= 值 (1.8.35–1.8.102 的 mobile/desktop) 照认", () => {
  assert.equal(normalizeOverride("mobile"), "phone");
  assert.equal(normalizeOverride("desktop"), "pc");
  assert.equal(normalizeOverride("touch"), "touch");
  assert.equal(normalizeOverride("keymouse"), "keymouse");
  assert.equal(normalizeOverride(""), "");
});
