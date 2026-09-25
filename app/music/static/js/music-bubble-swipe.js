// music-bubble-swipe — My Music 播放气泡手势 (1.8.5 右划返回 + 1.8.94 横滑切歌):
// 气泡是船坞里的固定件 (z50), 盖在推入层 (z44) 上面 —— 层上的右划手势根本
// 收不到它, 1.8.0 层铺满全高后气泡底下的内容全是层, 气泡自己就成了手势
// 死角。一条管线两用: 有层在, 右划拖栈顶层跟手位移 (1.8.5 旧用法, 松手
// 够远或带甩劲就收层); 其余横滑切歌 (1.8.94 用户点名「气泡左右滑动切歌」,
// 上下曲键撤了) —— 1.8.95 (用户点名「滑动的过程中要提前看到下一首」)
// #mini-drag 改摆三张卡 (上一首/当前/下一首) 横排: 拖动整条跟手平移, 邻曲
// 的封面歌名从两侧滑进来提前看到; 松手拖过内容区 28% 或带甩劲就顺势滑满
// 一整张换曲, 此时当前卡已被 renderPlayerChrome 换成邻曲内容 (邻曲卡刚放
// 的同一张图, 早解码好) 瞬移归位, 画面无缝 —— 换没换成用 currentTrack
// 对照, 没换成 (队尾顶住/回本曲开头) 邻曲卡滑走弹回; 那一侧没有邻曲就不
// 滑满原地弹回; 竖向立刻放掉, 不碍气泡自己的点击与滚动。
"use strict";
/* global $, PLACEHOLDER_ARTWORK, closePushStack, currentTrack, onTrackChange,
          paneMotion, playerNext, playerPrevious, pushStack, stageNeighbors */

(function bindBubbleSwipe() {
  const bubble = $("#mini-player");
  const drag = $("#mini-drag");
  const SWITCH_SHARE = 0.28;   // 拖过内容区几成换曲 (3D 舞台同款)
  const SETTLE = "transform .26s cubic-bezier(.25,1,.4,1)";   // 滑满/弹回
  let switching = false;       // 换曲滑满动画期: 新手势不接

  /** 两侧邻曲卡先备货 (封面歌名填好, 没曲的那侧藏掉): onTrackChange 平时
      刷, 拖开再补一次 —— 邻曲封面早解码, 滑进来就见, 归位也不闪旧图。 */
  function fillNeighborCards() {
    const neighbors = stageNeighbors();
    for (const [id, track] of [["mini-card-prev", neighbors.prev],
                               ["mini-card-next", neighbors.next]]) {
      const card = $("#" + id);
      card.classList.toggle("off", !track);
      if (!track) continue;
      const img = card.querySelector("img");
      img.src = track.album_id
        ? `/music/media/albums/${track.album_id}/artwork` : PLACEHOLDER_ARTWORK;
      card.querySelector("b").textContent = track.title;
      card.querySelector("small").textContent = track.artist;
    }
  }
  onTrackChange(fillNeighborCards);

  /** 整条平移 offset 像素: 三张卡一起走, 邻曲卡从对侧跟进视野。 */
  function poseBubble(offset) {
    drag.style.transform = `translateX(${offset}px)`;
  }

  /** 松手换曲: 顺势滑满一整张 (邻曲卡全进) → 换曲 (跟 3D 舞台同款, 用换没
      换成接力: 队尾顶住/回本曲开头 = 没换) → 换成了当前卡已是邻曲内容,
      瞬移归位画面无缝; 没换成从满位滑回中位。那一侧没邻曲就不滑满, 原地
      弹回 (playerNext 的队尾提示照给)。 */
  function commitBubble(direction) {
    switching = true;
    const width = drag.offsetWidth || 1;
    const side = $(direction === "next" ? "#mini-card-next" : "#mini-card-prev");
    if (side.classList.contains("off")) {      // 没邻曲: 不滑向空卡
      if (direction === "next") playerNext();
      else playerPrevious();
      drag.style.transition = SETTLE;
      poseBubble(0);
      setTimeout(() => {
        drag.style.transition = drag.style.transform = "";
        switching = false;
      }, 300);
      return;
    }
    drag.style.transition = SETTLE;
    poseBubble(direction === "next" ? -width : width);
    setTimeout(() => {
      const before = currentTrack;
      if (direction === "next") playerNext();
      else playerPrevious();
      if (currentTrack === before) {           // 没换成: 邻曲卡滑走, 弹回中位
        poseBubble(0);
        setTimeout(() => {
          drag.style.transition = drag.style.transform = "";
          switching = false;
        }, 300);
        return;
      }
      drag.style.transition = "none";          // 换成: 当前卡已是邻曲内容,
      poseBubble(0);                           // 瞬移归位无缝, 不放过渡
      drag.style.transition = drag.style.transform = "";
      switching = false;
    }, 260);
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
        else {
          fillNeighborCards();       // 拖开先备邻曲卡 (onTrackChange 平时刷)
          drag.style.transition = "none";
        }
      }
      if (mode === "layer") {
        paneMotion();                 // 拖动中: 磨砂持续暂撤 (每下续期)
        pane.style.transform = `translateX(${Math.max(0, dx)}px)`;
      } else {
        const width = drag.offsetWidth || 1;
        poseBubble(Math.max(-width, Math.min(width, dx)));  // 跟手 1:1, 一卡封顶
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
        drag.style.transition = SETTLE;
        poseBubble(0);
        setTimeout(() => {
          drag.style.transition = drag.style.transform = "";
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
        drag.style.transition = drag.style.transform = "";
      }
    };
    bubble.addEventListener("pointermove", move, { signal: signals.signal });
    bubble.addEventListener("pointerup", end, { signal: signals.signal });
    bubble.addEventListener("pointercancel", cancel, { signal: signals.signal });
  });
}());
