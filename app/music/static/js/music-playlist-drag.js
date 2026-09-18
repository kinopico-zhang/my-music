// music-playlist-drag — My Music 播放列表详情页曲目拖拽换序 (1.8.17 用户点名
// 「允许调整列表歌曲的顺序」): 队列拖拽 (music-player-queue-view) 同款手感 ——
// 按住行右缘把手上下拖, 被拖行跟手 (transform), 其余行让位平移, 松手按落点落定。
// 行住 .swipe-wrap 里 (与左滑删除同构): 1.8.19 起被拖的/被抬层的都是 wrap ——
// wrap overflow:hidden (左滑删除的裁切), 行在 wrap 里竖移出界会被裁得只剩
// 一截黑边 (行自己的 z-index 翻不出裁切); 拖动只认把手, 列表照常滚。
"use strict";
/* exported bindPlaylistDrag */

let playlistDrag = null;
let playlistDragSwallowClick = false;   // 松手落定的尾随 click 吞掉 (不开播)

/** 绑到曲目容器 (#playlist-tracks) 上; reorder(from, to) 由调用方持久化
    (PUT 全量新顺序) 并同步自己的曲目数组。 */
function bindPlaylistDrag(container, reorder) {
  container.addEventListener("pointerdown", (event) => {
    const grip = event.target.closest(".pl-grip");
    if (!grip || playlistDrag) return;
    const wrap = grip.closest(".swipe-wrap");
    const wraps = [...container.querySelectorAll(".swipe-wrap")];
    const index = wraps.indexOf(wrap);
    const row = wrap ? wrap.querySelector("button") : null;
    if (!wrap || !row || index < 0 || row.classList.contains("revealed")) return;
    event.preventDefault();                       // 把手按下就是拖, 不当点击
    grip.setPointerCapture(event.pointerId);      // 移出把手事件也不丢
    playlistDrag = { wrap, wraps, row, from: index, target: index,
                     rowH: wrap.offsetHeight || 1, startY: event.clientY,
                     moved: false };
    wrap.classList.add("dragging");   // 位移/抬层都落在 wrap (行翻不出裁切)
  });
  container.addEventListener("pointermove", (event) => {
    const drag = playlistDrag;
    if (!drag) return;
    const dy = event.clientY - drag.startY;
    if (!drag.moved) {
      if (Math.abs(dy) < 6) return;
      drag.moved = true;
    }
    drag.wrap.style.transform = `translateY(${dy}px)`;   // 被拖行跟手
    // 目标位 = 起始下标 + 拖过的行数: 只认拖动距离, 不认绝对坐标 —— 绝对
    // 坐标相对整个 offsetParent (头图/操作排的全高都记进来), 一动就整体
    // 偏出去, 让位乱跳 (1.8.18 修的正是这个: 行距均匀, 距离换算就可靠)
    drag.target = Math.max(0, Math.min(drag.wraps.length - 1,
        drag.from + Math.round(dy / drag.rowH)));
    drag.wraps.forEach((wrap, index) => {               // 其余行让位
      if (wrap === drag.wrap) return;
      let shift = 0;
      if (drag.target > drag.from) {
        if (index > drag.from && index <= drag.target) shift = -drag.rowH;
      } else if (drag.target < drag.from) {
        if (index >= drag.target && index < drag.from) shift = drag.rowH;
      }
      wrap.style.transform = shift ? `translateY(${shift}px)` : "";
    });
  });
  const finish = async (cancelled) => {
    const drag = playlistDrag;
    playlistDrag = null;
    if (!drag) return;
    // 清位移时 .dragging 还挂着 (transition none) —— 与队列同款, 落定不弹跳
    drag.wrap.style.transform = "";
    drag.wrap.classList.remove("dragging");
    drag.wraps.forEach((wrap) => { wrap.style.transform = ""; });
    if (cancelled || !drag.moved || drag.target === drag.from) return;
    playlistDragSwallowClick = true;
    // 先把 wrap 挪到落点位 (滚动位置纹丝不动), 再交给调用方持久化
    const reference = drag.target === drag.wraps.length - 1 ? null
      : drag.wraps[drag.target + (drag.target > drag.from ? 1 : 0)];
    container.insertBefore(drag.wrap, reference);
    await reorder(drag.from, drag.target);
  };
  container.addEventListener("pointerup", () => finish(false));
  container.addEventListener("pointercancel", () => finish(true));
  container.addEventListener("click", (event) => {
    if (playlistDragSwallowClick) {
      playlistDragSwallowClick = false;
      event.stopPropagation();               // 拖完的尾随 click 别开播
    }
  }, true);
}
