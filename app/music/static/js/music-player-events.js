// music-player-events — My Music 播放器事件绑定 (音频/按钮/键盘) + 开局接线。
// 拆自 music-player.js (结构化重构: 代码逐字节未动, 按 music.html 里的顺序加载, 跨模块引用走全局)。
"use strict";
/* global $, audioElement, bindDismissDrag, bindPlayerAudioEvents, bindQueueDrag,
          cancelLyricsScroll, closeFullPlayer,
          fpDismissDragged: writable, initArtStage, loadTrack,
          lyricsAutoScrolling, lyricsFollowPaused: writable, lyricsLastScrollAt: writable,
          lyricsViewOpen, openFullPlayer, playQueue, playerNext, playerOpen,
          playerPrevious, playerToggle,
          queueCyclePlayMode, queueJump, queueViewOpen,
          renderQueueView, resumeLyricsFollow,
          savePlayerState, toast, toggleLyricsView, toggleQueueView,
          updatePlayModeButton */
/* exported bindPlayerEvents, lyricsFollowPaused, lyricsLastScrollAt */

// ------------------------------------------------------------ 事件绑定

function bindPlayerEvents() {
  const audio = audioElement();

  // 气泡: 播放/暂停键 + 点开全屏页 (上下曲键 1.8.94 用户点名「左右滑动
  // 切歌」撤掉 —— 切歌走气泡横滑, 绑定在 music-bubble-swipe)
  $("#mini-play").addEventListener("click", (event) => { event.stopPropagation(); playerToggle(); });
  $("#mini-open").addEventListener("click", openFullPlayer);
  $("#fp-grab").addEventListener("click", () => {
    if (fpDismissDragged) {            // 刚拖过: 抬手补发的 click 不算
      fpDismissDragged = false;
      return;
    }
    closeFullPlayer("morph");         // 1.8.63 水滴收回气泡
  });
  bindDismissDrag($("#fp-grab"), true);   // 抓手条: 下拉收起 + 横拖右甩收起
  bindDismissDrag($("#fp-art-wrap"));     // 封面: 下拉收起 (左右划归 3D 舞台)
  initArtStage();   // 1.8.60 3D 封面舞台: 两侧站上一首/下一首, 左右划跟手切歌
  // 1.8.2 整页下拉收起 (用户点名): 没有自带手势/滚动的点都能拖 —— 歌词、
  // 队列自带滚动, 抓手/封面自带拖动, 按钮/滑杆各有点击与拖拽语义, 全让路
  bindDismissDrag($(".fp-sheet"), false, true);
  bindDismissDrag($(".fp-bg"), false, true);
  $("#fp-play").addEventListener("click", playerToggle);
  $("#fp-next").addEventListener("click", playerNext);
  $("#fp-prev").addEventListener("click", playerPrevious);
  // 1.8.89 三态循环一键 (用户点名): 列表循环 → 单曲循环 → 随机循环,
  // 切一下气泡报一下当前态; 待播列表头的两枚控制键退役 (列表只看不听令)
  $("#fp-mode-btn").addEventListener("click", () => {
    if (!playQueue) return;
    const mode = queueCyclePlayMode(playQueue);
    updatePlayModeButton();
    if (queueViewOpen) renderQueueView();   // 没开着不重铺 (翻开现铺, 1.8.61)
    savePlayerState();
    toast(mode === "all" ? "列表循环" : mode === "one" ? "单曲循环" : "随机循环");
  });
  $("#fp-lyrics-btn").addEventListener("click", toggleLyricsView);
  $("#fp-queue-btn").addEventListener("click", toggleQueueView);
  $("#lyrics-resume").addEventListener("click", resumeLyricsFollow);

  // 手动滑歌词 (程序定位引发的 scroll 不算) → 暂停跟唱 + 出"回到当前句";
  // 手指按下的那一刻先撤掉滚动动画, 之后的位置全算用户的。
  // 浏览期间整页取消模糊 (凑近了看), 静置或点行跳播后恢复距离模糊。
  $("#fp-lyrics").addEventListener("pointerdown", cancelLyricsScroll);
  $("#fp-lyrics").addEventListener("scroll", () => {
    if (lyricsAutoScrolling) return;
    // 1.8.53 修「开播放页在封面页上见着 回到当前句」: 关页途中歌词的
    // 惯性滚动还会补发几拍 scroll, 这时点亮浏览态会残留到下次开页
    if (!playerOpen || !lyricsViewOpen) return;
    if (!$("#fp-lyrics").classList.contains("static")) {   // 无时间轴: 没跟唱可暂停
      lyricsFollowPaused = true;
      $("#fp-lyrics").classList.add("browsing");
      $("#lyrics-resume").hidden = false;
    }
    lyricsLastScrollAt = Date.now();
  });

  $("#queue-list").addEventListener("click", (event) => {
    const row = event.target.closest("[data-queue-track-id]");
    if (!row || !playQueue) return;
    const track = queueJump(playQueue, Number(row.dataset.queueTrackId));
    if (track && track.playable) {
      loadTrack(track, true);
    } else {
      toast("这首浏览器播不了");
    }
  });
  bindQueueDrag();   // 队列左滑删除不在这绑 (1.8.29): 它用的 bindSwipeDelete
                     // 在浏览模块, 加载在播放器组之后 —— 开局跑会掐死后面
                     // 一串接线; 队列视图第一次打开时才绑 (queue-view 里)

  $("#fp-lyrics").addEventListener("click", (event) => {
    const line = event.target.closest(".lyrics-line");
    if (!line) return;
    const time = Number(line.dataset.time);
    if (time >= 0) audioElement().currentTime = time;
    // 点行跳播 = 在新位置落座: 退出浏览态恢复模糊;
    // 不抢着滚, 紧跟的 timeupdate 会把新当前句滚居中
    resumeLyricsFollow(false);
  });

  // 滑杆命中层: iOS 的 range 输入点轨道不跳值、7px 滑钮抓不住 (音量条整个
  // 点不动)。输入框包一层透明垫子自己算比例 —— 按下即跳、拖动跟手;
  // 值写回 input 再补发 input/change, 既有 --fill/seek/存档逻辑全复用。
  bindPlayerAudioEvents(audio);
}
