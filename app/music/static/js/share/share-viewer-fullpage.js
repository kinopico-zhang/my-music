// share-viewer-fullpage — My Music 分享页全屏播放页: 开合/下拉收起。
// 1.8.130 (用户点名「样式和普通播放页面一样」) 容器换 #full-player,
// 收起手势整用应用 music-player-fullpage 的 bindDismissDrag 同款
// (抓手条另有横拖右甩收起; 封面/歌词/队列/按钮/滑杆各让各的路) ——
// 应用的流体胶囊形变不带 (那套连着应用首页气泡, 分享页没有), 开合走滑入
// 滑出。封面的左右划归 3D 封面舞台 (music-player-art-stage), 旧的 40px
// 平面滑切退役。
"use strict";
/* global $, closeQueueView, lyricsViewOpen, playerNext, playerPrevious,
          queueViewOpen, toggleLyricsView, togglePlay */
/* exported closeFullPlayer, fpDismissDragged, openFullPlayer */

let fpHideTimer = 0;
let playerOpen = false;   // 全屏页开着吗 (防重入; 开关是纯视图状态, 不碰历史)

function openFullPlayer() {
  const fullPlayer = $("#full-player");
  clearTimeout(fpHideTimer);
  // 应用同款兜底: 关页途中惯性滚动补发的 scroll 可能把「回到当前句」又
  // 亮出来, 开页先按下去 (封面页上不该见着它)
  $("#lyrics-resume").hidden = true;
  fullPlayer.hidden = false;
  void fullPlayer.offsetWidth;   // 强制起点样式先落地再放滑入 (rAF 在安静页会饿死)
  fullPlayer.classList.add("open");
  playerOpen = true;
}

// direction "right" = 向右甩出收起 (抓手条横拖); 默认向下收 (拖拽松手)。
function closeFullPlayer(direction) {
  if (!playerOpen) return;
  playerOpen = false;
  const fullPlayer = $("#full-player");
  if (lyricsViewOpen) toggleLyricsView();
  if (queueViewOpen) closeQueueView();
  fullPlayer.style.pointerEvents = "none";   // 出场途中别挡下层
  clearTimeout(fpHideTimer);
  fullPlayer.classList.remove("open");
  if (direction === "right") fullPlayer.classList.add("dismiss-right");
  fpHideTimer = setTimeout(() => {
    fullPlayer.hidden = true;
    fullPlayer.style.pointerEvents = "";
    fullPlayer.classList.remove("dismiss-right");
  }, 300);
}

// ------------------------------------------------------------ 下拉/横划收起
// 抓手条/封面/整页空白往下拖: 播放页跟手下滑, 松手拖得够远或够快就收起,
// 否则弹回。抓手条另有横拖收起: 往右拖整页跟手走, 松手拖过三分之一
// (或带甩劲) 就向右甩出收起。拖动后的尾随 click 不算 (不然小拖一下也收起)。
// 整页化 (应用 1.8.2 同款): .fp-sheet/.fp-bg 也绑一份 (ignoreInteractive),
// 起手点落在自带手势的东西上就让路 —— 歌词/队列自带滚动, 抓手/封面自带
// 拖动, 按钮/滑杆各有点击与拖拽语义。封面上的左右划归 3D 封面舞台,
// 这里只管竖向收起 —— 横向在这直接放掉。
let fpDismissDragged = false;

// horizontalClose: 抓手条上的横划改成拖整页收起 (true), 而不是放掉。
// ignoreInteractive: 起手点命中按钮/输入/滑杆/歌词/队列 (或已绑拖动的
// 抓手/封面) 时整个手势放掉, 让位给它们自己的行为。
function bindDismissDrag(target, horizontalClose = false, ignoreInteractive = false) {
  const player = $("#full-player");
  let dragging = false;
  let pointerId = -1;
  let startX = 0;
  let startY = 0;
  let lastX = 0;
  let lastY = 0;
  let lastTime = 0;
  let velocity = 0;                  // px/ms, 松手那刻的甩速 (竖向)
  let hVelocity = 0;                 // 横向甩速
  let mode = "";                     // "" 未定 / "down" 收起 / "across" 抓手横拖收起
  target.addEventListener("pointerdown", (event) => {
    if (event.pointerType === "mouse" && event.button !== 0) return;
    if (ignoreInteractive && event.target.closest(
          "#fp-grab, #fp-art-wrap, .fp-scrub,"
          + " button, input")) return;
    // 歌词/待播放是整页盖屏的滚动器: 自己滚在半路时让路, 滚到顶 (或
    // 头部区) 时下拉归收起 —— 待播放的滚动器是里面的 #queue-list,
    // 歌词就是 #fp-lyrics 本身
    if (ignoreInteractive) {
      const scroller = event.target.closest("#fp-lyrics, #queue-list");
      if (scroller && scroller.scrollTop > 0) return;
    }
    dragging = true;
    pointerId = event.pointerId;
    startX = lastX = event.clientX;
    startY = lastY = event.clientY;
    lastTime = performance.now();
    velocity = 0;
    hVelocity = 0;
    mode = "";
    fpDismissDragged = false;
  });
  target.addEventListener("pointermove", (event) => {
    if (!dragging || event.pointerId !== pointerId) return;
    const now = performance.now();
    if (now > lastTime) {
      velocity = (event.clientY - lastY) / (now - lastTime);
      hVelocity = (event.clientX - lastX) / (now - lastTime);
      lastTime = now;
    }
    lastX = event.clientX;
    lastY = event.clientY;
    const dx = lastX - startX;
    const dy = lastY - startY;
    if (!mode) {
      if (Math.abs(dx) < 10 && Math.abs(dy) < 10) return;
      if (Math.abs(dy) >= Math.abs(dx)) mode = "down";
      else if (horizontalClose) mode = "across";
      else { dragging = false; return; }   // 横划没意义的目标, 放掉
      player.style.transition = "none";
      target.setPointerCapture(event.pointerId);
    }
    if (mode === "down") {
      if (dy > 10) fpDismissDragged = true;
      player.style.transform = dy > 0 ? `translateY(${dy * 0.92}px)` : "";
    } else {
      if (dx > 10) fpDismissDragged = true;
      player.style.transform = dx > 0 ? `translateX(${dx * 0.92}px)` : "";
    }
  });
  const finish = (event) => {
    if (!dragging || (event.pointerId !== undefined
                      && event.pointerId !== pointerId)) return;
    dragging = false;
    player.style.transition = "";
    player.style.transform = "";
    if (mode === "down") {
      if (lastY - startY > 90 || velocity > 0.55) closeFullPlayer();
      return;
    }
    if (mode !== "across") return;
    const width = player.offsetWidth || 1;
    const flick = hVelocity > 0.5 && lastX - startX > 30;
    if (lastX - startX >= width / 3 || flick) {
      closeFullPlayer("right");    // 样式交给 .dismiss-right 接管 (从当前位置甩出)
    }                              // 没拖够: 行内样式已清, 弹回原位
  };
  target.addEventListener("pointerup", finish);
  target.addEventListener("pointercancel", finish);
}

// ------------------------------------------------------------ 接线
$("#fp-grab").addEventListener("click", () => {
  if (fpDismissDragged) {            // 刚拖过: 抬手补发的 click 不算
    fpDismissDragged = false;
    return;
  }
  closeFullPlayer();
});
bindDismissDrag($("#fp-grab"), true);   // 抓手条: 下拉收起 + 横拖右甩收起
bindDismissDrag($("#fp-art-wrap"));     // 封面: 下拉收起 (左右划归 3D 舞台)
bindDismissDrag($(".fp-sheet"), false, true);
bindDismissDrag($(".fp-bg"), false, true);
$("#p-text").addEventListener("click", openFullPlayer);
$("#fp-prev").addEventListener("click", playerPrevious);
$("#fp-next").addEventListener("click", playerNext);
$("#fp-play").addEventListener("click", togglePlay);
