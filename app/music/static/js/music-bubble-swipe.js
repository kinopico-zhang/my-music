// music-bubble-swipe — My Music 播放气泡手势 (1.8.94 横滑切歌):
// 气泡是船坞里的固定件 (z50), 盖在推入层 (z44) 上面。1.8.5 曾让「有层在,
// 右划拖栈顶层收层」, 1.8.94 横滑改成切歌后两种语义打架: 想切上一首却把
// 底下的页面收了。1.8.96 (用户点名「第一首右划该橡皮筋, 别让底部页面把
// 事件收走退页」) 分家: 气泡的横滑只管切歌 (收页划页面本身就行),
// #mini-drag 摆三张卡 (上一首/当前/下一首) 横排, 拖动整条跟手平移, 邻曲
// 的封面歌名从两侧滑进来提前看到 (1.8.95); 那一侧没有邻曲 (第一首/最后
// 一首) 拖不动, 只跟三成还封顶 —— 橡皮筋, 松手弹回也不触发任何切歌;
// 松手拖过内容区 28% 或带甩劲就顺势滑满一整张换曲, 此时当前卡已被
// renderPlayerChrome 换成邻曲内容 (邻曲卡刚放的同一张图, 早解码好) 瞬移
// 归位, 画面无缝 —— 换没换成用 currentTrack 对照, 没换成 (回本曲开头)
// 邻曲卡滑走弹回; 竖向立刻放掉, 不碍气泡自己的点击与滚动。
"use strict";
/* global $, PLACEHOLDER_ARTWORK, currentTrack, onTrackChange,
          playerNext, playerPrevious, stageNeighbors */

(function bindBubbleSwipe() {
  const bubble = $("#mini-player");
  const drag = $("#mini-drag");
  const prevCard = $("#mini-card-prev");
  const nextCard = $("#mini-card-next");
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

  /** 弹回中位 (没拖够 / 那侧没邻曲的橡皮筋收场)。 */
  function springBack() {
    drag.style.transition = SETTLE;
    poseBubble(0);
    setTimeout(() => {
      drag.style.transition = drag.style.transform = "";
    }, 300);
  }

  /** 松手换曲 (那侧必有邻曲, end 里查过): 顺势滑满一整张 (邻曲卡全进) →
      换曲 (跟 3D 舞台同款, 用换没换成接力: 回本曲开头 = 没换) → 换成了
      当前卡已是邻曲内容, 瞬移归位画面无缝; 没换成从满位滑回中位。 */
  function commitBubble(direction) {
    switching = true;
    const width = drag.offsetWidth || 1;
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
    const startX = event.clientX;
    const startY = event.clientY;
    let claimed = false;   // 横滑已认领 (竖向放掉还给气泡)
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
      if (!claimed) {
        if (Math.abs(dx) < 10 && Math.abs(ev.clientY - startY) < 10) return;
        if (Math.abs(ev.clientY - startY) >= Math.abs(dx)) {
          cleanup();                 // 竖向: 还给气泡
          return;
        }
        claimed = true;              // 横滑一律切歌 (1.8.96 撤收层联动)
        bubble.setPointerCapture(ev.pointerId);
        fillNeighborCards();         // 拖开先备邻曲卡 (onTrackChange 平时刷)
        drag.style.transition = "none";
      }
      const width = drag.offsetWidth || 1;
      let offset = Math.max(-width, Math.min(width, dx));   // 跟手 1:1, 一卡封顶
      const side = dx < 0 ? nextCard : prevCard;
      if (side.classList.contains("off")) {   // 那侧没邻曲: 橡皮筋拖不动
        offset = Math.sign(dx) * Math.min(44, Math.abs(dx) * 0.3);
      }
      poseBubble(offset);
    };
    const end = () => {
      cleanup();
      if (!claimed) return;
      const width = drag.offsetWidth || 1;
      const d = Math.max(-1, Math.min(1, (lastX - startX) / width));
      const flick = Math.abs(velocity) > 0.5 && Math.abs(lastX - startX) > 30;
      const goNext = d <= -SWITCH_SHARE || (flick && velocity < 0);
      const goPrev = d >= SWITCH_SHARE || (flick && velocity > 0);
      if (goNext && !nextCard.classList.contains("off")) commitBubble("next");
      else if (goPrev && !prevCard.classList.contains("off")) commitBubble("prev");
      else springBack();   // 没拖够 / 那侧没邻曲: 弹回, 不动歌
    };
    const cancel = () => {
      cleanup();
      if (!claimed) return;
      drag.style.transition = "none";
      poseBubble(0);
      drag.style.transition = drag.style.transform = "";
    };
    bubble.addEventListener("pointermove", move, { signal: signals.signal });
    bubble.addEventListener("pointerup", end, { signal: signals.signal });
    bubble.addEventListener("pointercancel", cancel, { signal: signals.signal });
  });
}());
