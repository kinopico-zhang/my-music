// music-player-art-stage — My Music 播放页 3D 封面舞台 (1.8.60, 用户点名):
// 上一首/下一首斜插两侧 (CoverFlow 同款), 左右拖跟手转面, 松手 3D 落定切歌。
// 姿态 = 各卡槽位 (自身位 -1/0/1 + 拖拽进度) 的横移/纵深/转角/压暗, JS 直落
// 行内, 松手走原生过渡 (1.8.61)。1.8.66 过场中段扇形张开 (过卡那拍两侧
// 分最开不叠不穿), 来卡过半浮上旧卡沉底 (翻层藏进最大缝); 交班只留程序切歌。
"use strict";
/* global $, PLACEHOLDER_ARTWORK, currentTrack, onTrackChange, playQueue,
          playerNext, playerPrevious */
/* exported initArtStage */

const STAGE_SPACING = 0.55;   // 侧卡横移 (自身卡宽的占比)
const STAGE_ANGLE = 40;       // 侧卡转角 (度)
const STAGE_DEPTH = 150;      // 侧卡后退 (px, 槽位的平方 —— 越偏越退)
const STAGE_DIM = 0.42;       // 侧卡压暗 (槽位的平方 —— 越偏越暗)
const STAGE_FAN = 1;          // 过场扇形张开量 (过卡那拍横移 ×(1+此值))

let swayFrom = null;       // 松手余位: 换曲后从余位滑回中间, 不许跳位 (null = 程序切歌按走向猜)
let stagePrimed = false;   // 首次上屏不跳位 (冷启动恢复时播放页都没开)
let stageLastTrackId = 0;  // 同曲重载 (队首回本曲开头) 不做进场动画
let stageLastPos = -1;     // 上一拍的队列位, 用来猜程序切歌的来向
let handoffCard = null;    // 交班中的旧曲卡 (换曲那拍压顶溶出让位)
let handoffTimer = 0;      // 交班淡出完成后的复位计时 (落回侧卡层再淡回)
let stageHandoff = null;   // 交班侧: 旧曲卡退到哪一侧 ("prev"/"next")

/** 队列两侧邻居 (只读, 不动队列): 队首没上一首 (goBack 是回本曲开头); 队尾只有全队循环才绕回队首。 */
function stageNeighbors() {
  if (!playQueue || playQueue.position < 0) return { prev: null, next: null };
  const order = playQueue.order;
  const at = (pos) => playQueue.tracks[order[pos]] || null;
  return {
    prev: playQueue.position > 0 ? at(playQueue.position - 1) : null,
    next: playQueue.position < order.length - 1 ? at(playQueue.position + 1)
      : (playQueue.repeat === "all" && order.length > 1 ? at(0) : null),
  };
}

function stageCardSrc(img, track) {
  img.src = track && track.album_id
    ? `/music/media/albums/${track.album_id}/artwork` : PLACEHOLDER_ARTWORK;
}

/** 扇形倍率: 过卡那拍 (|slot|=0.5) 峰值 1+STAGE_FAN, 静止/越台 (|slot|≥1) 收回 1。 */
function fanOf(slot) {
  const t = Math.min(1, Math.abs(slot));
  return 1 + STAGE_FAN * 4 * t * (1 - t);
}

/** 一张卡摆到槽位: 横移按自身卡宽 (%) ×扇形倍率, 深度/压暗按槽位平方; 透明度恒写 1 (交班旧卡被接走时自愈)。 */
function poseCard(card, slot) {
  card.style.transform =
    `translateX(${slot * STAGE_SPACING * fanOf(slot) * 100}%)`
    + ` translateZ(${slot * slot * -STAGE_DEPTH}px)`
    + ` rotateY(${slot * STAGE_ANGLE}deg)`;
  card.style.filter = `brightness(${1 - slot * slot * STAGE_DIM})`;
  card.style.opacity = "1";
}

function poseStage(sway, live) {
  const wrap = $("#fp-art-wrap");
  wrap.classList.toggle("rise-next", !!live && sway <= -0.5);   // 拖动中来卡过半浮上 (z4)
  wrap.classList.toggle("rise-prev", !!live && sway >= 0.5);   // 翻层藏在扇形缝最大处
  poseCard($("#fp-art"), sway);
  poseCard($("#fp-art-prev"), sway - 1);
  poseCard($("#fp-art-next"), sway + 1);
}

/** 落定动画半路被抓起手: 读当前卡实时横移换算回 sway —— 扇形展开后横移≠sway, 定点迭代反解。 */
function stageAnimatedSway() {
  const center = $("#fp-art");
  const matrix = getComputedStyle(center).transform;
  if (!matrix || matrix === "none") return 0;
  try {
    const px = new DOMMatrixReadOnly(matrix).m41 / (center.offsetWidth * STAGE_SPACING);
    let s = px / 2;   // 真解在 [px/2, px] (倍率 1..(1+STAGE_FAN)), 三轮定点收敛
    for (let i = 0; i < 3; i++) s = px / fanOf(s);
    return Math.max(-1, Math.min(1, s)) || 0;
  } catch (_error) { return 0; }       // 矩阵读不出来就当中间位起手
}

/** 撤交班: 旧曲卡落回侧卡层 (z1) 淡回显形; 淡出没走完就被下一场接走也在这里平回。 */
function clearHandoff() {
  clearTimeout(handoffTimer);
  if (!handoffCard) return;
  handoffCard.classList.remove("handoff");
  handoffCard.style.opacity = "1"; handoffCard = null;
}

/** 换曲后重铺三张卡。start = 拖拽余位 | ±1 (程序切歌) | null 不动画; 程序切歌旧曲卡压顶交班。 */
function renderArtStage(start) {
  clearHandoff();
  const neighbors = stageNeighbors();
  stageCardSrc($("#fp-art-prev"), neighbors.prev);
  stageCardSrc($("#fp-art-next"), neighbors.next);
  $("#fp-art-prev").classList.toggle("off", !neighbors.prev);
  $("#fp-art-next").classList.toggle("off", !neighbors.next);
  const trackId = currentTrack ? currentTrack.track_id : 0;
  let from = null;
  if (stagePrimed && currentTrack && trackId !== stageLastTrackId) {
    if (start !== null) from = start;
    else if (playQueue) {
      const len = playQueue.order.length || 1;
      const step = (playQueue.position - stageLastPos + len) % len;
      from = step === len - 1 ? -1 : 1;   // 恰是上一首: 从左进, 其余从右
      stageHandoff = from > 0 ? "prev" : "next";   // 旧曲卡退去的那一侧
    }
  }
  stagePrimed = true; stageLastTrackId = trackId;
  stageLastPos = playQueue ? playQueue.position : -1;
  const wrap = $("#fp-art-wrap");
  wrap.classList.add("dragging");
  poseStage(from !== null ? from : 0);   // 起跳位 / 静止位 (掐过渡摆; 顺带撤 rise)
  void wrap.offsetWidth;                 // 起跳位先落地 (rAF 在安静页会饿死)
  wrap.classList.remove("dragging");
  if (from !== null) {                   // 有起跳位: 放过渡滑回中间
    poseStage(0);
    if (stageHandoff) {                  // 交班: 旧卡压顶 (z5) 溶出, 新卡透上
      handoffCard = $(stageHandoff === "prev" ? "#fp-art-prev" : "#fp-art-next");
      handoffCard.classList.add("handoff");
      handoffCard.style.opacity = "0";
      handoffTimer = setTimeout(clearHandoff, 420);
    }
  }
  stageHandoff = null;
}

function stageTrackChanged() {
  const start = swayFrom; swayFrom = null;
  renderArtStage(start);
}

/** 左右拖跟手 + 松手落定 (竖向让给下拉收起): 拖过四分之一或带甩劲切歌; 半路抓住落定中的封面也接得住。 */
function bindArtStageDrag(wrap) {
  let dragging = false, pointerId = -1;
  let startX = 0, startY = 0, lastX = 0, lastTime = 0;
  let hVelocity = 0;    // px/ms, 松手那刻的横向甩速
  let mode = "";        // "" 未定 / "sway" 3D 拖面
  let swayBase = 0;     // 起手那拍的 sway (落定动画半路抓取用)
  wrap.addEventListener("pointerdown", (event) => {
    if (event.pointerType === "mouse" && event.button !== 0) return;
    dragging = true;
    pointerId = event.pointerId;
    startX = lastX = event.clientX; startY = event.clientY; lastTime = performance.now();
    hVelocity = 0; mode = "";
  });
  wrap.addEventListener("pointermove", (event) => {
    if (!dragging || event.pointerId !== pointerId) return;
    const now = performance.now();
    if (now > lastTime) {
      hVelocity = (event.clientX - lastX) / (now - lastTime);
      lastTime = now;
    }
    lastX = event.clientX;
    const dx = lastX - startX;
    if (!mode) {
      if (Math.abs(dx) < 10 && Math.abs(event.clientY - startY) < 10) return;
      if (Math.abs(event.clientY - startY) >= Math.abs(dx)) {
        dragging = false;        // 竖向: 归下拉收起
        return;
      }
      mode = "sway";
      swayBase = stageAnimatedSway();
      clearHandoff();            // 交班半路接手: 旧卡复位 (z 落回再拖)
      wrap.classList.add("dragging");   // 拖动跟手, 掐掉落定过渡
      wrap.setPointerCapture(event.pointerId);
    }
    const width = wrap.offsetWidth || 1;
    const sway = Math.max(-1, Math.min(1, swayBase + dx / width));
    poseStage(sway, true);   // live: 过半翻层 (rise) 只在拖动中, 缝最大处看不见
  });
  const finish = (event) => {
    if (!dragging || (event.pointerId !== undefined && event.pointerId !== pointerId)) return;
    dragging = false;
    if (mode !== "sway") return;
    wrap.classList.remove("dragging");  // 过渡回来, 松手交给动画
    const width = wrap.offsetWidth || 1;
    const d = Math.max(-1, Math.min(1, swayBase + (lastX - startX) / width));
    const flick = Math.abs(hVelocity) > 0.5 && Math.abs(lastX - startX) > 30;
    if (d <= -0.28 || (flick && hVelocity < 0)) commitStage(d, "next");
    else if (d >= 0.28 || (flick && hVelocity > 0)) commitStage(d, "prev");
    else poseStage(0);                  // 没拖够: 弹回 (rise 顺带撤了)
  };
  for (const ev of ["pointerup", "pointercancel"]) wrap.addEventListener(ev, finish);
}

/** 松手落定切歌: 余位 (1+d / d-1) 递给换曲回调接力; 没换成 (队尾顶住/回本曲开头) 就地弹回。 */
function commitStage(d, direction) {
  const before = currentTrack;
  swayFrom = direction === "next" ? 1 + d : d - 1;
  if (direction === "next") playerNext();
  else playerPrevious();
  // 拖动松手不交班 (1.8.67): 扇形缝里层序天然接对, 溶解反而在缝里闪没再闪回
  if (currentTrack !== before) return;  // 换曲成功: 动画已由回调接力
  swayFrom = null;
  poseStage(0);
}

function initArtStage() {
  onTrackChange(stageTrackChanged);
  bindArtStageDrag($("#fp-art-wrap"));
}
