// music-pip-lyrics — 画中画跟唱窗的歌词机器 (1.8.141 方形跟唱版从
// music-pip.js 拆出, 代码逐字节未动; 301 行撞了 200 行帽, 顺着播放页
// 当年的拆法分家): 词走主页同一份缓存 (lyricsCache), 没缓存的曲子现拉
// 现解析 (与播放页 loadLyrics 同配方, 各画各的 DOM); 没词的曲子垫「这
// 首歌没有歌词」, 纯文本词整页清晰可滑、不跟唱。滚动动画走 pipWindow
// 自己的 requestAnimationFrame —— 主页切后台被浏览器限帧, 小窗自己
// 可见照常跑帧, 词不卡; 手动滑词暂停跟唱、静置回跟 (窗口常数与播放页
// 同一个 LYRICS_FOLLOW_RESUME_MS), 自己动画写的滚动不算手动。
"use strict";
/* global $, LYRICS_FOLLOW_RESUME_MS, activeLyricIndex, currentTrack,
          escapeHTML, fetchJSON, lyricsCache, lyricsOffsets, parseLyrics,
          pipWindow */
/* exported bindPipLyrics, cancelPipLyricsScroll, pipHighlightLyrics,
            pipLoadLyrics, pipResetLyrics */

let pipLyricsTrackId = 0;   // 窗里铺着哪首的词 (0 = 空; 高亮防串门闩)
let pipLyricIndex = -2;     // 窗里亮到第几行 (-2 = 待首句, 同播放页占位法)
let pipLyricsFollow = true; // 跟唱滚动中 (手动滑词时暂停, 静置回跟)
let pipLyricsLastScrollAt = 0;   // 最近一次手动滑词时刻
let pipSelfScrollUntil = 0;      // 自己动画写 scrollTop 的宽限尾 (scroll 事件别误判手动)
let pipScrollRaf = 0;       // pipWindow 的滚动动画帧句柄 (0 = 没在动)
let pipScrollTarget = null; // 追踪中的行 (换曲重铺后作废)
let pipScrollLastTime = 0;  // 上一帧时刻 (算 dt)

/** 窗里铺当前曲的歌词 (开窗/换曲时): 词走主页同一份缓存 (lyricsCache),
    没缓存的曲子现拉现解析 (与播放页 loadLyrics 同配方, 各画各的 DOM);
    没词的曲子垫「这首歌没有歌词」, 纯文本词整页清晰可滑、不跟唱。 */
async function pipLoadLyrics() {
  if (!pipWindow || !currentTrack) return;
  const track = currentTrack;
  if (!lyricsCache.has(track.track_id)) {
    try {
      const response = await fetchJSON(
        `/music/api/tracks/${track.track_id}/lyrics`);
      lyricsCache.set(track.track_id,
        response.lyrics ? parseLyrics(response.lyrics) : null);
      lyricsOffsets.set(track.track_id, response.lyrics_offset_ms || 0);
    } catch (_error) {
      lyricsCache.set(track.track_id, null);
    }
  }
  if (!pipWindow || !currentTrack
      || currentTrack.track_id !== track.track_id) return;  // 已切曲/已关窗
  cancelPipLyricsScroll();
  pipLyricsTrackId = track.track_id;
  pipLyricIndex = -2;
  const container = pipWindow.document.getElementById("pip-lyrics");
  const lyricsDocument = lyricsCache.get(track.track_id);
  if (!lyricsDocument || !lyricsDocument.lines.length) {
    container.innerHTML = '<div class="lyrics-empty">这首歌没有歌词</div>';
    container.classList.remove("static");
    return;
  }
  container.innerHTML = lyricsDocument.lines.map((line) =>
    `<div class="lyrics-line" data-time="${line.timeSeconds}">${escapeHTML(line.text)}</div>`
  ).join("");
  container.scrollTop = 0;        // innerHTML 换血不清 scrollTop, 先回顶
  container.classList.toggle("static", !lyricsDocument.synced);
  pipHighlightLyrics();
}

/** timeupdate 驱动: 窗里亮行跟着歌走 (对齐微调与播放页同一份 Map,
    正 = 词延后), 手动滑过只亮不滚, 静置片刻自动回跟。 */
function pipHighlightLyrics() {
  if (!pipWindow || !currentTrack
      || pipLyricsTrackId !== currentTrack.track_id) return;
  const lyricsDocument = lyricsCache.get(currentTrack.track_id);
  if (!lyricsDocument || !lyricsDocument.synced) return;
  const offsetSeconds = (lyricsOffsets.get(currentTrack.track_id) || 0) / 1000;
  const index = activeLyricIndex(
    lyricsDocument.lines, $("#audio").currentTime - offsetSeconds);
  if (index !== pipLyricIndex) {
    pipLyricIndex = index;
    const lines = pipWindow.document
      .querySelectorAll("#pip-lyrics .lyrics-line");
    lines.forEach((line, position) => {
      // 清晰度分工同播放页: 正唱的清晰放大, 下一句清晰不放大, 其余微模糊
      line.classList.toggle("active", position === index);
      line.classList.toggle("upnext", position === index + 1);
    });
    if (pipLyricsFollow && index >= 0 && lines[index]) {
      pipScrollLyricsTo(lines[index]);
    }
  }
  if (!pipLyricsFollow) maybeResumePipFollow();
}

/** 窗里滚到某行居中 —— rAF 指数缓出, 与播放页同款手感; 帧走
    pipWindow 自己的 requestAnimationFrame: PiP 窗可见就照常跑帧,
    主页切后台被浏览器限帧也不卡词。 */
function pipScrollLyricsTo(lineElement) {
  if (!pipWindow) return;
  const container = pipWindow.document.getElementById("pip-lyrics");
  if (!container.contains(lineElement)) return;   // 换曲重铺前的旧行: 别滚
  pipScrollTarget = lineElement;
  if (!pipScrollRaf) {
    pipScrollLastTime = pipWindow.performance.now();
    pipScrollRaf = pipWindow.requestAnimationFrame(pipScrollFrame);
  }
}

function pipScrollFrame(now) {
  pipScrollRaf = 0;
  const container = pipWindow && pipWindow.document
    && pipWindow.document.getElementById("pip-lyrics");
  const line = pipScrollTarget;
  if (!container || !line || !container.contains(line)) {
    pipScrollTarget = null;
    return;
  }
  pipSelfScrollUntil = Date.now() + 250;   // 这帧的 scrollTop 是自己写的
  const dt = Math.min(Math.max(now - pipScrollLastTime, 0), 40) / 1000;
  pipScrollLastTime = now;
  // 目标钳到可达区间: 头几行居中的目标在容器顶之上 (负), 短词/高窗时
  // 深行的目标又可能超过最大可滚距离 (词不满一屏时干脆滚不动) — 两头
  // 都钳, 缓动必有可达终点, 不然 rAF 永远差一截收不了尾 (空转, 手动
  // 滑词也被宽限期一直盖住)
  const target = Math.max(0, Math.min(
    container.scrollHeight - container.clientHeight,
    line.offsetTop - container.clientHeight / 2 + line.offsetHeight / 2));
  const remaining = target - container.scrollTop;
  if (Math.abs(remaining) < 1) {
    container.scrollTop = target;
    pipScrollTarget = null;
    return;
  }
  const step = remaining * Math.min(1, dt * 10);   // 指数缓出
  // 步长地板 1px: scrollTop 会被取整的环境 (移动端/浏览器缩放≠100%) 里
  // 不足 1px 的步子整型化后原地踏步, 缓动尾巴永远迈不过上面的收敛门槛
  // (rAF 空转) — 地板保证每帧至少挪 1px, 尾巴必能走完
  container.scrollTop += Math.abs(step) < 1 ? (step < 0 ? -1 : 1) : step;
  pipScrollRaf = pipWindow.requestAnimationFrame(pipScrollFrame);
}

function cancelPipLyricsScroll() {
  if (pipWindow && pipScrollRaf) pipWindow.cancelAnimationFrame(pipScrollRaf);
  pipScrollRaf = 0;
  pipScrollTarget = null;
}

/** 手动滑词后静置够了就回到跟唱 (静置窗口与播放页同一常数)。 */
function maybeResumePipFollow() {
  if (pipLyricsFollow) return;
  if (Date.now() - pipLyricsLastScrollAt < LYRICS_FOLLOW_RESUME_MS) return;
  pipLyricsFollow = true;
}

/** 小窗关了收尾 (pagehide 时由 music-pip.js 喊): 撤动画 + 清防串门闩。 */
function pipResetLyrics() {
  cancelPipLyricsScroll();
  pipLyricsTrackId = 0;
  pipLyricIndex = -2;
}

/** 歌词容器的手动滑词监听 (开窗时挂上): 手动滑词 = 浏览 — 暂停跟唱只亮
    不滚; 自己动画写的滚动不算手动。手指按下的那一刻先撤掉滚动动画并清
    宽限 (与播放页同款), 之后的位置全算用户的 —— 不然动画追行中上手滑,
    头几拍 scroll 会被当成自己写的, 跟手指抢。 */
function bindPipLyrics(container) {
  container.addEventListener("pointerdown", () => {
    cancelPipLyricsScroll();
    pipSelfScrollUntil = 0;
  });
  container.addEventListener("scroll", () => {
    if (pipScrollTarget || Date.now() < pipSelfScrollUntil) return;
    pipLyricsFollow = false;
    pipLyricsLastScrollAt = Date.now();
  });
}
