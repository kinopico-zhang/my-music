// music-recent-pane — My Music 最近播放页 (菜单「最近播放」进来的推入层)。
// 1.8.1 新增: 按最近一次播放时刻倒序整页铺开 (LRU, 最多 100 首)。
// 1.8.31 用户点名「最近播放不用显示播放次数」: 行右缘回到时长
// (词标/下载标照旧, 次数只在播放排行页出)。
"use strict";
/* global $, bindTrackLists, fetchJSON, listPlaceholderHTML, pageState,
          trackArtHTML, trackRowHTML */
/* exported renderRecentPane */

// ------------------------------------------------------------ 最近播放页

function renderRecentPane(target) {
  target.innerHTML = `
    <div class="pane-title">最近播放</div>
    <div id="pane-recent">${listPlaceholderHTML("加载中…")}</div>`;
  // 事件绑在容器上 (内容是异步重铺的, 绑内容会重复累加)
  bindTrackLists($("#pane-recent"), () => pageState.recentPane || []);
  loadRecentPane();
}

async function loadRecentPane() {
  let tracks = null;
  try {
    tracks = (await fetchJSON("/music/api/plays/recent?limit=100")).tracks;
  } catch (_error) { /* 下面占位文案兜底 */ }
  const element = $("#pane-recent");
  if (!element || !element.isConnected) return;   // 层已被换掉/收走
  pageState.recentPane = tracks || [];            // 点行开播的队列语境
  element.innerHTML = pageState.recentPane.length
    ? pageState.recentPane.map(
        (track) => trackRowHTML(track, trackArtHTML(track), "art")).join("")
    : listPlaceholderHTML("听过歌就会出现在这里, 各账号各记各的");
}
