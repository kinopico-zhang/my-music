// music-desktop-keys — 桌面端键盘层 (1.8.39, 用户点名「优化桌面 ui, 适配
// 键鼠操作」): 空格 播/停, / 直达搜索, Esc 依序收层 (那套电脑手机共用,
// 住在 music-global-events.js)。1.8.102 键位补全 (用户实报「PC Chrome
// 打开并没有适配键鼠」): 左右箭头改按桌面惯例快退/快进 (1.8.39 原是
// 切歌, 电脑上别扭), 切歌让给 Shift+左右 (与播放页两颗钮同一套语义:
// 播过 3 秒先回本曲开头); 上下箭头调音量 —— 全应用原先一根音量控制都
// 没有, 手机上音量归硬件键没感觉, 电脑上就是「没适配」。只在桌面端挂
// (1.8.35 的 isDesktopClient); 手机没有键盘, 蓝牙键盘的键也留给输入。
// 让路规矩 (1.8.102 收紧): 焦点在真输入控件 (输入框/下拉/进度·音量条/
// 可编辑) 上时键归控件; 点过的按钮/链接不再吞键 —— Windows Chrome 点按
// 即聚焦, 焦点停在钮上时空格/箭头全哑, 整个键盘层形同虚设。弹着的菜单
// (船坞/长按/封面) 开着时不抢键。
"use strict";
/* global $, isDesktopClient, playbackDuration, playerNext, playerPrevious,
          playerToggle */

const DESKTOP_SEEK_S = 10;        // ←/→ 一步 10 秒
const DESKTOP_VOLUME_STEP = 0.05; // ↑/↓ 一步 5%

function clampNumber(value, low, high) {
  return Math.min(high, Math.max(low, value));
}

/** 音量落地: 元素 + 音量条 (值与填充) + 记档。只在桌面端被调 —— iOS 的
    audio.volume 只读, 移动端音量归系统硬件键, 这层根本不挂。 */
function setDesktopVolume(value) {
  const audio = $("#audio");
  audio.volume = clampNumber(value, 0, 1);
  const percent = Math.round(audio.volume * 100);
  const slider = $("#fp-volume");
  if (slider) {
    slider.value = String(percent);
    slider.style.setProperty("--fill", `${percent}%`);
  }
  try { localStorage.setItem("music-volume", String(audio.volume)); }
  catch (_error) { /* 记不了档: 只影响下次打开的初始音量 */ }
}

function bindDesktopKeys() {
  if (!isDesktopClient()) return;   // 移动端不挂 (识别见 music-client.js)
  // 上次的音量接着用 (没记档/读不了 = 满音量)
  let saved = Number.NaN;
  try {
    const raw = localStorage.getItem("music-volume");
    if (raw !== null) saved = Number(raw);
  } catch (_error) { /* 隐私模式等读不了: 按满音量 */ }
  setDesktopVolume(Number.isFinite(saved) ? saved : 1);
  const volumeSlider = $("#fp-volume");
  if (volumeSlider) volumeSlider.addEventListener("input", () => {
    setDesktopVolume(Number(volumeSlider.value) / 100);
  });
  document.addEventListener("keydown", (event) => {
    if (event.repeat || event.ctrlKey || event.metaKey || event.altKey) return;
    const el = document.activeElement;
    if (el && el.closest("input, textarea, select, [contenteditable]")) {
      return;                       // 焦点在输入控件上: 键归控件
    }
    if (!$("#pop-menu").hidden || !$("#track-menu").hidden
        || !$("#cover-menu").hidden) return;
    const audio = $("#audio");
    if (event.key === " ") {
      event.preventDefault();
      playerToggle();
    } else if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
      event.preventDefault();
      if (event.shiftKey) {         // Shift+左右: 切歌
        if (event.key === "ArrowLeft") playerPrevious();
        else playerNext();
        return;
      }
      const total = playbackDuration();
      if (total > 0) {              // 左右: 快退/快进 (尾部留 0.2s 不顶到 ended)
        const step = event.key === "ArrowLeft" ? -DESKTOP_SEEK_S : DESKTOP_SEEK_S;
        audio.currentTime = clampNumber(audio.currentTime + step, 0, total - 0.2);
      }
    } else if (event.key === "ArrowUp" || event.key === "ArrowDown") {
      event.preventDefault();
      setDesktopVolume(audio.volume
        + (event.key === "ArrowUp" ? DESKTOP_VOLUME_STEP : -DESKTOP_VOLUME_STEP));
    } else if (event.key === "/") {
      event.preventDefault();
      $("#dock-search").click();    // 复用船坞搜索键接线 (导航 + 聚焦输入框)
    }
  });
}

bindDesktopKeys();
