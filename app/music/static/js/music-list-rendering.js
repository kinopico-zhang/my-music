// music-list-rendering — My Music 公共渲染件: 专辑卡/曲目行/艺人行/播放列表行/占位, 列表容器绑定, 播放指示同步。
// 拆自 music.js (结构化重构: 代码逐字节未动, 经典脚本按 music.html 里的顺序加载, 跨模块引用走全局)。
"use strict";
/* global ICON_BARS, ICON_LYRICS, PLACEHOLDER_ARTWORK, albumArtworkURL, artistArtworkURL,
          describeDuration, downloadMarkHTML, downloadTrackFromUI, downloads,
          downloadsEnabled, escapeHTML, formatPlaybackTime, playerStart, playlistCoverURL,
          toast, trackArtworkURL, updatePlayButtons */
/* exported albumCardHTML, artistRowHTML, bindTrackLists, listPlaceholderHTML,
            playlistCardHTML, playlistRowHTML, refreshPlaylistCoverIcons,
            refreshPlaylistName, rowForTrackMenu, syncPlayerIndicators,
            trackArtHTML, trackListBindings, trackRowHTML */

// ------------------------------------------------------------ 公共渲染件

/** 专辑卡 (网格): 封面 + 标题 + 艺人。 */
function albumCardHTML(album) {
  return `
    <button class="album-card" data-album-id="${album.album_id}">
      <span class="art-wrap">
        <img loading="lazy" decoding="async" alt=""
             src="${albumArtworkURL(album)}"
             onerror="this.onerror=null;this.src='${PLACEHOLDER_ARTWORK}'">
        ${album.has_artwork ? "" : '<span class="art-note">♪</span>'}
      </span>
      <b>${escapeHTML(album.title)}</b>
      <small>${escapeHTML(album.artist_name)}</small>
    </button>`;
}

/** 曲目行: 序号/小封面 + 动条 (播放中顶掉序号) + 标题 (不可播标) + 艺人
    + 词标 (❝, 行右侧与下载标平齐) + 下载标 + 时长。下载标不是真按钮
    (行本身是 button, 嵌套非法)。
    leadClass="art" 时引导位放宽 (44px 封面图替序号, 播放列表用)。
    trailingHTML 可顶掉时长位 (1.8.31 播放排行页: 换成区间内播放次数)。
    plain=true 时下载标也不出 (1.8.31 用户点名「排行上只需要显示播放
    次数」—— 时长已被 trailingHTML 顶掉, 下载标一并收走)。 */
function trackRowHTML(track, leadHTML, leadClass, trailingHTML, plain) {
  return `
    <button class="track-row${track.playable ? "" : " disabled"}"
            data-track-row="${track.track_id}" data-track-id="${track.track_id}">
      <span class="t-lead${leadClass ? ` ${leadClass}` : ""}">${leadHTML || ""}${ICON_BARS}</span>
      <span class="t-main">
        <span class="t-title"><span class="t-title-text">${escapeHTML(track.title)}</span>
          ${track.playable ? "" : `<i class="t-format">${escapeHTML(track.file_format)}</i>`}
        </span>
        <small>${escapeHTML(track.artist)}</small>
      </span>
      ${track.lyrics_available ? `<i class="t-lyric">${ICON_LYRICS}</i>` : ""}
      ${!plain && downloadsEnabled ? `
      <span class="t-dl${downloads.isDownloaded(track.track_id) ? " done" : ""}"
            data-download-track="${track.track_id}" role="button" tabindex="-1"
            aria-label="下载">${downloadMarkHTML(track.track_id)}</span>` : ""}
      <span class="t-time">${trailingHTML ?? formatPlaybackTime(track.duration_seconds)}</span>
    </button>`;
}

/** 曲目自己的小封面 (元数据内嵌图; 没有的给音符占位块)。
    接口万一抽不出图 (404) 也退回占位块, 别给用户看裂图。 */
function trackArtHTML(track) {
  return track.has_artwork
    ? `<img class="t-art" loading="lazy" decoding="async" alt=""
            src="${trackArtworkURL(track)}"
            onerror="this.replaceWith(Object.assign(document.createElement('span'),{className:'t-art',textContent:'♪'}))">`
    : '<span class="t-art">♪</span>';
}

function artistRowHTML(artist) {
  return `
    <button class="artist-row" data-artist-id="${artist.artist_id}">
      <img loading="lazy" decoding="async" alt="" class="poster"
           src="${artistArtworkURL(artist)}"
           onerror="this.onerror=null;this.src='${PLACEHOLDER_ARTWORK}'">
      <span class="a-main"><b>${escapeHTML(artist.name)}</b>
        <small>${artist.album_count} 张专辑 · ${artist.track_count} 首</small></span>
      <span class="chev">›</span>
    </button>`;
}

/** 播放列表行引导位: 自定义封面 / 渐变音符块。 */
function playlistRowIconHTML(playlist) {
  const cover = playlistCoverURL(playlist);
  return cover
    ? `<img class="pl-icon art" loading="lazy" decoding="async" alt="" src="${cover}">`
    : '<span class="pl-icon">♫</span>';
}

/** 播放列表卡封面方块的内容 (裂图退音符块, 与行同一份素材)。 */
function playlistCardArtHTML(playlist) {
  const cover = playlistCoverURL(playlist);
  return cover
    ? `<img loading="lazy" decoding="async" alt="" src="${cover}"
         onerror="this.replaceWith(Object.assign(document.createElement('span'),{className:'pl-icon',textContent:'♫'}))">`
    : '<span class="pl-icon">♫</span>';
}

/** 换/撤封面后把底下各页这张列表的封面就地换新 (列表页行 + 主页卡):
    底下的层收层回去不重铺 (1.8.80 的老坑), 行里的旧 ?v= 地址不换掉,
    返回看到的就是旧图 (1.8.99 用户实报)。只换封面那一块 —— 滚动位置
    和左滑状态都原地保住。 */
function refreshPlaylistCoverIcons(playlist) {
  document.querySelectorAll(
    `.playlist-row[data-playlist-id="${playlist.playlist_id}"] > .pl-icon`)
    .forEach((icon) => { icon.outerHTML = playlistRowIconHTML(playlist); });
  document.querySelectorAll(
    `.playlist-card[data-playlist-id="${playlist.playlist_id}"] .art-wrap`)
    .forEach((wrap) => { wrap.innerHTML = playlistCardArtHTML(playlist); });
}

/** 改名后把底下各页这张列表的名字就地换新 (列表页行 + 主页卡): 底下的
    层收层回去不重铺 (1.8.80 的老坑), 名字不换掉, 返回看到的就是旧名
    (1.8.123 用户实报; 封面 1.8.99 修过同款)。只动名字那几个字 ——
    滚动位置和左滑状态都原地保住。 */
function refreshPlaylistName(playlist) {
  document.querySelectorAll(
    `.playlist-row[data-playlist-id="${playlist.playlist_id}"] .a-main b`)
    .forEach((name) => { name.textContent = playlist.name; });
  document.querySelectorAll(
    `.playlist-card[data-playlist-id="${playlist.playlist_id}"] > b`)
    .forEach((name) => { name.textContent = playlist.name; });
}

/** 播放列表行: 自定义封面 (传过) / 渐变音符块 + 名字 + 规模。
    外面套一层左滑删除的壳 (播放列表页的行在用, 整列左滑删除)。 */
function playlistRowHTML(playlist) {
  return `
    <div class="swipe-wrap" data-swipe-playlist="${playlist.playlist_id}">
      <button class="playlist-row" data-playlist-id="${playlist.playlist_id}">
        ${playlistRowIconHTML(playlist)}
        <span class="a-main"><b>${escapeHTML(playlist.name)}</b>
          <small>${describeDuration(playlist.duration_seconds, playlist.track_count)}</small></span>
        <span class="chev">›</span>
      </button>
      <button class="swipe-del" aria-label="删除列表">删除</button>
    </div>`;
}

/** 播放列表卡 (1.8.28 主页段与专辑卡同排版, 用户点名): 复用 .album-card
    的整套卡排版, 封面方块里自定义封面 / 渐变音符块 + 名字 + 规模副题。
    卡片不套壳 —— 整列删除走播放列表页的列表行。 */
function playlistCardHTML(playlist) {
  return `
    <button class="album-card playlist-card" data-playlist-id="${playlist.playlist_id}">
      <span class="art-wrap">${playlistCardArtHTML(playlist)}</span>
      <b>${escapeHTML(playlist.name)}</b>
      <small>${describeDuration(playlist.duration_seconds, playlist.track_count)}</small>
    </button>`;
}

function listPlaceholderHTML(message) {
  return `<div class="list-empty">${message}</div>`;
}

/** 曲目点击 → 开播 (队列 = 所在列表; 不可播提示; 下载标点按 = 下载)。 */
const trackListBindings = new WeakMap();  // 容器 → tracksOf (长按菜单按所在列表开播)
let rowForTrackMenu = null;               // 菜单正对着的那行 (播放要它的列表语境)

function bindTrackLists(container, tracksOf) {
  trackListBindings.set(container, tracksOf);   // 长按菜单按所在列表开播
  container.addEventListener("click", (event) => {
    const mark = event.target.closest("[data-download-track]");
    if (mark) {                          // 下载标优先于整行播放
      const trackId = Number(mark.dataset.downloadTrack);
      const track = (tracksOf() || []).find(
        (item) => item.track_id === trackId);
      if (track && track.playable) downloadTrackFromUI(track);
      return;
    }
    const row = event.target.closest("[data-track-row]");
    if (!row) return;
    const trackId = Number(row.dataset.trackId);
    const tracks = tracksOf();
    const index = tracks.findIndex((track) => track.track_id === trackId);
    if (index < 0) return;
    const track = tracks[index];
    if (!track.playable) {
      toast(`浏览器播不了 ${String(track.file_format).toUpperCase()}`);
      return;
    }
    playerStart(tracks, index);
  });
}

function syncPlayerIndicators() {
  updatePlayButtons();       // 播放器模块的行高亮同步 (换视图后行是新 DOM)
}

