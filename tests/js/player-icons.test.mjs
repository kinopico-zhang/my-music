/* 播放器控制图标对齐的单元测试 (2026-09-14 用户反馈「歪七扭八」后立规矩):
   图标画在视框里, 视觉包围盒的中心必须落在视框中心 ——
   图标光心 = 按钮中心, 播放↔暂停切换不左右跳位, 上一首/下一首镜像对称;
   1.8.0 起船坞键和上弹菜单的图标也进同一规矩 (素材库 1024 视框的字形
   不在画布正中时, 用 viewBox 偏移把光心挪回来 —— 断言认视框中心)。
   从源文件文本里提 SVG 路径 (music-common.js 无导出尾巴, 不为测试改产品文件),
   用迷你路径解析器算包围盒 —— M/L/m/l/H/h/V/v/z + q/Q/t/T + a/A (圆弧
   连端点带极值一起标, 人像/下载这类带弧的素材库图标才量得准)。 */
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const dir = path.join(path.dirname(fileURLToPath(import.meta.url)),
  "../../app/music/static/js");
const common = fs.readFileSync(path.join(dir, "music-common.js"), "utf8");
const page = fs.readFileSync(path.join(dir, "..", "music.html"), "utf8");

/** 算 SVG 路径的几何包围盒 (图标用到的命令都认; M 后隐式 L 同样取点)。
    素材库图标 (2026-09-15 起) 是 q/t 二次曲线; 1.8.1 回退的旧资料库盒/
    旧齿轮是 c/s 三次曲线: 曲线必落在控制多边形凸包内, 所以控制点 +
    终点都标记; t/s 的反射控制点 = 2×当前点 − 上一控制点。 */
function pathBBox(d) {
  const tokens = d.match(/[A-Za-z]|-?\d*\.?\d+/g) || [];
  let x = 0, y = 0;               // 当前点 (绝对坐标)
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  let lastControl = null;         // 上一条 q/t 的控制点 (t 反射用)
  let lastCubic = null;           // 上一条 c/s 的第二控制点 (s 反射用)
  const markAt = (px, py) => {
    minX = Math.min(minX, px); maxX = Math.max(maxX, px);
    minY = Math.min(minY, py); maxY = Math.max(maxY, py);
  };
  const mark = () => markAt(x, y);
  let i = 0;
  let command = "";
  while (i < tokens.length) {
    if (/[A-Za-z]/.test(tokens[i])) { command = tokens[i]; i += 1; continue; }
    const num = () => Number(tokens[i++]);
    switch (command) {
      case "M": case "L": x = num(); y = num(); mark(); lastControl = null; lastCubic = null; break;
      case "m": case "l": x += num(); y += num(); mark(); lastControl = null; lastCubic = null; break;
      case "H": x = num(); mark(); lastControl = null; lastCubic = null; break;
      case "h": x += num(); mark(); lastControl = null; lastCubic = null; break;
      case "V": y = num(); mark(); lastControl = null; lastCubic = null; break;
      case "v": y += num(); mark(); lastControl = null; lastCubic = null; break;
      case "Q": {
        const cx = num(), cy = num();
        x = num(); y = num();
        markAt(cx, cy); mark();
        lastControl = [cx, cy]; lastCubic = null;
        break;
      }
      case "q": {
        const cx = x + num(), cy = y + num();
        x += num(); y += num();
        markAt(cx, cy); mark();
        lastControl = [cx, cy]; lastCubic = null;
        break;
      }
      case "C": {
        const c1x = num(), c1y = num(), c2x = num(), c2y = num();
        x = num(); y = num();
        markAt(c1x, c1y); markAt(c2x, c2y); mark();
        lastControl = null; lastCubic = [c2x, c2y];
        break;
      }
      case "c": {
        const c1x = x + num(), c1y = y + num();
        const c2x = x + num(), c2y = y + num();
        x += num(); y += num();
        markAt(c1x, c1y); markAt(c2x, c2y); mark();
        lastControl = null; lastCubic = [c2x, c2y];
        break;
      }
      case "S": {
        let c1x = x, c1y = y;
        if (lastCubic) { c1x = 2 * x - lastCubic[0]; c1y = 2 * y - lastCubic[1]; }
        const c2x = num(), c2y = num();
        x = num(); y = num();
        markAt(c1x, c1y); markAt(c2x, c2y); mark();
        lastControl = null; lastCubic = [c2x, c2y];
        break;
      }
      case "s": {
        let c1x = x, c1y = y;
        if (lastCubic) { c1x = 2 * x - lastCubic[0]; c1y = 2 * y - lastCubic[1]; }
        const c2x = x + num(), c2y = y + num();
        x += num(); y += num();
        markAt(c1x, c1y); markAt(c2x, c2y); mark();
        lastControl = null; lastCubic = [c2x, c2y];
        break;
      }
      case "T": {
        let cx = x, cy = y;
        if (lastControl) { cx = 2 * x - lastControl[0]; cy = 2 * y - lastControl[1]; }
        x = num(); y = num();
        markAt(cx, cy); mark();
        lastControl = [cx, cy]; lastCubic = null;
        break;
      }
      case "t": {
        let cx = x, cy = y;
        if (lastControl) { cx = 2 * x - lastControl[0]; cy = 2 * y - lastControl[1]; }
        x += num(); y += num();
        markAt(cx, cy); mark();
        lastControl = [cx, cy]; lastCubic = null;
        break;
      }
      case "A": case "a": {
        const rx = num(), ry = num(), rotDeg = num(), laf = num(), sf = num();
        const endX = command === "A" ? num() : x + num();
        const endY = command === "A" ? num() : y + num();
        markArcExtremes(rx, ry, rotDeg, laf, sf, x, y, endX, endY);
        x = endX; y = endY; lastControl = null; lastCubic = null;
        break;
      }
      case "z": case "Z": break;
      default: throw new Error(`路径命令没支持: ${command}`);
    }
  }
  return { minX, maxX, minY, maxY };

  /** 圆弧的极值点 (圆心参数化): 半轴端点 ± 旋转, 连两端点一起标。 */
  function markArcExtremes(rx, ry, rotDeg, laf, sf, x1, y1, x2, y2) {
    markAt(x1, y1); markAt(x2, y2);
    const rot = rotDeg * Math.PI / 180;
    const dx2 = (x1 - x2) / 2, dy2 = (y1 - y2) / 2;
    const cos = Math.cos(rot), sin = Math.sin(rot);
    const x1p = cos * dx2 + sin * dy2, y1p = -sin * dx2 + cos * dy2;
    const lam = (x1p * x1p) / (rx * rx) + (y1p * y1p) / (ry * ry);
    const scale = lam > 1 ? Math.sqrt(lam) : 1;
    rx /= scale; ry /= scale;
    const sign = laf === sf ? -1 : 1;
    const co = Math.sqrt(Math.max(0, (rx * rx * ry * ry - rx * rx * y1p * y1p
      - ry * ry * x1p * x1p) / (rx * rx * y1p * y1p + ry * ry * x1p * x1p)));
    const cxp = sign * co * rx * y1p / ry, cyp = sign * co * -ry * x1p / rx;
    const cx = cos * cxp - sin * cyp + (x1 + x2) / 2;
    const cy = sin * cxp + cos * cyp + (y1 + y2) / 2;
    for (const [ux, uy] of [[rx, 0], [-rx, 0], [0, ry], [0, -ry]]) {
      markAt(cx + cos * ux - sin * uy, cy + sin * ux + cos * uy);
    }
  }
}

function iconPath(name) {
  const match = common.match(new RegExp(`const ${name} = '[^']*d="([^"]+)"`));
  assert.ok(match, `music-common.js 里找不到 ${name}`);
  return match[1];
}

function centered(name, d, tolerance = 0.01) {
  const b = pathBBox(d);
  const cx = (b.minX + b.maxX) / 2, cy = (b.minY + b.maxY) / 2;
  assert.ok(Math.abs(cx - 12) <= tolerance, `${name} 横向光心 ${cx} ≠ 12`);
  assert.ok(Math.abs(cy - 12) <= tolerance, `${name} 纵向光心 ${cy} ≠ 12`);
  return b;
}

/** svg 整串的光心断言 (船坞键同款): 全部路径包围盒并集中心 == 视框中心,
    容差按视框边长取比例 —— iconfont 素材 (1024 画布) 字形不一定在正中,
    产品里用 viewBox 偏移把光心挪回来, 这里认视框中心。 */
function svgCentered(label, svg) {
  const viewBox = svg.match(/viewBox="([^"]+)"/)[1].split(/\s+/).map(Number);
  const boxes = [...svg.matchAll(/ d="([^"]+)"/g)].map((m) => pathBBox(m[1]));
  const cx = (Math.min(...boxes.map((b) => b.minX))
    + Math.max(...boxes.map((b) => b.maxX))) / 2;
  const cy = (Math.min(...boxes.map((b) => b.minY))
    + Math.max(...boxes.map((b) => b.maxY))) / 2;
  const [vx, vy, vw, vh] = viewBox;
  const tolX = Math.max(vw * 0.005, 0.02), tolY = Math.max(vh * 0.005, 0.02);
  assert.ok(Math.abs(cx - (vx + vw / 2)) <= tolX,
    `${label} 横向光心 ${cx} ≠ ${vx + vw / 2}`);
  assert.ok(Math.abs(cy - (vy + vh / 2)) <= tolY,
    `${label} 纵向光心 ${cy} ≠ ${vy + vh / 2}`);
}

/** 从 music-common.js 里取整枚图标 (const NAME = '<svg …>')。 */
function iconSvg(name) {
  const match = common.match(new RegExp(`const ${name} = '(<svg[\\s\\S]*?</svg>)'`));
  assert.ok(match, `music-common.js 里找不到 ${name}`);
  return match[1];
}

test("播放/暂停图标: 包围盒中心在正中 (切换不跳位)", () => {
  centered("ICON_PLAY (小)", iconPath("ICON_PLAY"));
  centered("ICON_PAUSE (小)", iconPath("ICON_PAUSE"));
  centered("ICON_PLAY_BIG", iconPath("ICON_PLAY_BIG"));
  centered("ICON_PAUSE_BIG", iconPath("ICON_PAUSE_BIG"));
  centered("ICON_ACTION_PLAY (行内播放角标)", iconPath("ICON_ACTION_PLAY"));
  centered("ICON_ACTION_TRASH (列表删除)", iconPath("ICON_ACTION_TRASH"));
});

test("上一首/下一首 (全屏页): 居中且彼此镜像", () => {
  const pick = (id) => {
    const match = page.match(new RegExp(`id="${id}".*?d="([^"]+)"`, "s"));
    assert.ok(match, `music.html 里找不到 ${id} 的图标路径`);
    return match[1];
  };
  const prev = centered("fp-prev", pick("fp-prev"));
  const next = centered("fp-next", pick("fp-next"));
  // 同宽同高 (镜像形状), 区间一致 —— 一对跳转键看起来才对称。
  // 镜像是 24−x 烘出来的, 浮点尾差 1e-15 级, 用容差不卡 bit 级相等
  const nearly = (a, b) => Math.abs(a - b) <= 1e-6;
  assert.ok(nearly(prev.maxX - prev.minX, next.maxX - next.minX),
    `上一首宽 ${prev.maxX - prev.minX} ≠ 下一首宽 ${next.maxX - next.minX}`);
  assert.ok(nearly(prev.maxY - prev.minY, next.maxY - next.minY),
    `上一首高 ${prev.maxY - prev.minY} ≠ 下一首高 ${next.maxY - next.minY}`);
  assert.ok(nearly(prev.minX, next.minX) && nearly(prev.maxX, next.maxX),
    `区间不对称: prev [${prev.minX}, ${prev.maxX}] vs next [${next.minX}, ${next.maxX}]`);
});

test("船坞键与上弹菜单图标 (1.8.0): 光心对准各自的视框中心", () => {
  const pick = (selector) => {
    const match = page.match(new RegExp(
      `${selector}[^>]*>\\s*(<svg viewBox="([^"]+)"[^>]*>[\\s\\S]*?</svg>)`));
    assert.ok(match, `music.html 里找不到 ${selector} 的图标`);
    // 菜单图标有复合字形 (1.8.1 专辑 = 旧资料库盒, 4 条路径): 光心取
    // 全部路径包围盒的并集, 只看第一条会把上面的装饰条漏掉 (差 118/1024)
    const ds = [...match[1].matchAll(/ d="([^"]+)"/g)].map((m) => m[1]);
    return { viewBox: match[2].split(/\s+/).map(Number), ds };
  };
  // 素材库的字形不一定在画布正中 (云下载 cy=490.6/1024): 用 viewBox 偏移
  // 把光心挪回视框中心, 断言 = 包围盒中心 == 视框中心。
  // 容差按视框边长取比例 (1024 画布上 0.5% ≈ 5 个单位, 旧齿轮差 2.4 在内)
  for (const [label, selector] of [
    ["dock-menu (汉堡)", 'id="dock-menu"'],
    ["dock-search (放大镜)", 'id="dock-search"'],
    ["pop-playlists (队列)", 'data-pop-nav="playlists"'],
    ["pop-albums (资料库盒)", 'data-pop-nav="albums"'],
    ["pop-artists (三人)", 'data-pop-nav="artists"'],
    ["pop-recent (时钟)", 'data-pop-nav="recent"'],
    ["pop-downloads (云下载)", 'data-pop-nav="downloads"'],
    ["pop-settings (齿轮)", 'data-pop-nav="settings"'],
  ]) {
    const { viewBox, ds } = pick(selector);
    const boxes = ds.map(pathBBox);
    const cx = (Math.min(...boxes.map((b) => b.minX))
      + Math.max(...boxes.map((b) => b.maxX))) / 2;
    const cy = (Math.min(...boxes.map((b) => b.minY))
      + Math.max(...boxes.map((b) => b.maxY))) / 2;
    const [vx, vy, vw, vh] = viewBox;
    const tolX = Math.max(vw * 0.005, 0.02), tolY = Math.max(vh * 0.005, 0.02);
    assert.ok(Math.abs(cx - (vx + vw / 2)) <= tolX,
      `${label} 横向光心 ${cx} ≠ ${vx + vw / 2}`);
    assert.ok(Math.abs(cy - (vy + vh / 2)) <= tolY,
      `${label} 纵向光心 ${cy} ≠ ${vy + vh / 2}`);
  }
});

test("全屏页新底行 (参考图 1:1 批): ⋯ / 循环 / 词 / 队列都居中", () => {
  const pick = (id) => {
    const match = page.match(new RegExp(`id="${id}".*?d="([^"]+)"`, "s"));
    assert.ok(match, `music.html 里找不到 ${id} 的图标路径`);
    return match[1];
  };
  // 取的是每个按钮的第一个 path (复合图标的第二路径不算)
  centered("fp-menu-btn (⋯)", pick("fp-menu-btn"));
  centered("fp-lyrics-btn (词引号)", pick("fp-lyrics-btn"));
  centered("fp-queue-btn (队列)", pick("fp-queue-btn"));
  // 1.8.89 循环模式键 (接管加列表键的位): 默认形内联在页里, 与 ICON_REPEAT
  // 逐字节同款 (首拍 updatePlayModeButton 不跳位); 单曲/随机两态住
  // music-common.js 换 innerHTML —— 1.8.90 三态重画为粗描边 (用户点名
  // 「线条要粗一点」), 1.8.91 再并进同一枚 path (半透明描边下一枚 path 只
  // 上一次色, 交叉/接头不叠深) 并 28→24 缩到与邻键同量 (用户点名「偏大」);
  // 1.8.111 换 iconfont 实底新画法: 列表/单曲共用同一枚环和同一视框 (用户
  // 点名「循环主题的位置要重叠」) —— 单曲的 d 以列表的 d 起头, 环逐像素
  // 不动; 1.8.115 徽章从环心挪 logo 右上角 (用户点名): 圆片盖住右上折角
  // 箭头旗顶到视框顶, 旗墨由反向旗子副本抵消, 切换环不跳位
  const repeatSvg = iconSvg("ICON_REPEAT");
  assert.ok(page.includes(repeatSvg), "页面默认形与 ICON_REPEAT 不同款");
  svgCentered("ICON_REPEAT (列表循环态)", repeatSvg);
  svgCentered("ICON_REPEAT_ONE (单曲循环态)", iconSvg("ICON_REPEAT_ONE"));
  svgCentered("ICON_SHUFFLE (随机循环态)", iconSvg("ICON_SHUFFLE"));
  // 1.8.111 循环主题重叠门禁: 两态同视框 + 单曲的环与列表逐字节同枚
  assert.ok(iconSvg("ICON_REPEAT_ONE").startsWith(
    repeatSvg.slice(0, repeatSvg.indexOf("d="))), "列表/单曲该共用同一视框");
  assert.ok(iconSvg("ICON_REPEAT_ONE").includes(`d="${iconPath("ICON_REPEAT")}`),
    "单曲的环该与列表同枚 (切换只有徽章显隐)");
  // 1.8.115 徽章右上角钉: 圆片顶点顶到视框 y=0, 「1」反向镂空随圆片就位
  // (1.8.116 「1」绕圆心放大到 ¾ 圆片高, M 点随缩放外移)
  assert.ok(iconPath("ICON_REPEAT_ONE").includes("M907.99 0C1015.01"),
    "徽章圆片该顶到视框顶 (右上角就位)");
  assert.ok(iconPath("ICON_REPEAT_ONE").includes("M973.77 337.75L973.77 48.26"),
    "「1」笔画该是放大款 (圆片里镂空, 1.8.116 ¾ 圆片高)");
  for (const name of ["ICON_REPEAT", "ICON_REPEAT_ONE", "ICON_SHUFFLE"]) {
    const svg = iconSvg(name);
    assert.ok((svg.match(/<path /g) || []).length === 1,
      `${name} 该只有一枚 path (拆多枚半透明下交叉处会叠深)`);
    assert.ok(svg.includes('width="24" height="24"'),
      `${name} 该是 24 号 (28 号比邻键偏大)`);
  }
});
