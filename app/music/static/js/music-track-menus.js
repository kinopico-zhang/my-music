// music-track-menus — My Music 曲目长按菜单: 开合/定位/按列表语境开播。
// 拆自 music.js (结构化重构); 分享链接 1.8.47 拆去 music-share-links.js。
"use strict";
/* global $, downloads, downloadsEnabled, playDownloadedRow, playerStart,
          rowForTrackMenu: writable, toast, trackListBindings */
/* exported closeTrackMenu, menuTrackDirect, openTrackMenu, openTrackMenuForTrack,
            pickerTrack, placeMenuAt, playTrackFromMenu, rowForTrackMenu, trackFromRow */

// ------------------------------------------------------------ 曲目长按菜单
// 任何界面的曲目行 (含「已下载」栏) 长按 500ms / 桌面右键, 弹出菜单:
// 播放 (在所在列表的语境里开播) / 进入艺人主页 / 进入专辑主页 (1.8.2) /
// 下载 (1.8.6) / 添加到播放列表 / 分享。全屏页 ⋯ 也走这个菜单。
let pickerTrack = null;                   // 正在挑列表往里加的曲目
let menuTrackDirect = null;               // 全屏页 ⋯ 直接对着曲目开时用这个

/** 行 → 曲目对象 (沿 DOM 向上找绑过列表的容器; 已下载栏查下载索引)。 */
function trackFromRow(row) {
  const trackId = Number(row.dataset.dlRow || row.dataset.trackRow);
  if (!trackId) return null;
  if (row.classList.contains("dl-row")) {
    return downloads.entries().find((entry) => entry.track_id === trackId)
      || null;
  }
  let scope = row.parentElement;
  while (scope) {
    const tracksOf = trackListBindings.get(scope);
    if (tracksOf) {
      return (tracksOf() || []).find(
        (track) => track.track_id === trackId) || null;
    }
    scope = scope.parentElement;
  }
  return null;
}

/** 菜单里的「播放」: 与点行同一条路径 (队列 = 所在列表)。 */
function playTrackFromMenu(track, row) {
  if (row?.classList.contains("dl-row")) {
    playDownloadedRow(track.track_id);
    return;
  }
  const tracks = row ? tracksOfRow(row) || [] : [];
  const index = tracks.findIndex((item) => item.track_id === track.track_id);
  if (!track.playable) {
    toast(`浏览器播不了 ${String(track.file_format).toUpperCase()}`);
    return;
  }
  if (index >= 0) playerStart(tracks, index);
  else playerStart([track], 0);           // 列表没找着 (视图已换): 单曲播
}

function tracksOfRow(row) {
  let scope = row.parentElement;
  while (scope) {
    const tracksOf = trackListBindings.get(scope);
    if (tracksOf) return tracksOf() || null;
    scope = scope.parentElement;
  }
  return null;
}

function openTrackMenu(row, point) {
  const track = trackFromRow(row);
  if (!track || row.classList.contains("busy")
      || row.classList.contains("disabled")) return;
  rowForTrackMenu = row;
  menuTrackDirect = null;
  $("#menu-track-title").textContent = track.title;
  $("#menu-track-artist").textContent = track.artist;
  $("#track-menu-artist").hidden = !track.artist_id;   // 老下载索引没存艺人号
  $("#track-menu-album").hidden = !track.album_id;     // 同理 (1.8.2 加的键)
  hideDownloadMenuItem(track);
  $("#track-menu").querySelector('[data-track-action="play"]').hidden = false;
  $("#track-menu-lyrics").hidden = true;   // 调整面板对着正在播的那首, 行菜单不带
  const menu = $("#track-menu");
  menu.hidden = false;
  $("#track-menu-mask").hidden = false;
  placeMenuAt(menu, point);
}

/** 全屏页 ⋯: 对着当前曲目开菜单 (没有行, 「播放」项藏掉 — 正在播呢)。 */
function openTrackMenuForTrack(track, point) {
  rowForTrackMenu = null;
  menuTrackDirect = track;
  $("#menu-track-title").textContent = track.title;
  $("#menu-track-artist").textContent = track.artist;
  $("#track-menu-artist").hidden = !track.artist_id;
  $("#track-menu-album").hidden = !track.album_id;
  hideDownloadMenuItem(track);
  $("#track-menu").querySelector('[data-track-action="play"]').hidden = true;
  $("#track-menu-lyrics").hidden = false;  // 1.8.133 调整歌词 (仅 ⋯ 变体有)
  const menu = $("#track-menu");
  menu.hidden = false;
  $("#track-menu-mask").hidden = false;
  placeMenuAt(menu, point);
}

/** 「下载」项 (1.8.6 用户点名加进 ⋯ 菜单): 离线下载没开 (明文 HTTP)
    或这首已下好 — 藏掉, 别给点了没反应的钮。 */
function hideDownloadMenuItem(track) {
  $("#track-menu-download").hidden = !downloadsEnabled
    || !downloads || downloads.isDownloaded(track.track_id);
}

/** 菜单定位: 触点下方, 出屏就翻到上方/收边 (fixed 元素, 坐标即视口)。
    竖向下限取全局上边界 (1.8.19 用户令: 固定控件不越过它) —— 长按
    首行时菜单也不会顶进磨砂带; #top-clear-probe 是边界的量尺 (钉在
    边界上的隐形件, offsetTop 即边界值)。 */
function placeMenuAt(menu, point) {
  menu.style.left = "0px";
  menu.style.top = "0px";
  const rect = menu.getBoundingClientRect();
  const margin = 10;
  const probe = $("#top-clear-probe");
  const minY = probe ? probe.offsetTop : margin;
  const width = document.documentElement.clientWidth;
  const height = document.documentElement.clientHeight;
  const x = Math.min(Math.max(point.x - rect.width / 2, margin),
                     width - rect.width - margin);
  let y = point.y + 14;
  if (y + rect.height > height - margin) y = point.y - rect.height - 14;
  menu.style.left = `${Math.max(margin, Math.round(x))}px`;
  menu.style.top = `${Math.max(minY, Math.round(y))}px`;
}

function closeTrackMenu() {
  $("#track-menu").hidden = true;
  $("#track-menu-mask").hidden = true;
  rowForTrackMenu = null;
  menuTrackDirect = null;
}

// 封面菜单: 长按/右键播放列表大封面弹「换封面 / 移除封面」(共用曲目菜单的遮罩)。
