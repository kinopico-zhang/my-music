// music-play-outbox-integration — My Music 播放计数补报队列接线 (1.8.124)。
// 浏览器适配器 (localStorage + fetch) + 实例 + 三个补报时机: 开局、回网
// (online)、回前台 (visibilitychange)。纯队列逻辑在 play-outbox.js
// (适配器注入, node --test 直测); 「playing」出声的记账口是本文件的
// reportPlay (music-player-audio-events 调)。
// 起因: 出声即上报原来是发后不管, 断网/服务重启/5xx 窗口里听过的歌就
// 永久丢了 (排行缺账, 用户问过「你的播放排行, 数据有丢失过吗」) ——
// 报不上先暂存本机, 回网或下次打开按真实播放时刻补报, 排行离线也不缺账。
"use strict";
/* global createPlayOutbox */
/* exported reportPlay */

const playOutbox = createPlayOutbox({
  readQueue: () => {
    try {
      const saved = JSON.parse(localStorage.getItem("music-play-outbox"));
      return Array.isArray(saved) ? saved : [];
    } catch {
      return [];   // 坏数据当空队: 清了重来, 不挡补报
    }
  },
  writeQueue: (entries) => {
    try {
      localStorage.setItem("music-play-outbox", JSON.stringify(entries));
    } catch {
      /* 本机满了就丢, 下次 report 再试落盘 */
    }
  },
  postPlay: (entry) => fetch("/music/api/plays", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(entry),
  }),
  now: () => Math.floor(Date.now() / 1000),
});

/** 「playing」出声记账口: 当场发得出去就出账, 报不上 (断网/5xx/401)
    暂存本机等回网补 —— 永不 reject, 补报从不挡听歌。 */
function reportPlay(trackId) {
  playOutbox.report(trackId);
}

window.addEventListener("online", () => { playOutbox.flush(); });
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible") playOutbox.flush();
});
playOutbox.flush();   // 开局先补一轮: 上次离线听过的那几笔
