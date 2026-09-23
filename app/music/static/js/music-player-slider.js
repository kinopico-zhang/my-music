// music-player-slider — My Music 滑杆命中区增强: 进度条轨道只有 7px,
// 手指按不准 —— 外面垫一层 28px 高的拖拽面, 指针走到哪值跟到哪。
// 拆自 music-player-audio-events (1.8.76: audio 元素事件与滑杆 DOM 增强
// 分家 —— 两边都顶着 200 行帽, 按逻辑再切一刀, 代码逐字节未动)。
"use strict";
/* exported enhanceSliderTouch */

function enhanceSliderTouch(input) {
  const wrap = document.createElement("div");
  wrap.className = "slider-hit";
  input.replaceWith(wrap);
  wrap.appendChild(input);
  let dragging = false;
  const apply = (clientX) => {
    const rect = wrap.getBoundingClientRect();
    if (rect.width <= 0) return;
    const min = Number(input.min);
    const max = Number(input.max);
    const ratio = Math.min(1, Math.max(0, (clientX - rect.left) / rect.width));
    input.value = String(Math.round(min + ratio * (max - min)));
    input.dispatchEvent(new Event("input", { bubbles: true }));
  };
  wrap.addEventListener("pointerdown", (event) => {
    dragging = true;
    event.preventDefault();               // 别触发文字选择/页面滚动
    wrap.setPointerCapture(event.pointerId);
    apply(event.clientX);
  });
  wrap.addEventListener("pointermove", (event) => {
    if (dragging) apply(event.clientX);
  });
  const release = () => {
    if (!dragging) return;
    dragging = false;
    input.dispatchEvent(new Event("change", { bubbles: true }));
  };
  wrap.addEventListener("pointerup", release);
  wrap.addEventListener("pointercancel", release);
  // 释放的兜底: 指针捕获万一失灵 (老 WebKit/系统手势抢走), pointerup
  // 落不到垫子上 —— scrubbing 会卡在 true, timeupdate 从此不刷时间,
  // 进度显示冻在拖动那格。窗口级再接一次 (垫子上已释放过就空跑)。
  window.addEventListener("pointerup", release);
  window.addEventListener("pointercancel", release);
}
