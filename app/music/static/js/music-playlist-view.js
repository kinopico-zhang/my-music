// music-playlist-view — My Music 播放列表详情页: 曲目管理/加歌/自定义封面上传/
// 改名 (1.8.17) + 曲目拖拽换序 (拖拽住在 music-playlist-drag)。
// 1.8.80 修删列表后主页还留着它: 原来先 navigate("home") 再补
// renderRootView —— navigate 把层栈收干净了, 后头那个 if (pushStack.length)
// 永远不成立, 主页没重铺过 (陈货直等下次整页重铺); 换成趁层还盖着先铺。
// 拆自 music.js (结构化重构, 经典脚本按 music.html 里的顺序加载, 跨模块引用走全局)。
"use strict";
/* global $, ICON_ACTION_IMAGE, ICON_ACTION_PLAY, ICON_ACTION_SHARE, ICON_ACTION_SHUFFLE,
          ICON_ACTION_TRASH, ICON_DOWNLOAD, bindCoverPress, bindHeroCollapse,
          bindPlaylistDrag, bindSwipeDelete, bindTrackLists,
          coverUploadPlaylistId: writable,
          describeDuration, downloadAllFromUI, downloadsEnabled, escapeHTML,
          fetchJSON, heroBarHTML, listPlaceholderHTML, navigate, playerStart,
          playlistCoverURL, pushPaneTarget, refreshPlaylistCoverIcons,
          renderRootView,
          sharePlaylist, syncPlayerIndicators, toast, trackArtHTML, trackRowHTML,
          wireHeroBarActions */
/* exported coverUploadPlaylistId, renderPlaylistView, uploadPlaylistCover */

// ------------------------------------------------------------ 播放列表页

async function renderPlaylistView(playlistId, target) {
  target = target || pushPaneTarget();    // 二级层薄层; 兜底 #main (无层时)
  target.innerHTML = listPlaceholderHTML("加载中…");
  let page = null;
  try {
    page = await fetchJSON(`/music/api/playlists/${playlistId}`);
  } catch (error) {
    target.innerHTML = listPlaceholderHTML(`加载失败: ${error.message}`);
    return;
  }
  const playlist = page.playlist;
  const playable = page.tracks.filter((track) => track.playable);
  const cover = playlistCoverURL(playlist);
  const coverLabel = cover ? "换封面" : "设置封面";
  target.innerHTML = `
    <div class="hero-head">
      <div class="album-hero">
        <button class="pl-cover-btn" id="cover-tap" aria-label="${coverLabel}"
                title="${coverLabel}">
          ${cover
            ? `<img class="pl-icon big art" alt="" src="${cover}">`
            : '<div class="pl-icon big">♫</div>'}
          <span class="cover-hint" aria-hidden="true">${ICON_ACTION_IMAGE}</span>
        </button>
        <div class="hero-txt">
          <h2 class="pl-name" title="点按改名">${escapeHTML(playlist.name)}</h2>
          <div class="hero-sub"><small class="hero-meta">${escapeHTML(describeDuration(
            playlist.duration_seconds, playlist.track_count))}</small></div>
        </div>
      </div>
      <div class="action-row">
        <button class="action icon primary" id="playlist-play" title="播放"
                aria-label="播放" ${playable.length ? "" : "disabled"}>
          ${ICON_ACTION_PLAY}</button>
        <button class="action icon" id="playlist-shuffle" title="随机播放"
                aria-label="随机播放" ${playable.length ? "" : "disabled"}>
          ${ICON_ACTION_SHUFFLE}</button>
        ${downloadsEnabled ? `
        <button class="action icon" id="playlist-download" data-dl-all title="下载全部"
                aria-label="下载全部" ${playable.length ? "" : "disabled"}>
          ${ICON_DOWNLOAD}</button>` : ""}
        <button class="action icon" id="playlist-share" title="分享"
                aria-label="分享">${ICON_ACTION_SHARE}</button>
        <button class="action icon" id="playlist-delete" title="删除列表"
                aria-label="删除列表">${ICON_ACTION_TRASH}</button>
      </div>
      ${heroBarHTML({ play: !!playable.length, shuffle: !!playable.length,
                      ...(downloadsEnabled ? { download: !!playable.length } : {}),
                      share: true, delete: true })}
    </div>
    <div class="track-list" id="playlist-tracks">
      ${page.tracks.map((track) => `
        <div class="swipe-wrap" data-swipe-track="${track.track_id}">
          ${trackRowHTML(track, trackArtHTML(track), "art")}
          <button class="swipe-del" aria-label="从列表移除">删除</button>
        </div>`).join("")}
    </div>`;
  const playList = () => playerStart(page.tracks, page.tracks.indexOf(playable[0]));
  const shuffleList = () => playerStart(page.tracks, page.tracks.indexOf(playable[0]), true);
  target.querySelector("#playlist-play").addEventListener("click", playList);
  target.querySelector("#playlist-shuffle").addEventListener("click", shuffleList);
  const playlistDownload = target.querySelector("#playlist-download");
  if (playlistDownload) {
    playlistDownload.addEventListener("click", () => downloadAllFromUI(page.tracks));
  }
  const shareThisList = () => sharePlaylist(playlist);
  target.querySelector("#playlist-share").addEventListener("click", shareThisList);
  const deleteThisList = async () => {
    if (!window.confirm(`删除播放列表「${playlist.name}」?`)) return;
    try {
      await fetchJSON(`/music/api/playlists/${playlistId}`, { method: "DELETE" });
      toast("已删除");
      // 一级页就在层底下, 趁层还盖着先整页重铺 (看不见重铺闪动), 再收层
      // 滑走 —— 露出来的就是没有它的主页。次序不能反: 先 navigate 层栈
      // 收干净, 再想补铺就没层可判断了 (1.8.80 修的是这个死闸)。
      renderRootView("home");
      navigate("home");
    } catch (error) {
      toast(`没删掉: ${error.message}`);
    }
  };
  target.querySelector("#playlist-delete").addEventListener("click", deleteThisList);
  // 顶栏动作条 (1.8.45): 收缩后 播放 + … 两颗, … 里就是这四颗
  wireHeroBarActions(target, {
    play: playList, shuffle: shuffleList,
    download: () => downloadAllFromUI(page.tracks), share: shareThisList,
    delete: deleteThisList,
  });
  bindCoverPress(playlistId, playlist.name, !!cover);
  // 改名 (1.8.17 用户点名「允许编辑播放列表的标题」): 点标题 prompt 落定
  // (与删列表的 confirm 同款原生对话, 不另造弹层)
  target.querySelector("h2.pl-name").addEventListener("click", async () => {
    const name = window.prompt("新的列表名", playlist.name);
    if (name === null) return;                     // 取消不算失败
    try {
      const updated = await fetchJSON(`/music/api/playlists/${playlistId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      playlist.name = updated.name;
      target.querySelector("h2.pl-name").textContent = updated.name;
      toast("列表名已更新");
    } catch (error) {
      toast(`没改上: ${error.message}`);
    }
  });
  bindTrackLists(target.querySelector("#playlist-tracks"), () => page.tracks);
  // 曲目行左滑露出删除: 移出列表后就地抽掉那行 (不整页重铺, 滚动位置保住),
  // 头上的 规模/时长 文案顺手重算。
  // 1.8.110 二次确认 (用户点名「所有的删除都要二次确认」), 反悔行自动收起
  bindSwipeDelete(target.querySelector("#playlist-tracks"), async (wrap) => {
    const trackId = Number(wrap.dataset.swipeTrack);
    const track = page.tracks.find((item) => item.track_id === trackId);
    const title = track ? track.title : "这首歌";
    if (!window.confirm(`从「${playlist.name}」移除「${title}」?`)) return;
    try {
      await fetchJSON(`/music/api/playlists/${playlistId}/tracks/${trackId}`,
                      { method: "DELETE" });
      wrap.remove();
      page.tracks = page.tracks.filter((track) => track.track_id !== trackId);
      const heroSmall = target.querySelector(".hero-txt small");
      if (heroSmall) {
        heroSmall.textContent = describeDuration(
          page.tracks.reduce((sum, track) => sum + (track.duration_seconds || 0), 0),
          page.tracks.length);
      }
      toast("已从列表移除");
    } catch (error) {
      toast(`没移除掉: ${error.message}`);
    }
  });
  // 拖拽换序 (1.8.17 用户点名「允许调整列表歌曲的顺序」): 把手拖完先就地
  // 挪 DOM (滚动位置不动), 再把全量新顺序 PUT 上去; 没存上重拉详情对齐服务端
  bindPlaylistDrag(target.querySelector("#playlist-tracks"), async (from, to) => {
    const [moved] = page.tracks.splice(from, 1);
    page.tracks.splice(to, 0, moved);
    try {
      await fetchJSON(`/music/api/playlists/${playlistId}/order`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ track_ids: page.tracks.map((track) => track.track_id) }),
      });
    } catch (error) {
      toast(`顺序没存上: ${error.message}`);
      renderPlaylistView(playlistId);
    }
  });
  coverUploadPlaylistId = playlistId;
  bindHeroCollapse(target);              // 1.8.34 封面收缩顶栏 (上划钉成顶栏)
  syncPlayerIndicators();
}

/** 隐藏文件选择器选中图片 → 直接把字节 PUT 上去 (原图直存, 不压缩)。 */
async function uploadPlaylistCover(playlistId) {
  const input = $("#cover-file");
  const file = input.files && input.files[0];
  input.value = "";                     // 同一张图重选也要触发 change
  if (!file) return;
  if (file.size > 10 * 1024 * 1024) {
    toast("封面太大了 (上限 10 MB)");
    return;
  }
  try {
    const updated = await fetchJSON(
      `/music/api/playlists/${playlistId}/cover`, {
        method: "PUT",
        headers: { "Content-Type": file.type || "application/octet-stream" },
        body: file,
      });
    toast("封面已更新");
    // 响应里是新版本号: 底下列表页/主页的封面就地换新, 返回看到的才是新图
    refreshPlaylistCoverIcons(updated);
    renderPlaylistView(playlistId);
  } catch (error) {
    toast(`封面没传上去: ${error.message}`);
  }
}

