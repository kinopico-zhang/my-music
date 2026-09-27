// handoff.test — 后台连播提前接力裁决的决策表 (1.8.100)。
// 纯逻辑 (handoff.js) node 直测: 什么时候趁声音还在响就切下一曲。
import test from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const dir = path.join(path.dirname(fileURLToPath(import.meta.url)),
                      "../../app/music/static/js");
const { HANDOFF_WINDOW_S, HANDOFF_RESET_S, shouldHandoffEarly } =
  require(path.join(dir, "handoff.js"));

const BASE = { hidden: true, scrubbing: false, repeatOne: false,
               remaining: 0.3, spent: false };

test("窗口常量: 提前量零点几秒, 复位线 1 秒", () => {
  assert.equal(HANDOFF_WINDOW_S, 0.45);
  assert.equal(HANDOFF_RESET_S, 1);
});

test("后台 + 还剩零点几秒 + 没拖进度条 → 接力, 资格记一次", () => {
  const v = shouldHandoffEarly(BASE);
  assert.deepEqual(v, { handoff: true, spent: true });
});

test("前台不接力 (自然播完零裁切, ended 路原样)", () => {
  assert.equal(shouldHandoffEarly({ ...BASE, hidden: false }).handoff, false);
});

test("拖进度条不接力 (别抢用户手里的操作)", () => {
  assert.equal(shouldHandoffEarly({ ...BASE, scrubbing: true }).handoff, false);
});

test("单曲循环不接力 (ended 自己回开头, 不换曲)", () => {
  assert.equal(shouldHandoffEarly({ ...BASE, repeatOne: true }).handoff, false);
});

test("剩余回 1 秒之上 → 资格复位 (新曲时间轴, 末尾可再触发)", () => {
  const v = shouldHandoffEarly({ ...BASE, remaining: 30, spent: true });
  assert.deepEqual(v, { handoff: false, spent: false });
});

test("本曲末尾已接力过 → 连拍不再动手 (防 timeupdate 密集触发连切)", () => {
  const v = shouldHandoffEarly({ ...BASE, spent: true });
  assert.deepEqual(v, { handoff: false, spent: true });
});

test("窗口边界: 0.45 内动手, 出窗不动, ≤0 交给 ended 保底", () => {
  assert.equal(
    shouldHandoffEarly({ ...BASE, remaining: HANDOFF_WINDOW_S }).handoff, true);
  assert.equal(
    shouldHandoffEarly({ ...BASE, remaining: HANDOFF_WINDOW_S + 0.01 })
      .handoff, false);
  assert.equal(shouldHandoffEarly({ ...BASE, remaining: 0 }).handoff, false);
  assert.equal(shouldHandoffEarly({ ...BASE, remaining: -0.5 }).handoff, false);
});
