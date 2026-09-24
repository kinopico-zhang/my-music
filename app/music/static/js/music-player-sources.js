// music-player-sources — My Music 曲目音频源解析与失败兜底: 本地字节
// (手动下载 > 自动缓存) 优先, 流媒体直连兜底; 播放挂了先试缓存救回,
// 不行跳下一首。
// 拆自 music-player-queue (1.8.76: 换源/兜底与队列驱动分家, queue 顶到
// 200 行帽按逻辑再切一刀 —— loadTrack 管"播什么", 这儿管"声音从哪来")。
// 1.8.76 锁屏/后台连播三刀的源侧两刀: 已下载/已自动缓存的歌在 loadTrack
// 里先按流占位 (同步赋址不断流), 这儿补刀换 blob (还没出声才换); 流挂了
// localBlobFor 救回原位置接着放, 没有就 playerNext 强续 —— 连挂 3 首封顶
// 停住 (playFailStreak), 边界流一挂不再死在半路。
// 1.8.78 的打断后自动续播 1.8.83 撤了 (用户实报: 切去别的 app 看视频,
// 视频会被这边自动恢复的音乐打断) —— 打断后想接着播自己点 (锁屏键/
// 回 app 点播放, 1.8.71 的解锁还在)。
// 1.8.87 断网连播两刀 (用户实报「开车时一首放完, 下一首停在暂停」, 全程
// 缓存歌在播、服务日志零请求): ① 补刀换源掐了流占位上挂起的 play() 且
// wasPaused 读到假 true 不再重启 —— 起播意图带进换源, 换完自己下达;
// ② error 分家: 网络 (code 2/0) 不跳歌不计数, 就地挂起回前台/计时到点
// 自动重试 (不在前台绝不自己开声, 1.8.83 规矩不破); 解码 (3/4) 才连跳封顶。
"use strict";
/* global audioElement, autoCache, autoCacheEnabled, currentTrack, downloads,
          downloadsEnabled, noteAudioSourceChanged, playerNext, startAudio,
          toast */
/* exported discardNetworkRetry, directStreamURL, loadSequence,
            notePlaybackFailed, notePlaybackSucceeded,
            playerUpgradeDownloadedSource, playingObjectURL,
            resolveTrackSource, trackLocalCached */

let playingObjectURL = "";   // audio 正在用的 blob 源; 换曲时 revoke (一首几十 MB, 攒着会撑爆手机内存)
let loadSequence = 0;        // 换源解析的过站号: 快速连切, 旧的解析回来直接作废
let playFailStreak = 0;      // 连挂计数: 出声即清零, 连挂 3 首停 (无限跳歌封顶)
let pendingNetworkRetry = false;  // 断网挂起 (1.8.87 ②): 歌/位置原地不动, 等信号自动接着放
let networkRetryTimer = 0;        // 挂起期间的一次性重试计时 (iOS 冻结没声的页面, 多半靠回前台兜)
let networkRetryToasted = false;  // 一次断网只提一声 (出声/换曲重置)

/** 下载能力在线且这首歌已手动下载? (调用可能早于下载模块加载 —— boot
    顺序, typeof 兜住还没影子的全局, 不至于 ReferenceError。) */
function trackDownloaded(trackId) {
  return typeof downloadsEnabled !== "undefined" && downloadsEnabled
    && downloads && downloads.isDownloaded(trackId);
}

/** 自动缓存里有这首? (同上一道 typeof 兜底: 集成模块加载更晚)。 */
function autoCached(trackId) {
  return typeof autoCacheEnabled !== "undefined" && autoCacheEnabled
    && autoCache && autoCache.has(trackId);
}

/** 本地 (手动下载或自动缓存) 有这份音? 同步答, 只看索引不碰字节。 */
function trackLocalCached(trackId) {
  return trackDownloaded(trackId) || autoCached(trackId);
}

/** 流媒体直连地址: SW 见 ?direct 标记放行, 浏览器媒体栈自己连网络。 */
function directStreamURL(trackId) {
  return `/music/media/stream/${trackId}?direct=1`;
}

/** 本地音字节: 手动下载优先 (用户亲手下的不许被 LRU 清), 自动缓存次之。 */
async function localBlobFor(trackId) {
  if (trackDownloaded(trackId)) {
    const blob = await downloads.cachedBlob(trackId);
    if (blob) return blob;
  }
  if (autoCached(trackId)) return autoCache.blob(trackId);
  return null;
}

/** 曲目音频源: 本地有直读成 blob, 其余流媒体直连。 */
async function resolveTrackSource(trackId) {
  const blob = await localBlobFor(trackId);
  if (blob) return URL.createObjectURL(blob);
  return directStreamURL(trackId);
}

/** 补刀换缓存源 (1.8.59 恢复现场引入, 1.8.76 扩到常规切歌): 缓存歌在
    loadTrack 里先按流占位 (同步赋址, iOS 在「没有出声的音频」那一瞬能
    把整页挂起, 不能等异步读), 本地字节一就位就换 blob; 流上已出声就按
    流听完 (onlyIfNotAudible)。resumeAfterSwap (1.8.87 ①): 占位上挂着的
    play() 会被换 src 掐成 AbortError 吞掉, 且 audio.paused 那刻还是假
    true —— 起播意图由这边带回, 换完自己重启, 不然永远停在暂停态。 */
async function playerUpgradeDownloadedSource(onlyIfNotAudible, resumeAfterSwap) {
  const track = currentTrack;
  const audio = audioElement();
  if (!track || !trackLocalCached(track.track_id)) return;
  if (!audio.src || audio.src.startsWith("blob:")) return;   // 已是缓存源
  const token = ++loadSequence;
  const blob = await localBlobFor(track.track_id);
  if (!blob || token !== loadSequence || currentTrack !== track) return;
  if (onlyIfNotAudible && !audio.paused && audio.readyState >= 2) return;
  const wasPaused = audio.paused;
  const at = audio.currentTime;          // 恢复态的待生效进度别丢
  const source = URL.createObjectURL(blob);
  if (playingObjectURL) URL.revokeObjectURL(playingObjectURL);
  playingObjectURL = source;
  audio.src = source;
  noteAudioSourceChanged();   // 不然 startAudio 会把新源再白重挂一次
  audio.currentTime = at;
  if (!wasPaused || resumeAfterSwap) startAudio().catch(() => {});
}

/** 出声了: 连挂计数清零, 断网挂起重试也不需要了 (playing 事件里调)。 */
function notePlaybackSucceeded() {
  playFailStreak = 0;
  networkRetryToasted = false;   // 下次断网重新提一声
  discardNetworkRetry();
}

/** 播放挂了 (audio error 事件)。1.8.87 ② 分家 (用户点名「服务不稳定也
    要有恢复措施」): 网络 (2/0) 是信号问题 —— 本地有整曲立刻换过去接着
    放, 没有就地挂起等信号, 不跳歌不计数; 解码不了 (3/4) 才是歌本身的
    问题, 照旧救回/跳下一首, 连挂 3 首封顶 (烂文件串不无限跳)。 */
function notePlaybackFailed() {
  if (!currentTrack) return;
  const code = audioElement().error ? audioElement().error.code : 0;
  if (code !== 3 && code !== 4) {
    if (trackLocalCached(currentTrack.track_id)) recoverFailedPlayback(true);
    else armNetworkRetry();   // 缓存有立刻救回; 没有: 不跳歌, 原地等信号
    return;
  }
  playFailStreak += 1;
  if (playFailStreak >= 3) {
    playFailStreak = 0;    // 停下报一次; 下次点播放重新计
    toast("连着几首都播不了, 先停了");
    return;
  }
  recoverFailedPlayback();
}

/** 失败兜底 (1.8.76 第三刀): 当前曲先问本地字节 (流挂了, 缓存里可能有
    整曲), 有就原位置接着放; 没有就 playerNext(true) 强续 —— 这之前
    error 只弹一句「这首播放失败了」就地停住, 锁屏连播死在半路的帮凶。
    stayOnTrack (1.8.87 ② 断网路径): 救不回也不跳歌, 转挂起等信号。 */
async function recoverFailedPlayback(stayOnTrack) {
  const track = currentTrack;
  if (!track) return;
  const at = audioElement().currentTime;   // 挂掉时的位置, 缓存救回接着放
  const token = ++loadSequence;
  const blob = await localBlobFor(track.track_id);
  if (token !== loadSequence || currentTrack !== track) return;   // 已经切走了
  if (!blob) {
    // 索引说有缓存, 字节却读不出: 当断网挂起 (计时节流, 不跟 error 转圈)
    if (stayOnTrack) { armNetworkRetry(); return; }
    playerNext(true);
    return;
  }
  const audio = audioElement();
  const source = URL.createObjectURL(blob);
  if (playingObjectURL) URL.revokeObjectURL(playingObjectURL);
  playingObjectURL = source;
  audio.src = source;
  noteAudioSourceChanged();
  if (at > 0 && track.duration_seconds) {
    audio.currentTime = Math.min(at, track.duration_seconds - 1);   // blob 是整曲, 旧位置接得上
  }
  startAudio().catch(() => {});
}

/** 挂起重试: 缓存里有了换缓存源, 没有就同一首再拉流 (startAudio 自带
    1.8.71/84 重挂解锁); 还断网 error 再来重新挂起 (计时节流)。绝不跳歌。 */
function retryAfterNetworkDrop() {
  discardNetworkRetry();
  if (!currentTrack) return;
  if (trackLocalCached(currentTrack.track_id)) {
    recoverFailedPlayback(true);
    return;
  }
  startAudio().catch(() => {});
}

/** 断网挂起: 歌和位置原地不动, 计时一次 + 回前台即刻重试。页面不在前台
    绝不自己开声 (1.8.83 规矩); iOS 冻结没声的页面, 计时多半靠回前台兜。 */
function armNetworkRetry() {
  pendingNetworkRetry = true;
  if (!networkRetryTimer) {
    networkRetryTimer = setTimeout(() => {
      networkRetryTimer = 0;
      if (!pendingNetworkRetry || document.hidden) return;   // 隐着: 等回前台
      retryAfterNetworkDrop();
    }, 15000);
  }
  if (!networkRetryToasted) {
    networkRetryToasted = true;
    toast("信号断了, 回来会自动接着放");
  }
}

/** 挂起重试作废: 换曲了/出声了就是不需要了 (loadTrack 与 playing 事件里调)。 */
function discardNetworkRetry() {
  pendingNetworkRetry = false;
  if (networkRetryTimer) {
    clearTimeout(networkRetryTimer);
    networkRetryTimer = 0;
  }
}

// 回前台: 挂起中的断网重试即刻试一把 (开车等红灯点亮手机那下)。
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible" && pendingNetworkRetry) {
    retryAfterNetworkDrop();
  }
});
