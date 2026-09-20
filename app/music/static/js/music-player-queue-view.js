// music-player-queue-view — My Music 队列视图 (占封面区): 翻开/整行拖拽换序/左滑删除。
// 拆自 music-player.js (结构化重构, 按 music.html 里的顺序加载, 跨模块引用走全局)。
"use strict";
/* global $, ICON_BARS, bindSwipeDelete, escapeHTML, lyricsViewOpen,
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

// 左滑删除只绑一次; 1.8.29 起视图第一次打开才绑 (bindSwipeDelete 住浏览模块, 开局跑必炸)
let queueSwipeBound = false;

function toggleQueueView() {
  if (queueViewOpen) { closeQueueView(); return; }
  if (lyricsViewOpen) toggleLyricsView();   // 同住封面区, 二选一
  // 1.8.29 修 (真机播放不了): bindSwipeDelete 住浏览模块 (加载在播放器组
  // 后面), 开局跑必 ReferenceError 掐死同函数后面的整组接线 —— 第一次开视图才绑。
  if (!queueSwipeBound) {
    queueSwipeBound = true;
    bindQueueSwipeDelete();
  }
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
  // 当前曲 eq 动条, 其余接续编号 (当前算 1); 1.8.31 整行按住一会儿拖换序
  // (把手退役)。1.8.27 行套 .swipe-wrap (左滑删除); data-queue-pos 记
  // order 绝对位 (视图下标 0 = order[position]), 删行/换序都按它换算
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
      </button>
      <button class="swipe-del" aria-label="从队列移除">删除</button>
    </div>`;
  }).join("") || '<div class="lyrics-empty">队列是空的</div>';
}

// 拖拽换位 (1.8.31 整行拖, 用户点名「不需要显示三个横杠, 直接拖整个条」):
// 按住 ~200ms 进预备 (armed 微亮提示), 再动就是拖 —— 被拖行跟手, 其余行
// 让位平移, 松手按落点改 order。预备期滑走 (>10px) 交还原生 (竖扫滚列表);
// 预备后第一个 8px 定向, 横向撤 (左滑删除的地盘); armed 起 touchmove 全掐
// (非被动, 原生滚动接管 = pointercancel 断半路)。1.8.27 拖拽单位上移到
// wrap (wrap overflow:hidden 裁行内竖移); 落点位只认拖动距离, 不认
// offsetTop 绝对坐标 (相对布局一动让位乱跳, 1.8.18 的教训)。
const QUEUE_ARM_MS = 200;              // 按住这么久 = 起拖预备 (比长按菜单短)
let queueDragSwallowClick = false;     // 按住过的那一下, 抬手尾随 click 吞掉

function finishQueueDrag(cancelled) {
  const drag = queueDrag;
  queueDrag = null;
  if (!drag) return;
  drag.wrap.classList.remove("dragging", "drag-armed");
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
  let armTimer = 0;               // 预备计时器 (0 = 没在等)
  let arm = null;                 // 预备期那一按 {id, row, wrap, x, y, armed}

  const cancelArm = () => {       // 预备撤销: 计时器/预备亮全清
    clearTimeout(armTimer);
    armTimer = 0;
    if (arm) { arm.wrap.classList.remove("drag-armed"); arm = null; }
    if (queueDrag && !queueDrag.moved) queueDrag = null;   // 预备态一起撤
  };

  // 预备/拖拽中掐掉触摸的默认滚动 (非被动): 原生一旦接管就是 pointercancel,
  // 拖拽断在半路。没按住够 200ms 的场合不掺和 (竖滑滚列表照旧原生)
  list.addEventListener("touchmove", (event) => {
    if ((arm && arm.armed) || (queueDrag && queueDrag.moved)) {
      event.preventDefault();
    }
  }, { passive: false });

  list.addEventListener("pointerdown", (event) => {
    if (queueDrag || armTimer) return;
    const row = event.target.closest(".queue-row");
    if (!row || event.target.closest(".swipe-del")) return;
    const wrap = row.closest(".swipe-wrap");
    if (!wrap || wrap.classList.contains("revealed")) return;
    arm = { id: event.pointerId, row, wrap,
            x: event.clientX, y: event.clientY, armed: false };
    armTimer = setTimeout(() => {   // 按住一小会儿 = 起拖预备 (整行可拖)
      armTimer = 0;
      const wraps = [...list.querySelectorAll(".swipe-wrap")];
      const index = wraps.indexOf(wrap);
      if (!arm || index < 0 || !playQueue) { cancelArm(); return; }
      arm.armed = true;
      queueDragSwallowClick = true;       // 按住过的抬手不算行点击 (不跳播)
      wrap.classList.add("drag-armed");
      try { row.setPointerCapture(event.pointerId); } catch (_error) { }
      queueDrag = { wrap, wraps, fromView: index, target: index,
                    rowH: wrap.offsetHeight || 1,
                    startX: arm.x, startY: arm.y, moved: false };
    }, QUEUE_ARM_MS);
  });
  list.addEventListener("pointermove", (event) => {
    if (arm && !arm.armed           // 预备期就滑走: 交还滚动/左滑删除
        && (event.pointerId !== arm.id || Math.hypot(event.clientX - arm.x,
              event.clientY - arm.y) > 10)) cancelArm();
    if (!queueDrag) return;
    const drag = queueDrag;
    if (!drag.moved) {
      const dx = event.clientX - drag.startX;
      const dy = event.clientY - drag.startY;
      if (Math.abs(dx) < 8 && Math.abs(dy) < 8) return;
      if (Math.abs(dx) > Math.abs(dy)) {   // 横向: 左滑删除的地盘, 撤
        cancelArm();
        return;
      }
      drag.moved = true;
      drag.wrap.classList.add("dragging");
      drag.startY = event.clientY;         // 从坐实那一下跟手
    }
    const dy = event.clientY - drag.startY;
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
  const dropDrag = (cancelled) => {  // 松手/被系统掐: 拖完落定, 没拖撤预备
    if (queueDrag && queueDrag.moved) { finishQueueDrag(cancelled); arm = null; }
    else cancelArm();
  };
  list.addEventListener("pointerup", () => dropDrag(false));
  list.addEventListener("pointercancel", () => dropDrag(true));
  // 按住过/拖完的尾随 click 吞掉 (行点击 = 跳播, 拖完跳一下不是本意)
  list.addEventListener("click", (event) => {
    if (!queueDragSwallowClick) return;
    queueDragSwallowClick = false;
    event.stopPropagation();
  }, true);
}

// 左滑删行 (1.8.27, 用户点名「所有列表的删除按钮都这样」): 与播放列表/
// 下载列表同款 bindSwipeDelete。删的是 wrap 记的 order 绝对位; 当前曲
// 删不得 (queueRemove 拒), 重铺 + 提示一句。bindSwipeDelete 在浏览模块
// (加载在播放器组之后), 所以只在队列视图第一次打开时调用 (见上)。
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

