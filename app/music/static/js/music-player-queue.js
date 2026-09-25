// music-player-queue — My Music 队列驱动: 开播/暂停/上下曲/跳过不可播, loadTrack 换源。
// 拆自 music-player.js (结构化重构: 按 music.html 里的顺序加载, 跨模块引用走全局;
// 1.8.59 下一曲预取拆去 music-player-prefetch)。
// 1.8.66 切歌不改播放状态; 1.8.68 修播放键误报「被浏览器拦」; 1.8.71 起播/暂停搬去 audio-events;
// 1.8.76 音频源解析与失败兜底拆去 music-player-sources, loadTrack 源同步落定
// (锁屏/后台连播主刀: ended 到下一曲 play() 之间不再隔着异步读缓存)。
"use strict";
/* global audioElement, createPlayQueue,
          currentTrack: writable, directStreamURL, discardNetworkRetry,
          discardPrefetch, loadLyrics, lyricsActiveIndex: writable,
          lyricsCache, lyricsViewOpen, noteAudioSourceChanged, pauseAudio,
          playQueue: writable, playRecorded: writable,
          playerUpgradeDownloadedSource, playingObjectURL: writable,
          prefetchLyrics, prefetchNextTrack, prefetched: writable,
          queueAdvance, queueCurrent, queueGoBack, queueShuffleAll,
          queueViewOpen, renderPlayerChrome, renderQueueView,
          savePlayerState, startAudio, syncLyricsButton, toast,
          trackChangeListeners, trackLocalCached, updateMediaSession */
/* exported loadTrack, lyricsActiveIndex, onTrackChange, playRecorded,
            playerCurrentTrack, playerCurrentTrackId, playerIsPlaying,
            playerNext, playerPrevious, playerStart, playerToggle */

// ------------------------------------------------------------ 队列驱动

/** 浏览页入口: 给一批曲目 (及起始下标) 开播; shuffleOn = 随机播这批。 */
function playerStart(tracks, startIndex, shuffleOn) {
  playQueue = createPlayQueue(tracks, startIndex);
  playQueue.repeat = "all";   // 1.8.89 三态循环: 新队列默认列表循环 (关态退役)
  if (shuffleOn) queueShuffleAll(playQueue);   // 整队洗牌 = 随机循环态
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
  let track = queueAdvance(playQueue);
  // 1.8.76 连播不栽在播不了的格式上: tak/dsf/ape 一路跳过 (预取早就
  // 会跳, 队列推进一直没跳 —— 歌单里夹一首播不了的, 连播到那就地停住)
  while (track && !track.playable) track = queueAdvance(playQueue);
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
  discardNetworkRetry();                   // 断网挂起的重试跟旧曲作废 (1.8.87)
  renderPlayerChrome();
  // 队列没开着就不整页重铺 (翻开时会现铺) —— innerHTML 大重建在主线程,
  // 切歌那一拍挤上去, 封面 3D 落定的动画跟着掉帧 (1.8.61 修「切歌很卡」)
  if (queueViewOpen) renderQueueView();
  if (lyricsViewOpen) loadLyrics();
  updateMediaSession();
  for (const listener of trackChangeListeners) listener(track);
  // 1.8.76 连播去 await (锁屏/后台自停的主刀): 源同步落定 —— ended 事件
  // 里到下一曲 play() 之间原本隔着一步 Cache API 异步读, iOS 恰在「没有
  // 出声的音频」那一瞬能把整页挂起, 挂起后微任务不再回来 = 连播死在半路。
  // 已下载/已自动缓存的先按流占位 (手势内同步赋址), 缓存直读一就位就
  // 补刀换 blob (还没出声才换 —— music-player-sources, 过站号/换曲闸都在
  // 那边, 连切由 currentTrack 对照作废)。
  // 1.8.87 ① 补刀带上起播意图: 流占位上挂着的 play() 会被换 src 掐成
  // AbortError 吞掉, 且那一刻 audio.paused 读到的还是假 true (play 挂起
  // ≠在播), 没人再把播放下达回来 = 歌对了却永远停在暂停态 (开车断网
  // 连播断的根) —— 换完源由补刀自己重启。
  const source = prefetchedURL || directStreamURL(track.track_id);
  playingObjectURL = prefetchedURL;   // blob 源记账 (换曲时 revoke)
  audio.src = source;
  if (!prefetchedURL && trackLocalCached(track.track_id)) {
    playerUpgradeDownloadedSource(true, autoplay);   // 补刀换缓存源; 起播意图带回
  }
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
