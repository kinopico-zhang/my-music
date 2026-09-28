// music-client — 客户端识别 (1.8.35 单轴 mobile/desktop → 1.8.103 双轴
// 拆分, 用户点名「按屏幕尺寸分手机小/PC 大, 尺寸只影响布局; 按操作逻辑
// 分键鼠/触摸, PC 键鼠下优化触摸逻辑; 用浏览器信息判定」): 两条正交轴
// 各写各的, 互不牵连 ——
//   data-size="small|large"    布局轴: 视口宽 ≥700px 走大屏布局, 窗口
//     拖宽/缩窄跟着换。样式收在 music-large.css (作用域一律
//     html[data-size="large"]), 只动布局 (内容列宽/网格列数/播放页列宽);
//     手机窄屏是无前缀基线, 一个字节不动。
//   data-input="touch|keymouse" 操作轴: 主指针粗细优先 (触屏手机/平板的
//     主指针都是 coarse, 带鼠标的桌面是 fine), UA 兜底 (iPad 桌面模式
//     伪装 Mac 时主指针仍是粗的), 插拔鼠标跟着换。样式收在
//     music-desktop.css (作用域一律 html[data-input="keymouse"]), 只动
//     操作手感 (光标/悬停/键盘快捷键/音量/行距密度); 触摸是基线不动。
// 两轴独立翻转: iPad = 大屏 + 触摸; PC 拖窄窗口 = 小屏 + 键鼠。
// ?ui= 预览覆写: phone/pc 两轴一起强制, touch/keymouse 只强制操作轴
// (布局照旧跟视口走, PC 上可预览 iPad 形态); 旧值 mobile/desktop 照认
// (映射 phone/pc)。
// 拆轴的动机 (用户点名): 之后键鼠操作的改动全走操作轴, 手机触屏体验
// 零波及。
"use strict";
/* exported classifyInput, classifySize, inputKind, isKeyMouseInput,
            isLargeSize, normalizeOverride, sizeKind */

const SIZE_WIDE_QUERY = "(min-width: 700px)";   // 与大屏布局同一把尺

/**
 * 布局轴 (纯函数, node --test 直测)。
 * @param {boolean} wideViewport matchMedia("(min-width: 700px)").matches
 * @param {string} override      ?ui= 归一后的值 (phone|pc|touch|keymouse|乱值)
 * @returns {"small"|"large"}
 */
function classifySize(wideViewport, override) {
  if (override === "phone") return "small";     // 覆写只认 phone/pc
  if (override === "pc") return "large";        // (touch/keymouse 只管操作轴)
  return wideViewport ? "large" : "small";
}

/**
 * 操作轴 (纯函数): 覆写最优先 → 主指针粗细 → UA 兜底。
 * @param {boolean} coarsePointer matchMedia("(pointer: coarse)").matches
 * @param {string} userAgent      navigator.userAgent
 * @param {string} override       ?ui= 归一后的值
 * @returns {"touch"|"keymouse"}
 */
function classifyInput(coarsePointer, userAgent, override) {
  if (override === "phone" || override === "touch") return "touch";
  if (override === "pc" || override === "keymouse") return "keymouse";
  if (coarsePointer) return "touch";   // 主指针是触屏: 手机/平板走触摸
  if (/iPhone|iPad|iPod|Android|Mobile/i.test(userAgent)) return "touch";
  return "keymouse";
}

/** ?ui= 旧值归一 (1.8.35–1.8.102 用的 mobile/desktop), 新值原样过。 */
function normalizeOverride(raw) {
  if (raw === "mobile") return "phone";
  if (raw === "desktop") return "pc";
  return raw;
}

/** 页面接线: 写 <html data-size / data-input>, 两条轴各自跟着自家的
    浏览器信号换 (窗口宽度 ↔ 主指针粗细)。 */
function applyClientAxes() {
  let raw = "";
  try {
    raw = new URLSearchParams(window.location.search).get("ui") || "";
  } catch (error) { /* location.search 异常按没有覆盖参处理 */ }
  const override = normalizeOverride(raw);
  const root = document.documentElement;
  root.dataset.size = classifySize(
    window.matchMedia(SIZE_WIDE_QUERY).matches, override);
  root.dataset.input = classifyInput(
    window.matchMedia("(pointer: coarse)").matches, navigator.userAgent,
    override);
}

/** 当前布局档 ("small"|"large"); 识别没跑过时按小屏兜底。 */
function sizeKind() {
  return document.documentElement.dataset.size === "large"
    ? "large" : "small";
}

/** 是否大屏布局 (布局轴的 JS 分叉入口)。 */
function isLargeSize() {
  return sizeKind() === "large";
}

/** 当前操作档 ("touch"|"keymouse"); 识别没跑过时按触摸兜底。 */
function inputKind() {
  return document.documentElement.dataset.input === "keymouse"
    ? "keymouse" : "touch";
}

/** 是否键鼠 (操作轴的 JS 分叉入口: if (isKeyMouseInput()) { …键鼠行为… })。 */
function isKeyMouseInput() {
  return inputKind() === "keymouse";
}

if (typeof window !== "undefined" && window.document) {
  applyClientAxes();
  window.matchMedia(SIZE_WIDE_QUERY)
    .addEventListener("change", applyClientAxes);   // 窗口拖宽/缩窄
  window.matchMedia("(pointer: coarse)")
    .addEventListener("change", applyClientAxes);   // 插拔鼠标/平板模式翻转
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { classifyInput, classifySize, inputKind, isKeyMouseInput,
                     isLargeSize, normalizeOverride, sizeKind };
}
