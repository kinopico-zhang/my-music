// music-player-queue-view — My Music 队列视图 (占封面区): 翻开/重排/拖把拖拽换序/左滑删除。
// 拆自 music-player.js (结构化重构: 代码逐字节未动, 按 music.html 里的顺序加载, 跨模块引用走全局)。
"use strict";
/* global $, ICON_BARS, ICON_GRIP, bindSwipeDelete, escapeHTML, lyricsViewOpen,
          playQueue, playerCurrentTrackId, queueDrag: writable, queueRemove,
          queueReorder, queueUpcoming, queueViewOpen: writable, savePlayerState,
          toast, toggleLyricsView */
/* exported bindQueueDrag, bindQueueSwipeDelete, closeQueueView, renderQueueView,
            toggleQueueView */

// ------------------------------------------------------------ 队列视图 (占封面区)

/** 点队列键: 封面原地翻开成播放队列 (顶排 随机/循环 + upcoming 列表)。
    封面区就一块地方 —— 歌词开着先让歌词收掉。(开合状态 queueViewOpen
    声明在文件顶部: 前面的收起函数也要引用它。) */
function closeQueueView() {
  queueViewOpen = false;
  $("#fp-queue").hidden = true;
  $("#fp-art-wrap").hidden = false;
  $("#fp-queue-btn").classList.remove("on");
  $("#full-player").classList.remove("queue");
}

function toggleQueueView() {
  if (queueViewOpen) { closeQueueView(); return; }
  if (lyricsViewOpen) toggleLyricsView();   // 同住封面区, 二选一
  queueViewOpen = true;
  renderQueueView();
  $("#fp-art-wrap").hidden = true;
  $("#fp-queue").hidden = false;
  $("#fp-queue-btn").classList.add("on");
  $("#full-player").classList.add("queue");
}

function renderQueueView() {
  if (!playQueue) return;
  const upcoming = queueUpcoming(playQueue);
  const currentId = playerCurrentTrackId();
  $("#fq-count").textContent = `${upcoming.length} 首歌曲`;
  // 当前曲 eq 动条, 其余接续编号 (当前算 1); 右缘拖拽把手按住上下拖换顺序。
  // 1.8.27 行套 .swipe-wrap (左滑删除, 用户点名「所有列表都这样」—— 队列
  // 是最后一个没壳的列表); data-queue-pos 记 order 绝对位 (视图下标 0 =
  // order[position]), 删行/换序都按它换算
  $("#queue-list").innerHTML = upcoming.map((track, index) => {
    const on = track.track_id === currentId;
    return `
    <div class="swipe-wrap" data-queue-pos="${Math.max(0, playQueue.position) + index}">
      <button class="queue-row${on ? " on" : ""}"
              data-queue-track-id="${track.track_id}">
        <span class="q-lead">${on ? ICON_BARS
          : `<i class="q-num">${index + 1}</i>`}</span>
        <span class="q-title">${escapeHTML(track.title)}</span>
        <span class="q-artist">${escapeHTML(track.artist)}</span>
        <span class="q-grip" aria-hidden="true">${ICON_GRIP}</span>
      </button>
      <button class="swipe-del" aria-label="从队列移除">删除</button>
    </div>`;
  }).join("") || '<div class="lyrics-empty">队列是空的</div>';
}

// 拖拽换位: 按住右缘把手上下拖 —— 被拖行跟手 (transform), 其余行让位平移;
// 松手按落点改 order (当前曲位照旧由 queueReorder 兜住)。把手 touch-action:
// none, 拖把不滚列表; 行本身 pan-y, 列表照常滚。视图下标 0 = order[position]。
// 1.8.27 被拖的/被抬层的都改成 wrap (行住 .swipe-wrap 里, 左滑删除同构;
// 播列表详情页同款): wrap overflow:hidden, 行在 wrap 里竖移出界会被裁;
// 落点位 = 起始下标 + 拖过的行数 (距离换算, 不认 offsetTop 绝对坐标 ——
// 相对布局一动就让位乱跳, 1.8.18 的教训)。
function finishQueueDrag(cancelled) {
  const drag = queueDrag;
  queueDrag = null;
  if (!drag) return;
  drag.wrap.classList.remove("dragging");
  drag.wraps.forEach((wrap) => { wrap.style.transform = ""; });
  if (cancelled || !drag.moved || drag.target === undefined
      || drag.target === drag.fromView || !playQueue) return;
  const base = Math.max(0, playQueue.position);
  if (queueReorder(playQueue, base + drag.fromView, base + drag.target)) {
    renderQueueView();
    savePlayerState();
  }
}

function bindQueueDrag() {
  const list = $("#queue-list");
  list.addEventListener("pointerdown", (event) => {
    const grip = event.target.closest(".q-grip");
    if (!grip || queueDrag) return;
    const wrap = grip.closest(".swipe-wrap");
    const wraps = [...list.querySelectorAll(".swipe-wrap")];
    const index = wraps.indexOf(wrap);
    const row = wrap ? wrap.querySelector("button") : null;
    if (!wrap || !row || index < 0 || wrap.classList.contains("revealed")) return;
    event.preventDefault();                       // 拖把按下就是拖, 不当点击
    grip.setPointerCapture(event.pointerId);      // 移出把手事件也不丢
    queueDrag = { wrap, wraps, fromView: index, target: index,
                  rowH: wrap.offsetHeight || 1, startY: event.clientY,
                  moved: false };
    wrap.classList.add("dragging");
  });
  list.addEventListener("pointermove", (event) => {
    if (!queueDrag) return;
    const drag = queueDrag;
    const dy = event.clientY - drag.startY;
    if (!drag.moved) {
      if (Math.abs(dy) < 6) return;
      drag.moved = true;
    }
    drag.wrap.style.transform = `translateY(${dy}px)`;   // 被拖行跟手
    drag.target = Math.max(0, Math.min(drag.wraps.length - 1,
        drag.fromView + Math.round(dy / drag.rowH)));
    drag.wraps.forEach((wrap, index) => {         // 其余行让位
      if (wrap === drag.wrap) return;
      let shift = 0;
      if (drag.target > drag.fromView) {
        if (index > drag.fromView && index <= drag.target) shift = -drag.rowH;
      } else if (drag.target < drag.fromView) {
        if (index >= drag.target && index < drag.fromView) shift = drag.rowH;
      }
      wrap.style.transform = shift ? `translateY(${shift}px)` : "";
    });
  });
  list.addEventListener("pointerup", () => finishQueueDrag(false));
  list.addEventListener("pointercancel", () => finishQueueDrag(true));
}

// 左滑删行 (1.8.27, 用户点名「所有列表的删除按钮都这样」): 与播放列表/
// 下载列表同款 bindSwipeDelete。删的是 wrap 记的 order 绝对位; 当前曲
// 删不得 (queueRemove 拒), 重铺 + 提示一句。
function bindQueueSwipeDelete() {
  bindSwipeDelete($("#queue-list"), async (wrap) => {
    if (!playQueue) return;
    if (queueRemove(playQueue, Number(wrap.dataset.queuePos))) {
      savePlayerState();
    } else {
      toast("正在播这首, 删不得");
    }
    renderQueueView();
  });
}

