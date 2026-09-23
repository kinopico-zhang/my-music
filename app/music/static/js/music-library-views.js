// music-library-views — My Music 资料库独立页 (1.8.0 拆段成页): 专辑/艺人页容器与分页挂载。
// 拆自 music.js (结构化重构), 原资料库页签分段 (segment) 撤掉,
// 专辑/艺人/已下载各自成推入层, 缓存仍按段名住 pageState.lists。
// 1.8.76 已下载面板整块拆去 music-downloads-pane.js (views 顶到 200 行帽
// 按逻辑再切一刀), 本文件只剩专辑/艺人两个资料库页。
"use strict";
/* global appendListPage, listPlaceholderHTML, loadListPage, navigate,
          pageState, playDownloadedRow */
/* exported renderAlbumsPane, renderArtistsPane, resetLibraryLists */

// ------------------------------------------------------------ 资料库独立页

function resetLibraryLists() {
  pageState.lists = {};
}

/** 专辑页: 大标题 + 网格 (缓存有货直接铺, 不够的分页链自己续)。
    1.8.81 两种进法两个序: 主页「最近添加专辑」段头进来按添加时间倒排
    (最新在前), 菜单「所有专辑」进来照旧按标题 —— 缓存也按段名分开住。 */
function renderAlbumsPane(target, variant) {
  const recent = variant === "recent";
  target.innerHTML = `
    <div class="pane-title">${recent ? "最近添加" : "所有专辑"}</div>
    <div class="lib-body"></div>`;
  mountSegmentList(target.querySelector(".lib-body"),
                   recent ? "albums-recent" : "albums");
}

/** 艺人页: 大标题 + 行列表 (与专辑页同一套分页链, 段名不同)。 */
function renderArtistsPane(target) {
  target.innerHTML = `
    <div class="pane-title">所有艺人</div>
    <div class="lib-body"></div>`;
  mountSegmentList(target.querySelector(".lib-body"), "artists");
}

/** 分页列表挂载: 缓存重铺从头渲染, 没缓存先占位再拉首页。 */
function mountSegmentList(body, segment) {
  bindLibraryBody(body);
  body.dataset.segment = segment;   // 段守卫的锚: 在途旧分页回来对不上就丢弃
  const list = pageState.lists[segment];
  if (list && list.items.length) {
    list.renderedCount = 0;         // 缓存重铺从头渲染 (旧值是上次铺到的位置)
    appendListPage(body, segment, list);
    return;
  }
  body.innerHTML = listPlaceholderHTML("加载中…");
  loadListPage(segment, body);
}

/** 资料库页事件 (专辑/艺人跳转 + 已下载点行开播), 绑在各自的页容器上。 */
function bindLibraryBody(body) {
  body.addEventListener("click", (event) => {
    const albumCard = event.target.closest("[data-album-id]");
    if (albumCard) { navigate(`album/${albumCard.dataset.albumId}`); return; }
    const artistRow = event.target.closest("[data-artist-id]");
    if (artistRow) { navigate(`artist/${artistRow.dataset.artistId}`); return; }
    const downloadRow = event.target.closest("[data-dl-row]");
    if (downloadRow) { playDownloadedRow(Number(downloadRow.dataset.dlRow)); }
  });
}
