/* music-hero-bar-actions.js 路径换岗的纯几何单元测试 (1.8.46 三改, 用户点名
   「控件移动不一定非要走直线, 你计算一下, 要这几个控件移动的过程中不要有
   重叠的时刻」): 按真机代表几何 (iPhone 390/375 宽的操作行 → 顶栏右侧槽位,
   播放列表 5 键 / 专辑 4 键 / 艺人 2 键) 逐帧扫过全程行程 k, 验证:
   1. 任意时刻, 任何两颗仍可见 (淡出未过 0.15) 的飞行键, 中心距总有一个
      轴不小于键宽 40 —— 方块不叠 ⇔ 有一轴分开, 全程无重叠;
   2. 起飞/落位与弦端点重合 (弧线 sin(πe) 两端归零) —— 换岗无闪;
   3. 错峰排程: 到 … 路程近的先到场, 到场时刻两两错开。 */
import test from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const dir = path.join(path.dirname(fileURLToPath(import.meta.url)),
  "../../app/music/static/js");
const { HERO_BAR_FADE, heroBarPlanLanes, heroBarPointAt } =
  require(path.join(dir, "music-hero-bar-actions.js"));

const ROW_Y = 337;    // 操作行中心 (头内坐标: 封面 242 + 文字 59 + 边距)
const BAR_Y = 22;     // 顶栏行中心 (44 高的条居中)
const BTN = 40;       // 键的视觉边长 (36 槽位 × 行键起飞缩放 40/36)

/** 代表几何: n 颗 40px 行键 pitch 50 居中在层内容宽里; 顶栏槽位右贴
    16px 边距 —— 播放键槽 right-62, … 键/末键槽 right-18 (pitch 44)。 */
function buildFlyers(viewport, page) {
  const counts = { playlist: 5, album: 4, artist: 2 };
  const n = counts[page];
  const rowX = 16 + (viewport - 32 - (n * 40 + (n - 1) * 10)) / 2 + 20;
  const right = viewport - 16;
  const flyers = [];
  const at = (fx, tx, fade) =>
    ({ fx, fy: ROW_Y, tx, ty: BAR_Y, fade, arr: 1, bx: 0, by: 0 });
  flyers.push(at(rowX, right - 62, false));            // 播放键 → 自家槽
  for (let i = 1; i < n; i += 1) {
    flyers.push(at(rowX + 50 * i, right - 18, true));  // 其余收拢进 …
  }
  heroBarPlanLanes(flyers);
  return flyers;
}

/** 键在行程 k 的透明度 (与 heroBarTravel 同式): 收拢键到场前自淡。 */
function visibility(f, k) {
  if (!f.fade) return 1;
  const u = Math.min(1, k / f.arr);
  return Math.max(0, 1 - Math.max(0, (u - 1 + HERO_BAR_FADE) / HERO_BAR_FADE));
}

test("全程无重叠: 任意时刻两颗可见键总有一轴分开 ≥ 键宽", () => {
  for (const viewport of [390, 375]) {
    for (const page of ["playlist", "album", "artist"]) {
      const flyers = buildFlyers(viewport, page);
      let worst = Infinity;
      for (let i = 0; i <= 480; i += 1) {
        const k = i / 480;
        const pts = flyers.map((f) => heroBarPointAt(f, k));
        for (let a = 0; a < flyers.length; a += 1) {
          for (let b = a + 1; b < flyers.length; b += 1) {
            if (visibility(flyers[a], k) <= 0.15 ||
                visibility(flyers[b], k) <= 0.15) continue;
            const dx = Math.abs(pts[a][0] - pts[b][0]);
            const dy = Math.abs(pts[a][1] - pts[b][1]);
            worst = Math.min(worst, Math.max(dx, dy));
          }
        }
      }
      assert.ok(worst >= BTN,
        `${viewport}/${page}: 可见键途中相叠, 最小轴距 ${worst.toFixed(1)} < ${BTN}`);
    }
  }
});

test("起飞/落位与端点重合 (弧线两端归零, 换岗无闪)", () => {
  const flyers = buildFlyers(390, "playlist");
  const [px, py] = heroBarPointAt(flyers[0], 0);
  assert.ok(Math.hypot(px - flyers[0].fx, py - flyers[0].fy) < 0.01);
  for (const f of flyers) {
    const [x, y] = heroBarPointAt(f, f.arr);
    assert.ok(Math.hypot(x - f.tx, y - f.ty) < 0.01);
  }
});

test("错峰排程: 到 … 路程近的先到场, 到场时刻两两错开", () => {
  const flyers = buildFlyers(390, "playlist");
  const dist = (f) => Math.hypot(f.tx - f.fx, f.ty - f.fy);
  const sink = flyers.filter((f) => f.fade).sort((a, b) => dist(a) - dist(b));
  const arrs = sink.map((f) => f.arr);
  assert.ok(arrs.every((a, i) => i === 0 || arrs[i - 1] < a), "近的应先到场");
  assert.ok(arrs[0] < 1 && arrs[arrs.length - 1] === 1, "最远的一颗压轴到场");
});
