// music-home-view — My Music 主页视图: 三段 (最近播放音乐/最新添加专辑/
// 最近播放列表), 各 10 个, 段头带 › 查看全部 (1.8.24 用户点名改版)。
// 拆自 music.js (结构化重构, 经典脚本按 music.html 里的顺序加载, 跨模块引用走全局)。
"use strict";
/* global $, albumCardHTML, bindSwipeDelete, bindTrackLists, fetchJSON, listPlaceholderHTML, navigate,
          pageState, playlistRowHTML, toast, trackArtHTML, trackRowHTML */
/* exported renderHomeView */

// ------------------------------------------------------------ 主页

// 每段条数 (用户点的 10 个; 看全量走段头的 › 进对应页)
const HOME_SECTION_COUNT = 10;

/** 段头: 标题 + 右缘 ›, 整条可点 (data-see-all → 查看全部的目标页)。 */
function sectionHeadHTML(title, target) {
  return `<button class="section-head" data-see-all="${target}">
    <span>${title}</span><span class="chev">›</span></button>`;
}

// 段头 › 查看全部: 绑在 document (主页重铺不累加 —— #root-view 是常驻
// 元素, 绑它身上每次 renderHomeView 都会再挂一份, 点一下进两层);
// data-see-all 只有主页段头在用, 别的视图点了没影响。
document.addEventListener("click", (event) => {
  const head = event.target.closest("[data-see-all]");
  if (head) navigate(head.dataset.seeAll);
});

function renderHomeView() {
  $("#root-view").innerHTML = `
    ${sectionHeadHTML("最近播放音乐", "recent")}
    <div id="home-recent">${listPlaceholderHTML("加载中…")}</div>
    ${sectionHeadHTML("最新添加专辑", "albums")}
    <div id="home-albums" class="album-grid">${listPlaceholderHTML("加载中…")}</div>
    ${sectionHeadHTML("最近播放列表", "playlists")}
    <div id="home-playlists">${listPlaceholderHTML("加载中…")}</div>`;
  // 事件绑在容器上 (内容是异步重铺的, 绑内容会重复累加)
  $("#home-playlists").addEventListener("click", (event) => {
    const row = event.target.closest("[data-playlist-id]");
    if (row) navigate(`playlist/${row.dataset.playlistId}`);
  });
  // 列表行左滑露出删除: 删掉后就地抽行, 不整页重铺
  bindSwipeDelete($("#home-playlists"), async (wrap) => {
    const playlistId = Number(wrap.dataset.swipePlaylist);
    try {
      await fetchJSON(`/music/api/playlists/${playlistId}`, { method: "DELETE" });
      wrap.remove();
      toast("已删除");
    } catch (error) {
      toast(`没删掉: ${error.message}`);
    }
  });
  bindTrackLists($("#home-recent"), () => pageState.homeRecent || []);
  loadHomeRecent();
  loadHomeAlbums();
  loadHomePlaylists();
}

async function loadHomeRecent() {
  let tracks = null;
  try {
    tracks = (await fetchJSON(
      `/music/api/plays/recent?limit=${HOME_SECTION_COUNT}`)).tracks;
  } catch (_error) { /* 下面占位文案兜底 */ }
  const element = $("#home-recent");
  if (!element || !element.isConnected) return;   // 已被换掉 (二级层下重铺也一样保护)
  pageState.homeRecent = tracks || [];
  element.innerHTML = pageState.homeRecent.length
    ? pageState.homeRecent.map(
        (track) => trackRowHTML(track, trackArtHTML(track), "art")).join("")
    : listPlaceholderHTML("听过歌就会出现在这里, 各账号各记各的");
}

async function loadHomeAlbums() {
  let albums = null;
  try {
    albums = (await fetchJSON(
      `/music/api/albums?sort=added&limit=${HOME_SECTION_COUNT}`)).albums;
  } catch (_error) { /* 下面占位文案兜底 */ }
  const element = $("#home-albums");
  if (!element || !element.isConnected) return;
  element.innerHTML = albums && albums.length
    ? albums.map(albumCardHTML).join("")
    : listPlaceholderHTML("曲库扫完, 专辑就摆在这了");
}

async function loadHomePlaylists() {
  let playlists = null;
  try {
    playlists = (await fetchJSON(
      `/music/api/playlists/recent?limit=${HOME_SECTION_COUNT}`)).playlists;
  } catch (_error) { /* 下面占位文案兜底 */ }
  const element = $("#home-playlists");
  if (!element || !element.isConnected) return;
  element.innerHTML = playlists && playlists.length
    ? playlists.map(playlistRowHTML).join("")
    : listPlaceholderHTML("还没有播放列表; 长按任意歌曲就能新建一个");
}
