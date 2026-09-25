// music-bubble-swipe — My Music 播放气泡手势 (1.8.5 右划返回 + 1.8.94 横滑切歌):
// 气泡是船坞里的固定件 (z50), 盖在推入层 (z44) 上面 —— 层上的右划手势根本
// 收不到它, 1.8.0 层铺满全高后气泡底下的内容全是层, 气泡自己就成了手势
// 死角。一条管线两用: 有层在, 右划拖栈顶层跟手位移 (1.8.5 旧用法, 松手
// 够远或带甩劲就收层); 其余横滑切歌 (1.8.94 用户点名「气泡左右滑动切歌」,
// 上下曲键撤了) —— 封面文字整块跟手平移, 松手拖过内容区 28% 或带甩劲
// 就顺势滑出换曲、新歌从对侧滑进 (3D 舞台同款口径); 没换成 (队尾顶住/
// 回本曲开头) 原侧弹回; 竖向立刻放掉, 不碍气泡自己的点击与滚动。
"use strict";
/* global $, closePushStack, currentTrack, paneMotion, playerNext,
          playerPrevious, pushStack */

(function bindBubbleSwipe() {
  const bubble = $("#mini-player");
  const drag = $("#mini-drag");
  const SWITCH_SHARE = 0.28;   // 拖过内容区几成换曲 (3D 舞台同款)
  const IN_CURVE = "transform .28s cubic-bezier(.25,1,.4,1), opacity .2s ease";
  let switching = false;       // 换曲滑出/滑进动画期: 新手势不接

  /** 内容平移 offset 像素, 随出屏程度变淡 (满程剩 0.65, 给滑出垫底)。 */
  function poseBubble(offset) {
    drag.style.transform = `translateX(${offset}px)`;
    const width = drag.offsetWidth || 1;
    drag.style.opacity = String(1 - Math.min(1, Math.abs(offset) / width) * 0.35);
  }

  /** 松手换曲: 顺势滑出 → 换曲 (跟 3D 舞台同款, 用换没换来接力动画:
      队尾顶住/回本曲开头 = 没换) → 换成了新歌从对侧滑进, 没换成原侧弹回。 */
  function commitBubble(direction) {
    switching = true;
    const out = (drag.offsetWidth || 1) * 1.05;   // 出屏距离 (略过界防露边)
    drag.style.transition = "transform .17s ease-in, opacity .15s ease-in";
    poseBubble(direction === "next" ? -out : out);
    setTimeout(() => {
      const before = currentTrack;
      if (direction === "next") playerNext();
      else playerPrevious();
      const changed = currentTrack !== before;
      drag.style.transition = "none";
      poseBubble(changed ? (direction === "next" ? out * 0.45 : -out * 0.45)
                         : (direction === "next" ? -out : out));
      void drag.offsetWidth;               // 起跳位先落地, 再放过渡
      drag.style.transition = IN_CURVE;
      poseBubble(0);
      setTimeout(() => {                   // 收尾: 内联清干净, 不压后场过渡
        drag.style.transition = drag.style.transform = drag.style.opacity = "";
        switching = false;
      }, 300);
    }, 170);
  }

  bubble.addEventListener("pointerdown", (event) => {
    if (event.pointerType === "mouse" && event.button !== 0) return;
    if (switching) return;
    const pane = pushStack.length ? pushStack[pushStack.length - 1].pane : null;
    const startX = event.clientX;
    const startY = event.clientY;
    let mode = "";        // "" 未定 / "layer" 拖层 / "track" 拖歌
    let lastX = startX;
    let lastT = event.timeStamp;
    let velocity = 0;     // px/ms, 松手那刻的横向甩速
    const signals = new AbortController();
    const cleanup = () => signals.abort();
    const move = (ev) => {
      const dx = ev.clientX - startX;
      if (ev.timeStamp > lastT) {
        velocity = (ev.clientX - lastX) / (ev.timeStamp - lastT);
      }
      lastX = ev.clientX;
      lastT = ev.timeStamp;
      if (!mode) {
        if (Math.abs(dx) < 10 && Math.abs(ev.clientY - startY) < 10) return;
        if (Math.abs(ev.clientY - startY) >= Math.abs(dx)) {
          cleanup();                 // 竖向: 还给气泡
          return;
        }
        mode = dx > 0 && pane ? "layer" : "track";   // 有层右划收层, 其余切歌
        bubble.setPointerCapture(ev.pointerId);
        if (mode === "layer") pane.style.transition = "none";
        else drag.style.transition = "none";
      }
      if (mode === "layer") {
        paneMotion();                 // 拖动中: 磨砂持续暂撤 (每下续期)
        pane.style.transform = `translateX(${Math.max(0, dx)}px)`;
      } else {
        const out = (drag.offsetWidth || 1) * 1.05;
        poseBubble(Math.max(-out, Math.min(out, dx)));   // 跟手 1:1, 出屏封顶
      }
    };
    const end = (ev) => {
      cleanup();
      if (!mode) return;
      if (mode === "layer") {
        const dx = Math.max(0, lastX - startX);
        const width = pane.offsetWidth || 1;
        const flick = ev.timeStamp - lastT < 100 && lastX - startX > 40;
        pane.style.transition = "";
        pane.style.transform = "";
        if (dx <= width / 3 && !flick) {
          paneMotion();               // 弹回也是一段运动, 磨砂照旧暂撤
          return;
        }
        closePushStack(pushStack.length - 1);   // 只收顶层 (Esc 同款走法)
        return;
      }
      const width = drag.offsetWidth || 1;
      const d = Math.max(-1, Math.min(1, (lastX - startX) / width));
      const flick = Math.abs(velocity) > 0.5 && Math.abs(lastX - startX) > 30;
      if (d <= -SWITCH_SHARE || (flick && velocity < 0)) commitBubble("next");
      else if (d >= SWITCH_SHARE || (flick && velocity > 0)) commitBubble("prev");
      else {                          // 没拖够: 弹回
        drag.style.transition = IN_CURVE;
        poseBubble(0);
        setTimeout(() => {
          drag.style.transition = drag.style.transform = drag.style.opacity = "";
        }, 300);
      }
    };
    const cancel = () => {
      cleanup();
      if (mode === "layer") {
        paneMotion();
        pane.style.transition = "";
        pane.style.transform = "";
      } else if (mode === "track") {
        drag.style.transition = "none";
        poseBubble(0);
        drag.style.transition = drag.style.transform = drag.style.opacity = "";
      }
    };
    bubble.addEventListener("pointermove", move, { signal: signals.signal });
    bubble.addEventListener("pointerup", end, { signal: signals.signal });
    bubble.addEventListener("pointercancel", cancel, { signal: signals.signal });
  });
}());
