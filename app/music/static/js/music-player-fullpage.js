// music-player-fullpage — My Music 全屏播放页开合: 滑入滑出, 下拉/横划收起。
// 拆自 music-player.js (结构化重构, 代码逐字节未动, 按 music.html 里的顺序加载, 跨模块引用走全局)。
// 1.8.60 封面的左右划切歌拆去 music-player-art-stage (3D 封面舞台接手)。
// 1.8.63 开场换成流体胶囊形变 (music-player-fluid-morph): 点气泡从胶囊轮廓
// 原位延展成整页 (水滴铺开), 程序化收起收拢回胶囊; 拖拽收起 (下拉/右甩)
// 照旧滑出 —— 手上有惯性, 滑出才是连续的动作语言。
"use strict";
/* global $, FLUID_CLOSE_MS, closeQueueView, fluidCollapse, fluidExpand,
          fluidReset, lyricsViewOpen, queueViewOpen, toggleLyricsView */
/* exported bindDismissDrag, closeFullPlayer, fpDismissDragged, openFullPlayer, playerOpen */

let fpHideTimer = 0;

let playerOpen = false;   // 全屏页开着吗 (防重入; 开关是纯视图状态, 不碰历史)

function openFullPlayer() {
  const fullPlayer = $("#full-player");
  clearTimeout(fpHideTimer);
  // 1.8.53 兜底: 关页途中惯性滚动补发的 scroll 可能把「回到当前句」又
  // 亮出来, 开页先按下去 (封面页上不该见着它)
  $("#lyrics-resume").hidden = true;
  fullPlayer.hidden = false;
  fullPlayer.style.pointerEvents = "";
  // 1.8.63 流体胶囊形变: 从气泡的胶囊轮廓原位延展成整页, 尺寸/圆角走
  // 高阻尼流体曲线 —— 没在播 (没有气泡可依) 才退回滑入
  if (fluidExpand(fullPlayer)) {
    fullPlayer.classList.add("open");   // 先上: 落位后样式表无缝接手
    playerOpen = true;
    return;
  }
  fluidReset(fullPlayer);    // 清形变残留, 滑入世界量准起点
  void fullPlayer.offsetWidth;   // 强制起点样式先落地再放滑入 (rAF 在安静页会饿死)
  fullPlayer.classList.add("open");
  playerOpen = true;
}

// direction "morph" = 流体收拢回气泡 (水滴收回); "right" = 向右甩出收起
// (抓手条横拖); 默认向下收 (拖拽松手的收起 —— 带着惯性走滑出)。
function closeFullPlayer(direction) {
  if (!playerOpen) return;
  playerOpen = false;
  const fullPlayer = $("#full-player");
  if (lyricsViewOpen) toggleLyricsView();
  if (queueViewOpen) closeQueueView();
  fullPlayer.style.pointerEvents = "none";   // 出场途中别挡下层
  clearTimeout(fpHideTimer);
  // 1.8.63 流体收场: 收拢回气泡的胶囊轮廓, 落位清场交还气泡
  if (direction === "morph" && fluidCollapse(fullPlayer)) {
    fpHideTimer = setTimeout(() => {
      fullPlayer.hidden = true;
      fullPlayer.style.pointerEvents = "";
      fullPlayer.classList.remove("open");
      fluidReset(fullPlayer);   // 清行内几何, 交还气泡
    }, FLUID_CLOSE_MS);
    return;
  }
  fluidReset(fullPlayer);   // 形变残留清掉 (滑出世界不认行内几何)
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
// 1.8.2 整页化 (用户点名「任何一点都能拖」): .fp-sheet/.fp-bg 也绑一份
// (ignoreInteractive), 起手点落在自带手势的东西上就让路 —— 歌词/队列自带
// 滚动, 抓手/封面自带拖动, 按钮/滑杆各有点击与拖拽语义。
// 1.8.60 封面上的左右划归 3D 封面舞台 (music-player-art-stage), 这里只管
// 竖向收起 —— 横向在这直接放掉。
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
    // 歌词/待播放是整页盖屏的滚动器 (1.8.5 修「切到待播放后全局下拉
    // 退出小了」): 自己滚在半路时让路, 滚到顶 (或头部区) 时下拉归收起 ——
    // 待播放的滚动器是里面的 #queue-list, 歌词就是 #fp-lyrics 本身
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
      fluidReset(player);    // 形变半路抓起: 先回干净世界再跟手拖
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

/** 歌词结果/外部入口: 打开歌词视图 (已开着就不动; 没歌词的曲子点不开)。 */
