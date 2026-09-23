// music-player-queue — My Music 队列驱动: 开播/暂停/上下曲/跳过不可播, loadTrack 换源。
// 拆自 music-player.js (结构化重构: 按 music.html 里的顺序加载, 跨模块引用走全局;
// 1.8.59 下一曲预取拆去 music-player-prefetch)。
// 1.8.66 切歌不改播放状态; 1.8.68 修播放键误报「被浏览器拦」; 1.8.71 起播/暂停搬去 audio-events。
"use strict";
/* global audioElement, createPlayQueue, currentTrack: writable, discardPrefetch,
          downloads, downloadsEnabled, loadLyrics, lyricsActiveIndex: writable,
          lyricsCache, lyricsViewOpen, noteAudioSourceChanged, pauseAudio,
          playQueue: writable, playRecorded: writable, prefetchLyrics,
          prefetchNextTrack, prefetched: writable, queueAdvance, queueCurrent,
          queueGoBack, queueShuffleAll, queueViewOpen, renderPlayerChrome,
          renderQueueView, savePlayerState, startAudio, syncLyricsButton, toast,
          trackChangeListeners, updateMediaSession */
/* exported loadTrack, lyricsActiveIndex, onTrackChange, playRecorded,
            playerCurrentTrack, playerCurrentTrackId, playerIsPlaying, playerNext,
            playerPrevious, playerStart, playerToggle, playerUpgradeDownloadedSource,
            resolveTrackSource */

// ------------------------------------------------------------ 队列驱动

/** 浏览页入口: 给一批曲目 (及起始下标) 开播; shuffleOn = 随机播这批。 */
function playerStart(tracks, startIndex, shuffleOn) {
  playQueue = createPlayQueue(tracks, startIndex);
  if (shuffleOn) queueShuffleAll(playQueue);   // 整队洗牌, 不是"当前曲钉队首"
  const track = queueCurrent(playQueue);
  if (!track) return;
  if (!track.playable) {
    advanceToPlayable();
    return;
  }
  loadTrack(track, true);
}

/** 起播统一入口 (1.8.71 起住 music-player-audio-events, 带打断解锁)。 */

function playerToggle() {
  const audio = audioElement();
  if (!currentTrack) return;
  if (!audio.paused) {
    if (audio.readyState < 3) return;   // 起播还在缓冲: 别掐 (掐了 = AbortError 误报拦截)
    pauseAudio();
    return;
  }
  startAudio().catch((e) => {
    // AbortError = 半路被换源/暂停打断 (正常接力), 只有真的被浏览器拦才提示
    if (e && e.name === "NotAllowedError") toast("播放被浏览器拦了, 再点一次");
  });
}

function playerNext(forceAutoplay) {
  if (!playQueue) return;
  const track = queueAdvance(playQueue);
  if (!track) {                       // 队尾: 停在原地 (苹果同款)
    toast("播完了");
    return;
  }
  // 1.8.66 切歌不改播放状态: 暂停中切歌保持暂停 (自然播完连播传 true 强续)
  loadTrack(track, forceAutoplay === true || !audioElement().paused);
}

function playerPrevious() {
  if (!playQueue) return;
  const audio = audioElement();
  if (audio.currentTime > 3) {        // 播过 3 秒先回本曲开头
    audio.currentTime = 0;
    return;
  }
  const track = queueGoBack(playQueue);
  if (track) loadTrack(track, !audio.paused);   // 1.8.66 切歌不改播放状态
}

/** 不可播格式连跳, 直到遇到能播的 (全队都播不了就提示)。 */
function advanceToPlayable() {
  let track = queueCurrent(playQueue);
  while (track && !track.playable) {
    track = queueAdvance(playQueue);
  }
  if (!track) {
    toast("这批曲目浏览器都播不了");
    return;
  }
  loadTrack(track, true);
}

/** 载入曲目: 音频源 (预取到位直接用 blob, 秒切) + 迷你条/全屏页/锁屏
    元数据 + 歌词缓存失效 + 顺手预取下一曲。startTime = 待生效进度
    (点播一律 0; 冷启动恢复带上存档进度)。 */
let playingObjectURL = "";   // audio 正在用的 blob 源; 换曲时 revoke (一首几十 MB, 攒着会撑爆手机内存)
let loadSequence = 0;        // 换源解析的过站号: 快速连切, 旧的解析回来直接作废

async function loadTrack(track, autoplay, startTime = 0) {
  currentTrack = track;
  playRecorded = false;
  lyricsCache.delete(track.track_id);      // 每次换曲重取 (歌词可能刚扫描进来)
  syncLyricsButton();    // 1.8.20 键默认灰 (当没词), 探明有词才亮 (视图开着保持可点)
  prefetchLyrics(track);
  lyricsActiveIndex = -1;
  const audio = audioElement();
  const prefetchedURL = prefetched && prefetched.trackId === track.track_id
    ? prefetched.objectURL : "";
  if (playingObjectURL) URL.revokeObjectURL(playingObjectURL);   // 上一曲用完的 blob
  playingObjectURL = "";
  if (prefetchedURL) prefetched = null;    // 占位交给 audio, 别再 revoke
  else discardPrefetch();                  // 其余情况旧预取作废
  renderPlayerChrome();
  // 队列没开着就不整页重铺 (翻开时会现铺) —— innerHTML 大重建在主线程,
  // 切歌那一拍挤上去, 封面 3D 落定的动画跟着掉帧 (1.8.61 修「切歌很卡」)
  if (queueViewOpen) renderQueueView();
  if (lyricsViewOpen) loadLyrics();
  updateMediaSession();
  for (const listener of trackChangeListeners) listener(track);
  // 1.8.59 锁屏自停根修 (iOS 27 用户报「播着播着自己停了, 开 app 又自动
  // 续播」): 音频流原本全经 SW 中转, iOS 锁屏会冻结 SW —— 管线要不到
  // 数据断粮自停, 开屏解冻挂起请求补上又自动续播。现在播放全程绕开 SW:
  // 流媒体带 ?direct 标记让 SW 放行 (同步赋址, 起播留在点按手势里);
  // 已下载的直读 Cache API 成 blob (异步一步, 断网也照播)。
  let source = prefetchedURL
    || (trackDownloaded(track.track_id) ? "" : directStreamURL(track.track_id));
  if (!source) {
    if (!audio.paused) pauseAudio();   // 读缓存要一步: 先掐住旧曲别多响
    const token = ++loadSequence;
    const resolved = await resolveTrackSource(track.track_id);
    if (token !== loadSequence || currentTrack !== track) return;   // 连切抢了先
    source = resolved;
  }
  playingObjectURL = source.startsWith("blob:") ? source : "";
  audio.src = source;
  noteAudioSourceChanged();   // 换了新源, 打断解锁态作废 (1.8.71)
  // 点播一律从头。冷启动恢复写过一次"待生效进度" (preload=none 时它一直
  // 挂着不生效), Safari 会把它漏到之后点开的歌上 —— 从一半播起的真凶。
  // 显式写 currentTime (换源之后写, 只落在新源上): HAVE_NOTHING 时是覆盖
  // 待生效进度, 已载入时是直接倒到目标 (点播 0 / 恢复存档进度)。
  audio.currentTime = startTime;
  savePlayerState();
  prefetchNextTrack();
  if (autoplay) startAudio().catch(() => { /* iOS 偶发拒绝: 保持暂停态 */ });
}

/** 下载能力在线且这首歌已下载? (恢复现场跑在下载模块加载前 —— boot
    顺序, typeof 兜住还没影子的全局, 不至于 ReferenceError。) */
function trackDownloaded(trackId) {
  return typeof downloadsEnabled !== "undefined" && downloadsEnabled
    && downloads && downloads.isDownloaded(trackId);
}

/** 流媒体直连地址: SW 见 ?direct 标记放行, 浏览器媒体栈自己连网络。 */
function directStreamURL(trackId) {
  return `/music/media/stream/${trackId}?direct=1`;
}

/** 曲目音频源: 已下载的直读 Cache API 成 blob, 其余流媒体直连。 */
async function resolveTrackSource(trackId) {
  if (trackDownloaded(trackId)) {
    const blob = await downloads.cachedBlob(trackId);
    if (blob) return URL.createObjectURL(blob);
  }
  return directStreamURL(trackId);
}

/** 恢复现场的补刀 (1.8.59): 已下载的当前曲在恢复时只能按流媒体占位
    (那时下载模块还没加载) —— 全模块就位后 (app-boot 收尾) 换成缓存
    直读的 blob 源, 锁屏 SW 冻结掐不断, 断网也照播。 */
async function playerUpgradeDownloadedSource() {
  const track = currentTrack;
  const audio = audioElement();
  if (!track || !trackDownloaded(track.track_id)) return;
  if (!audio.src || audio.src.startsWith("blob:")) return;   // 已是缓存源
  const token = ++loadSequence;
  const source = await resolveTrackSource(track.track_id);
  if (token !== loadSequence || currentTrack !== track
      || !source.startsWith("blob:")) {
    if (source.startsWith("blob:")) URL.revokeObjectURL(source);
    return;
  }
  const wasPaused = audio.paused;
  const at = audio.currentTime;          // 恢复态的待生效进度别丢
  if (playingObjectURL) URL.revokeObjectURL(playingObjectURL);
  playingObjectURL = source;
  audio.src = source;
  noteAudioSourceChanged();   // 不然 startAudio 会把新源再白重挂一次
  audio.currentTime = at;
  if (!wasPaused) startAudio().catch(() => {});
}

function playerCurrentTrackId() {
  return currentTrack ? currentTrack.track_id : 0;
}

/** 全屏页 ⋯ / ♥ 按钮要的当前曲目 (含恢复现场那首)。 */
function playerCurrentTrack() {
  return currentTrack;
}

function playerIsPlaying() {
  return !!currentTrack && !audioElement().paused;
}

function onTrackChange(listener) {
  trackChangeListeners.push(listener);
}
