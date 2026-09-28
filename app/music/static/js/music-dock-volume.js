// music-dock-volume — 船坞音量气泡 (1.8.103, 用户点名「非移动端底下
// 除了菜单/播放气泡/搜索, 再加一个音量调节气泡, 点击后可以调节音量」):
// 键鼠端专属 —— 挂操作轴 data-input=keymouse (music-client.js 双轴拆分
// 后这层的第一个新功能), 触摸端基线整个不显示 (音量归系统硬件键,
// iOS 的 audio.volume 只读)。点船坞音量键在键上方弹一枚小气泡, 拖条
// 调音量; 落地走 music-desktop-keys.js 的 setDesktopVolume (全应用唯一
// 事实源 —— 播放页音量条 / 船坞气泡 / ↑↓ 键三处同源, 拖谁其余两处跟着
// 走, 记档 localStorage)。Esc 收层进 music-global-events.js 的链头。
"use strict";
/* global $, setDesktopVolume */

/** 气泡定位: 右缘对齐音量键, 往左展开 (键 46px 条 ~160px); 出屏收边。 */
function placeVolumePop(pop, button) {
  const rect = button.getBoundingClientRect();
  pop.style.left = `${Math.max(8, rect.right - pop.offsetWidth)}px`;
}

function bindDockVolume() {
  const button = $("#dock-volume");
  const pop = $("#volume-pop");
  const range = $("#dock-volume-range");
  if (!button || !pop || !range) return;
  button.addEventListener("click", () => {
    pop.hidden = !pop.hidden;
    if (!pop.hidden) placeVolumePop(pop, button);   // 量完宽再定位 (藏着量不出)
  });
  range.addEventListener("input", () => {
    setDesktopVolume(Number(range.value) / 100);
  });
  // 点气泡外收气泡 (不挡那一击 —— 点船坞菜单键同时收气泡+开菜单, 一击两得)
  document.addEventListener("pointerdown", (event) => {
    if (pop.hidden) return;
    if (!event.target.closest("#volume-pop, #dock-volume")) pop.hidden = true;
  });
  // 窗口变形 (拖宽/缩放) 后锚点挪了: 收掉, 下回打开重定位
  window.addEventListener("resize", () => { pop.hidden = true; });
}

bindDockVolume();
