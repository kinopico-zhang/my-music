// music-player-persistence — My Music 播放现场持久化: localStorage 存/恢复 (队列/曲目/进度)。
// 拆自 music-player.js (结构化重构: 按 music.html 里的顺序加载, 跨模块引用走全局)。
// 1.8.142 起现场再镜像一份到服务端 (localStorage 会被 Safari 清掉): 队列变
// 全量 PUT, 进度 5 秒一拍 tick PUT; 开局本地档没了, 从服务端回填。
"use strict";
/* global PLAYER_STATE_KEY, audioElement, createPlayQueue, currentTrack,
          fetchJSON, loadTrack, playQueue: writable, queueCurrent */
/* exported playerRestore, playerStateServerBackfill, savePlayerState */

// ------------------------------------------------------------ 持久化
function savePlayerState() {
  if (!playQueue || !currentTrack) return;
  const audio = audioElement();
  try {
    localStorage.setItem(PLAYER_STATE_KEY, JSON.stringify({
      tracks: playQueue.tracks.slice(0, 500),
      index: playQueue.tracks.indexOf(currentTrack),
      order: playQueue.order.slice(0, 500),     // 拖拽换过的顺序别丢 (随机序也保真)
      position: playQueue.position,
      time: audio.currentTime,
      shuffle: playQueue.shuffle,
      repeat: playQueue.repeat,
    }));
  } catch (_error) { /* 存储满了就算了, 不影响听歌 */ }
  syncPlayerState();
}

// ------------------------------------------------- 服务端镜像 (1.8.142)
let lastSyncedQueue = "";   // 上次发出的队列 JSON (变没变 → 全量还是 tick)
let lastTickSentAt = 0;     // 上次 tick 发出时刻 (节流 ≥4 秒)

function sendPlayerState(url, body, keepalive) {
  return fetchJSON(url, {               // 失败由调用方收: 全量要作废签, tick 无所谓
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    keepalive,
  });
}

function syncPlayerState() {
  if (!playQueue || !currentTrack) return;
  const audio = audioElement();
  const index = playQueue.tracks.indexOf(currentTrack);
  if (index < 0) return;
  const tracks = playQueue.tracks.slice(0, 500);
  const order = playQueue.order.slice(0, 500);
  const queueJson = JSON.stringify([tracks, order, playQueue.shuffle,
                                    playQueue.repeat]);
  const now = Date.now();
  const where = { index, position: playQueue.position,
                  time: audio.currentTime };
  if (queueJson !== lastSyncedQueue) {          // 队列变了: 全量 (大行, 别勤写)
    lastSyncedQueue = queueJson;
    lastTickSentAt = now;
    sendPlayerState("/music/api/player-state", {
      tracks, order, shuffle: playQueue.shuffle, repeat: playQueue.repeat,
      ...where,
    }).catch(() => { lastSyncedQueue = ""; });  // 发丢了作废签, 下趟重发整包
    return;
  }
  // tick 节流 (≥4 秒); 页面正在离开时不节 —— keepalive 把这笔带走
  if (now - lastTickSentAt < 4000
      && document.visibilityState === "visible") return;
  lastTickSentAt = now;
  sendPlayerState("/music/api/player-state/tick", where, true)
    .catch(() => {});       // 小拍丢了下拍补, 不作废签
}

/** 把一份现场档 (localStorage 或服务端) 落回播放器: 恢复到暂停态,
 * iOS 不许自动播。档的 shape 两处同源, 这里是唯一消费口。 */
function applySavedState(saved) {
  if (!saved || !Array.isArray(saved.tracks) || !saved.tracks.length) {
    return false;
  }
  playQueue = createPlayQueue(saved.tracks, saved.index || 0);
  playQueue.repeat = saved.repeat === "one" ? "one" : "all";   // 1.8.89 三态: off 退役, 老档落列表循环
  // 存过顺序 (拖拽换位/随机洗牌后的 order) 就原样恢复: 队列视图所见即所存。
  // 校验是完整排列才认 (老存档/被截断的都不认, 回落原始顺序); 没恢复成
  // 顺序就不认 shuffle 旗标 —— 顺序是重建的, 旗标亮着却按原序走会骗人。
  let orderRestored = false;
  if (Array.isArray(saved.order) && saved.order.length === saved.tracks.length
      && new Set(saved.order).size === saved.tracks.length
      && saved.order.every((n) => Number.isInteger(n)
                            && n >= 0 && n < saved.tracks.length)) {
    playQueue.order = saved.order.slice();
    playQueue.position = Math.min(Math.max(0, saved.position || 0),
                                  saved.order.length - 1);
    orderRestored = true;
  }
  playQueue.shuffle = orderRestored && !!saved.shuffle;
  const track = queueCurrent(playQueue);
  if (!track) { playQueue = null; return false; }
  // 1.8.59 起走 loadTrack 同一条换源路 (流媒体直连 / 已下载缓存直读),
  // 存档进度由 startTime 带上 (换源之后才写 —— 待生效进度只落在新源上,
  // 不会像旧版那样漏到之后点开的歌上)
  loadTrack(track, false, saved.time || 0);
  return true;
}

/** 冷启动恢复上次听到的地方 (本地档, 同步秒回)。 */
function playerRestore() {
  let saved = null;
  try {
    saved = JSON.parse(localStorage.getItem(PLAYER_STATE_KEY) || "null");
  } catch (_error) { saved = null; }
  applySavedState(saved);
}

/** 开局服务端回填 (1.8.142): 本地档被 Safari 清了, 从服务端把现场捞回来
 * (换台设备登录也接得上)。本地已有现场/用户已动了就不抢; 捞回来顺手写回
 * localStorage —— 下次开局又秒回。 */
async function playerStateServerBackfill() {
  if (currentTrack) return;
  let state = null;
  try { state = await fetchJSON("/music/api/player-state"); }
  catch (_error) { return; }                    // 离线开局不碍事
  if (currentTrack) return;                     // 等待期间用户动了也不抢
  const queue = state && state.queue;
  if (!queue || !Array.isArray(queue.tracks) || !queue.tracks.length) return;
  const position = state.position || {};
  const saved = {
    tracks: queue.tracks, order: queue.order,
    index: position.index || 0, position: position.position || 0,
    time: position.time || 0,
    shuffle: queue.shuffle, repeat: queue.repeat,
  };
  if (!applySavedState(saved)) return;
  lastSyncedQueue = JSON.stringify([saved.tracks, saved.order,
                                    saved.shuffle, saved.repeat]);
  try { localStorage.setItem(PLAYER_STATE_KEY, JSON.stringify(saved)); }
  catch (_error) { /* 存不进就只靠服务端那份 */ }
}
