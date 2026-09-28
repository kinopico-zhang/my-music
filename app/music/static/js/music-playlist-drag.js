// music-playlist-drag — My Music 播放列表详情页曲目拖拽换序 (1.8.17 用户点名
// 「允许调整列表歌曲的顺序」; 1.8.31 改整行拖, 用户点名「不需要显示三个
// 横杠, 默认都是直接拖动调整顺序, 长按是右键菜单」): 行上按住 ~200ms 进
// 预备 (比长按菜单的 500ms 短), 再动就是拖 —— 被拖行跟手 (wrap transform),
// 其余行让位平移, 松手按落点落定。预备期就滑走 (>10px) 交还原生: 竖向
// 轻扫照旧滚列表, 横向让给左滑删除; 预备后第一个 8px 定向, 横向的也撤。
// 长按菜单开了 (500ms) 同撤 —— 菜单压在行上, 拖不动了。
// 1.8.108 键鼠端鼠标即按即拖 (用户点名「播放列表要支持鼠标拖拽调整顺
// 序」): 桌面惯例没有「按住等预备」, 按下就是起拖意图 —— 动够 8px 竖向
// 就拖; 触摸端照旧按住 ~200ms (得跟滚动/左滑分家)。鼠标路径不亮预备态
// (点一下就闪一下太吵), 也没动过就不吞 click —— 按下抬手照旧开播。
// 行住 .swipe-wrap 里 (与左滑删除同构): 1.8.19 起被拖的/被抬层的都是
// wrap —— wrap overflow:hidden (左滑删除的裁切), 行在 wrap 里竖移出界会被
// 裁得只剩一截黑边 (行自己的 z-index 翻不出裁切)。
"use strict";
/* global $, isKeyMouseInput */
/* exported bindPlaylistDrag */

let playlistDrag = null;
let playlistDragSwallowClick = false;   // 按住过的那一下, 尾随 click 吞掉 (不开播)
const PLAYLIST_ARM_MS = 200;            // 按住这么久 = 起拖预备 (< 菜单的 500ms)

/** 绑到曲目容器 (#playlist-tracks) 上; reorder(from, to) 由调用方持久化
    (PUT 全量新顺序) 并同步自己的曲目数组。 */
function bindPlaylistDrag(container, reorder) {
  let armTimer = 0;               // 预备计时器 (0 = 没在等)
  let arm = null;                 // 预备期那一按 {id, row, wrap, x, y, armed}

  const cancelArm = () => {       // 预备撤销: 计时器/预备亮全清
    clearTimeout(armTimer);
    armTimer = 0;
    if (arm) {
      arm.wrap.classList.remove("drag-armed");
      arm = null;
    }
    if (playlistDrag && !playlistDrag.moved) playlistDrag = null;   // 预备态一起撤
  };

  // 预备落定 (触摸端等满 200ms / 键鼠端鼠标按下即): 抬层挂在 wrap, 让位
  // 集合记下来。held = 是等出来的预备 —— 亮行板提示「可以拖了」+ 抬手不
  // 算点击; 鼠标即按即拖没有等待期, 不亮不吞 (点了没动 = 开播)
  const armDrag = (pointerId, held) => {
    if (!arm) { cancelArm(); return; }
    const wraps = [...container.querySelectorAll(".swipe-wrap")];
    const index = wraps.indexOf(arm.wrap);
    if (index < 0) { cancelArm(); return; }
    arm.armed = true;
    if (held) {
      playlistDragSwallowClick = true;    // 按住过的抬手不算点击 (不开播)
      arm.wrap.classList.add("drag-armed");
    }
    try { arm.row.setPointerCapture(pointerId); } catch (_error) { }
    playlistDrag = { wrap: arm.wrap, wraps, from: index, target: index,
                     rowH: arm.wrap.offsetHeight || 1,
                     startX: arm.x, startY: arm.y, moved: false };
  };

  // 预备/拖拽中掐掉触摸的默认滚动 (非被动): 原生一旦接管就是 pointercancel,
  // 拖拽断在半路。没按住够 200ms 的场合不掺和 (竖滑滚列表照旧原生)
  container.addEventListener("touchmove", (event) => {
    if ((arm && arm.armed) || (playlistDrag && playlistDrag.moved)) {
      event.preventDefault();
    }
  }, { passive: false });

  // 鼠标拖拽的坑 (1.8.108): 行首小封面是 <img>, 按在封面上起拖会被原生
  // 图片拖拽抢走指针流 (拖拽断在半路)。预备/拖拽进行中掐掉 dragstart;
  // 没在拖的场合不掺和。触摸指针不派发 dragstart, 此路只有鼠标会走
  container.addEventListener("dragstart", (event) => {
    if (arm && arm.armed) event.preventDefault();
  });

  container.addEventListener("pointerdown", (event) => {
    if (playlistDrag || armTimer) return;
    // 鼠标只认主键 —— 右键 (菜单)/中键 (自动滚动) 不是拖拽意图
    if (event.pointerType === "mouse" && event.button !== 0) return;
    const row = event.target.closest(".track-row");
    if (!row || event.target.closest(".swipe-del")) return;
    const wrap = row.closest(".swipe-wrap");
    if (!wrap || wrap.classList.contains("revealed")) return;
    arm = { id: event.pointerId, row, wrap,
            x: event.clientX, y: event.clientY, armed: false };
    if (event.pointerType === "mouse" && isKeyMouseInput()) {
      armDrag(event.pointerId, false);   // 键鼠端鼠标即按即拖, 不等预备
    } else {
      armTimer = setTimeout(() => {      // 触摸: 按住一小会儿 = 起拖预备
        armTimer = 0;
        armDrag(event.pointerId, true);
      }, PLAYLIST_ARM_MS);
    }
  });
  container.addEventListener("pointermove", (event) => {
    // 长按菜单开了 (按住到 500ms): 让位 —— 菜单压在行上, 拖不动了
    if (arm && !$("#track-menu").hidden) { cancelArm(); return; }
    if (arm && !arm.armed) {       // 预备期就滑走: 交还滚动/左滑删除
      if (event.pointerId !== arm.id
          || Math.hypot(event.clientX - arm.x,
                        event.clientY - arm.y) > 10) cancelArm();
    }
    if (!playlistDrag) return;
    const drag = playlistDrag;
    if (!drag.moved) {
      const dx = event.clientX - drag.startX;
      const dy = event.clientY - drag.startY;
      if (Math.abs(dx) < 8 && Math.abs(dy) < 8) return;
      playlistDragSwallowClick = true;    // 动够 8px 就是拖拽意图, 抬手不开播
      if (Math.abs(dx) > Math.abs(dy)) {   // 横向: 左滑删除的地盘, 撤
        cancelArm();
        return;
      }
      drag.moved = true;
      drag.wrap.classList.add("dragging");   // 位移/抬层都落在 wrap (行翻不出裁切)
      drag.startY = event.clientY;           // 从坐实那一下跟手
    }
    const dy = event.clientY - drag.startY;
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
    arm = null;
    if (!drag) return;
    const commit = !cancelled && drag.moved && drag.target !== drag.from;
    // 让位行清位移分两条路 (1.8.20 修「送手时让过位的行又抖一下」): 落定的
    // 话换序的 DOM 挪动同帧发生, 让位行的自然位已经变了, 带着过渡清位移
    // 会先跳一格再滑回来 —— 必须无过渡清 + 落帧钉死; 取消/没挪没有 DOM
    // 挪动, 让过渡跑, 行顺滑滑回原位
    if (commit) {
      drag.wraps.forEach((wrap) => {
        if (wrap !== drag.wrap) wrap.style.transition = "none";
      });
    }
    // 清位移时 .dragging 还挂着 (transition none) —— 与队列同款, 落定不弹跳
    drag.wrap.style.transform = "";
    drag.wrap.classList.remove("dragging", "drag-armed");
    drag.wraps.forEach((wrap) => { wrap.style.transform = ""; });
    if (!commit) return;
    void container.offsetHeight;   // 落帧: 让位行的无过渡清位移落账, 过渡别补放
    drag.wraps.forEach((wrap) => { wrap.style.transition = ""; });
    playlistDragSwallowClick = true;
    // 先把 wrap 挪到落点位 (滚动位置纹丝不动), 再交给调用方持久化
    const reference = drag.target === drag.wraps.length - 1 ? null
      : drag.wraps[drag.target + (drag.target > drag.from ? 1 : 0)];
    container.insertBefore(drag.wrap, reference);
    await reorder(drag.from, drag.target);
  };
  container.addEventListener("pointerup", () => {
    if (playlistDrag && playlistDrag.moved) finish(false);
    else cancelArm();
  });
  container.addEventListener("pointercancel", () => {
    if (playlistDrag && playlistDrag.moved) finish(true);
    else cancelArm();
  });
  container.addEventListener("click", (event) => {
    if (playlistDragSwallowClick) {
      playlistDragSwallowClick = false;
      event.stopPropagation();               // 按住过/拖完的尾随 click 别开播
    }
  }, true);
}
