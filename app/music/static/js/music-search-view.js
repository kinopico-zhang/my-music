// music-search-view — My Music 搜索页 (1.8.17 换思路, 用户点名): 页顶一条
// sticky —— 编辑态放搜索框 (钉屏幕最上, 系统磨砂带底下, 键盘再高也盖不住
// 顶端), 回车落定后查询词升作页标题「搜索：xxx」, 点标题回来改 (全选原词,
// 直接打字即替换)。有查询时结果分四子页左右滑切换 (骨架/页签/铺页在
// music-search-pages.js)。搜索还是边打边搜 (防抖 300ms), 回车立刻落定。
// 页壳 (.search-shell) 自己是滚动器 + #search-body 撑 --kb-full (1.8.15)
// 与文档解锁 (1.8.16) 原样保留 —— 键盘让位的滚落在页壳里, 黑带那一页
// 翻过去了, 这两块别再动 (用户点名「不要重蹈覆辙」)。
// 1.8.6 起所有元素查找都收在本层 target 里: 旧搜索层滑出还挂着 DOM 的
// 420ms 内, $() 全局找会抓到旧层的元素 (重进搜索输入框失灵的元凶)。
"use strict";
/* global bindSearchTabs, bindTrackLists, buildSearchPages, escapeHTML, fetchJSON,
          listPlaceholderHTML, navigate, openFullPlayer, openLyricsView, pageState,
          playerStart, renderSearchResults, toast */
/* exported renderSearchView */

// ------------------------------------------------------------ 搜索页

function renderSearchView(target) {
  target.innerHTML = `
    <div class="search-shell">
      <div class="search-head">
        <div class="search-box">
          <svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true"><circle cx="7" cy="7" r="5" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="m11 11 3.4 3.4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
          <input id="search-input" type="search" enterkeyhint="search" autocomplete="off"
                 placeholder="歌曲、专辑、艺人、歌词 (拼音简繁都行)" maxlength="100"
                 value="${escapeHTML(pageState.searchQuery)}">
          <button id="search-clear" hidden aria-label="清空">✕</button>
        </div>
        <button type="button" class="search-title">搜索</button>
        <div class="search-tabs" id="search-tabs">
          <button type="button" class="on" data-search-tab="tracks">歌曲<small></small></button>
          <button type="button" data-search-tab="artists">艺人<small></small></button>
          <button type="button" data-search-tab="albums">专辑<small></small></button>
          <button type="button" data-search-tab="lyrics">歌词<small></small></button>
        </div>
      </div>
      <div id="search-body"></div>
    </div>`;
  const shell = target.querySelector(".search-shell");
  const input = target.querySelector("#search-input");
  const clearButton = target.querySelector("#search-clear");
  const title = target.querySelector(".search-title");
  // 提交后的标题: 查询词升作页标题 (空查询就是光杆「搜索」)
  const syncTitle = () => {
    title.textContent = pageState.searchQuery
      ? `搜索：${pageState.searchQuery}` : "搜索";
  };
  syncTitle();
  // 空查询开局即编辑态 (1.8.18 修「点放大镜进来没有输入框」): 框默认藏着
  // (:not(.editing) display:none), 而藏着的框恰恰聚不上焦 —— 焦点进不去,
  // .editing 就永远等不来。先亮框, 船坞键的 focus 才落得下去
  if (!pageState.searchQuery) shell.classList.add("editing");
  // 编辑态 = 焦点在框里 (键盘在): 框钉页首; 一失焦 (回车/点别处/切页签)
  // 就算落定 —— 框撤下, 查询词顶上标题位
  input.addEventListener("focus", () => shell.classList.add("editing"));
  input.addEventListener("blur", () => {
    shell.classList.remove("editing");
    syncTitle();
    shell.scrollTo(0, 0);   // 让位滚过页壳的话归位, 标题底下别压着结果
  });
  title.addEventListener("click", () => {
    shell.classList.add("editing");   // 框先亮出来才聚焦得上 (隐藏的框 focus 不进)
    input.focus(); input.select();
  });
  let debounceTimer = 0;
  input.addEventListener("input", () => {
    pageState.searchQuery = input.value.trim();
    clearButton.hidden = !input.value;
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => runSearch(target), 300);
  });
  // 回车 (键盘上的「搜索」键) = 落定: 撤掉防抖立刻搜 + 收键盘, 查询词升作
  // 页标题 —— 边打边搜的尾款别丢 (打完立刻回车的那 300ms 窗口)
  input.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    event.preventDefault();
    clearTimeout(debounceTimer);
    runSearch(target);
    input.blur();
  });
  clearButton.addEventListener("click", () => {
    input.value = "";
    pageState.searchQuery = "";
    clearButton.hidden = true;
    runSearch(target);
  });
  bindSearchBody(target);
  bindSearchTabs(target);
  runSearch(target);
}

/** 结果区事件 (专辑/艺人跳转 + 行开播 + 歌词命中连播): 绑在容器上 ——
    容器跨查询常驻, 绑内容会重复累加。 */
function bindSearchBody(target) {
  const body = target.querySelector("#search-body");
  body.addEventListener("click", (event) => {
    const albumCard = event.target.closest("[data-album-id]");
    if (albumCard) { navigate(`album/${albumCard.dataset.albumId}`); return; }
    const artistRow = event.target.closest("[data-artist-id]");
    if (artistRow) { navigate(`artist/${artistRow.dataset.artistId}`); return; }
  });
  bindTrackLists(body, () => {
    const results = pageState.searchResults;
    return results ? results.tracks : [];
  });
  body.addEventListener("click", (event) => {
    const lyricRow = event.target.closest("[data-lyric-track]");
    if (!lyricRow) return;
    const results = pageState.searchResults;
    const track = results && results.lyric_hits.find(
      (hit) => hit.track.track_id === Number(lyricRow.dataset.lyricTrack));
    if (!track || !track.track.playable) {
      toast("这首浏览器播不了");
      return;
    }
    const tracks = results.lyric_hits.map((hit) => hit.track);
    playerStart(tracks, tracks.findIndex((item) => item.track_id === track.track.track_id));
    openFullPlayer();
    openLyricsView();
  });
}

async function runSearch(target) {
  const body = target.querySelector("#search-body");
  if (!body) return;
  const shell = body.parentElement;   // .search-shell: 页签显隐跟着 paged 走
  if (pageState.searchAbort) pageState.searchAbort.abort();
  if (!pageState.searchQuery) {
    pageState.searchResults = null;
    body.classList.remove("paged");
    shell.classList.remove("paged");
    body.innerHTML = listPlaceholderHTML(
      "搜歌名、艺人、专辑或一句歌词, 拼音简繁都行");
    return;
  }
  const controller = new AbortController();
  pageState.searchAbort = controller;
  if (!body.classList.contains("paged")) {
    body.classList.add("paged");
    shell.classList.add("paged");
    buildSearchPages(body);        // 四子页骨架 (music-search-pages.js)
  }   // 换词不重建容器: 旧结果留到新结果到, 页序与滚动位置不动
  try {
    const results = await fetchJSON(
      `/music/api/search?q=${encodeURIComponent(pageState.searchQuery)}`,
      { signal: controller.signal });
    if (controller.signal.aborted || !body.isConnected) return;   // 层已收走
    pageState.searchResults = results;
    renderSearchResults(body, results);
  } catch (error) {
    if (error.name === "AbortError") return;
    for (const page of body.children) {
      page.innerHTML = listPlaceholderHTML(`搜索失败: ${error.message}`);
    }
  }
}
