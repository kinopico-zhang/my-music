// music-desktop-keys — 桌面端键盘层 (1.8.39, 用户点名「优化桌面 ui, 适配
// 键鼠操作」): 空格 播/停, 左右箭头 上一首/下一首 (与播放页两颗钮同一套
// 语义: 播过 3 秒先回本曲开头), / 直达搜索 —— 只在桌面端挂 (1.8.35 的
// isDesktopClient); 手机没有键盘, 蓝牙键盘的键也留给输入。Esc 依序收层
// 那套电脑手机共用, 住在 music-global-events.js。
// 让路规矩: 焦点在输入框/按钮上时键归控件 (空格该点按钮、箭头该拖进度
// 条); 弹着的菜单 (船坞/长按/封面) 开着时不抢键。
"use strict";
/* global $, isDesktopClient, playerNext, playerPrevious, playerToggle */

function bindDesktopKeys() {
  if (!isDesktopClient()) return;   // 移动端不挂 (识别见 music-client.js)
  document.addEventListener("keydown", (event) => {
    if (event.repeat || event.ctrlKey || event.metaKey || event.altKey) return;
    const el = document.activeElement;
    if (el && el.closest("input, textarea, select, button, a, [contenteditable]")) {
      return;                       // 焦点在控件上: 键归控件
    }
    if (!$("#pop-menu").hidden || !$("#track-menu").hidden
        || !$("#cover-menu").hidden) return;
    if (event.key === " ") {
      event.preventDefault();
      playerToggle();
    } else if (event.key === "ArrowLeft") {
      event.preventDefault();
      playerPrevious();
    } else if (event.key === "ArrowRight") {
      event.preventDefault();
      playerNext();
    } else if (event.key === "/") {
      event.preventDefault();
      $("#dock-search").click();    // 复用船坞搜索键接线 (导航 + 聚焦输入框)
    }
  });
}

bindDesktopKeys();
