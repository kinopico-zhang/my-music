// share-viewer-queue — 分享页待播队列视图 (1.8.130 新增, 占封面区)。
// 应用 music-player-queue-view 的只读版: 分享清单即待播队列, 从当前曲
// 往后排, 点行跳播。换序/左滑删除不带 —— 那是登录用户的队列管理, 访客
// 只有这份分享。样式整用应用的 music-queue.css, 只有行动条/行封面是
// 分享页的 svg 动条 (在 share-viewer-player.css 补几条)。
"use strict";
/* global $, BARS_SVG, artURL, audio, currentTrack, esc, lyricsViewOpen,
          playQueue, queueUpcoming, queueViewOpen: writable, toggleLyricsView */
/* exported closeQueueView, renderQueueView, toggleQueueView */

function closeQueueView() {
  queueViewOpen = false;
  $("#fp-queue").hidden = true;
  $("#fp-art-wrap").hidden = false;
  $("#fp-queue-btn").classList.remove("on");
  $("#full-player").classList.remove("queue");
}

function toggleQueueView() {
  if (queueViewOpen) { closeQueueView(); return; }
  if (lyricsViewOpen) toggleLyricsView();   // 同住封面区, 二选一 (app 同款)
  queueViewOpen = true;
  renderQueueView();
  $("#fp-art-wrap").hidden = true;
  $("#fp-queue").hidden = false;
  $("#fp-queue-btn").classList.add("on");
  $("#full-player").classList.add("queue");
}

/** 队列行封面 (app trackArtHTML 的分享版): 走分享 token 的公开路由,
    裂图退 ♪ 占位 (类名跟 app 的 .t-art 同名, 样式在 share-viewer-player)。 */
function queueArtHTML(track) {
  return `<img class="t-art" loading="lazy" decoding="async" alt=""
    src="${artURL(track)}"
    onerror="this.replaceWith(Object.assign(document.createElement('span'),
      {className:'t-art',textContent:'♪'}))">`;
}

function renderQueueView() {
  if (!playQueue) return;
  const upcoming = queueUpcoming(playQueue);
  const currentId = currentTrack ? currentTrack.track_id : 0;
  $("#fq-count").textContent = `${upcoming.length} 首歌曲`;
  $("#queue-list").innerHTML = upcoming.map((track) => {
    const on = track.track_id === currentId;
    return `<button class="queue-row${on ? " on" : ""}${on && !audio.paused ? " playing" : ""}"
            data-queue-track-id="${track.track_id}">
      <span class="q-lead">${on ? BARS_SVG : ""}${queueArtHTML(track)}</span>
      <span class="q-main">
        <span class="q-title">${esc(track.title)}</span>
        <span class="q-artist">${esc(track.artist)}</span>
      </span>
    </button>`;
  }).join("") || '<div class="lyrics-empty">队列是空的</div>';
}
