// music-client — 客户端识别 (1.8.35, 用户点名「前端要判断客户端是移动端
// 还是 PC 端, 以后两端设计不一样, 先把架构调好」): 启动即把 mobile/desktop
// 写进 <html data-client>, CSS 以 html[data-client="desktop"] 作用域分叉
// (桌面端样式收在 music-desktop.css, 移动端样式保持默认基线不动), JS 走
// clientKind()/isDesktopClient() 分叉。
// 判定口径: 主指针粗细优先 (触屏手机/平板的主指针都是 coarse, 带鼠标的
// 桌面是 fine), UA 兜底 (iPad 桌面模式伪装 Mac 时主指针仍是粗的);
// ?ui=mobile|desktop 强制覆盖 (真机预览另一端的样子)。
"use strict";
/* exported classifyClient, clientKind, isDesktopClient */

/**
 * 判定客户端类型 (纯函数, node --test 直测)。
 * @param {boolean} coarsePointer matchMedia("(pointer: coarse)").matches
 * @param {string} userAgent      navigator.userAgent
 * @param {string} override       ?ui= 参数值 ("mobile"|"desktop"|空串/乱值)
 * @returns {"mobile"|"desktop"} 客户端类型
 */
function classifyClient(coarsePointer, userAgent, override) {
  if (override === "mobile" || override === "desktop") return override;
  if (coarsePointer) return "mobile";    // 主指针是触屏: 手机/平板走移动端
  if (/iPhone|iPad|iPod|Android|Mobile/i.test(userAgent)) return "mobile";
  return "desktop";
}

/** 页面接线: 写 <html data-client>, 主指针变了 (插拔鼠标/平板模式翻转) 跟着换。 */
function applyClientKind() {
  let override = "";
  try {
    override = new URLSearchParams(window.location.search).get("ui") || "";
  } catch (error) { /* location.search 异常按没有覆盖参处理 */ }
  document.documentElement.dataset.client = classifyClient(
    window.matchMedia("(pointer: coarse)").matches,
    navigator.userAgent, override);
}

/** 当前客户端 ("mobile"|"desktop"); 识别没跑过时按移动端兜底。 */
function clientKind() {
  return document.documentElement.dataset.client === "desktop"
    ? "desktop" : "mobile";
}

/** 是否桌面端 (JS 分叉入口: if (isDesktopClient()) { …桌面行为… })。 */
function isDesktopClient() {
  return clientKind() === "desktop";
}

if (typeof window !== "undefined" && window.document) {
  applyClientKind();
  window.matchMedia("(pointer: coarse)").addEventListener("change", applyClientKind);
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { classifyClient, clientKind, isDesktopClient };
}
