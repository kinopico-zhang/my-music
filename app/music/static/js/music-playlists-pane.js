// music-playlists-pane — My Music 播放列表独立页 (菜单「播放列表」进来的推入层)。
// 1.8.0 资料库拆独立顶级视图: 播放列表从主页一段升格成整页,
// 行内容/交互与主页列表段同款 (点行进详情, 左滑删整列)。
// 1.8.80 左滑删完顺手把主页列表段那张卡也抽走 (removeHomePlaylistCard):
// 主页层底下躺着不重铺, 不抽它回主页还看到已删的 (用户实报)。
"use strict";
/* global $, bindSwipeDelete, fetchJSON, listPlaceholderHTML, navigate,
          playlistRowHTML, removeHomePlaylistCard, toast */
/* exported renderPlaylistsPane */

// ------------------------------------------------------------ 播放列表页

function renderPlaylistsPane(target) {
  target.innerHTML = `
    <div class="pane-title">播放列表</div>
    <div id="pane-playlists">${listPlaceholderHTML("加载中…")}</div>`;
  const list = $("#pane-playlists");
  // 事件绑在容器上 (内容是异步重铺的, 绑内容会重复累加)
  list.addEventListener("click", (event) => {
    const row = event.target.closest("[data-playlist-id]");
    if (row) navigate(`playlist/${row.dataset.playlistId}`);
  });
  // 列表行左滑露出删除: 删掉后就地抽行, 不整页重铺 (与主页同款)。
  // 1.8.110 二次确认 (用户点名「删除歌单应该给二次确认」): 与详情页删列表
  // 同一句话、同款原生 confirm; 反悔了行自动收起 (swipe 模块统一收尾)
  bindSwipeDelete(list, async (wrap) => {
    const playlistId = Number(wrap.dataset.swipePlaylist);
    const nameTag = wrap.querySelector(".a-main b");
    const name = nameTag ? nameTag.textContent : "这个列表";
    if (!window.confirm(`删除播放列表「${name}」?`)) return;
    try {
      await fetchJSON(`/music/api/playlists/${playlistId}`, { method: "DELETE" });
      wrap.remove();
      removeHomePlaylistCard(playlistId);   // 主页层底下那张同款卡一起抽掉
      toast("已删除");
    } catch (error) {
      toast(`没删掉: ${error.message}`);
    }
  });
  loadPlaylistsPane();
}

async function loadPlaylistsPane() {
  let playlists = null;
  try {
    playlists = (await fetchJSON("/music/api/playlists")).playlists;
  } catch (_error) { /* 下面占位文案兜底 */ }
  const element = $("#pane-playlists");
  if (!element || !element.isConnected) return;   // 层已被换掉/收走
  element.innerHTML = playlists && playlists.length
    ? playlists.map(playlistRowHTML).join("")
    : listPlaceholderHTML("还没有播放列表; 长按任意歌曲就能新建一个");
}
