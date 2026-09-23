// music-share-links — My Music 的分享链接 (1.8.47 拆自 music-track-menus.js,
// 文件超 200 行按域再拆): 后端开 24 小时免登录的 uuid 链接, 有系统分享就
// 发 URL, 没有 (明文 HTTP) 退化为复制链接。1.8.47 (你报的「iOS 分享界面
// 上没有被分享内容的封面」): 封面抓成本地文件一起递给系统分享 —— 面板
// 只认 files 里的图才显示缩略图; 单曲/专辑/列表的选图逻辑在后端
// (share_routes 的 _share_artwork_path, 与微信卡片 og:image 同一段)。
"use strict";
/* global fetchJSON, toast */
/* exported shareAlbum, sharePlaylist, shareTrack */

/** 封面抓成本地文件 (1.8.47): 抓不着/系统不支持给 null, 退纯链接分享。 */
async function shareCoverFile(path) {
  try {
    const res = await fetch(path);
    if (!res.ok) return null;
    const blob = await res.blob();
    const file = new File([blob], "cover", { type: blob.type });
    return navigator.canShare({ files: [file] }) ? file : null;
  } catch (_error) { return null; }    // 封面没抓着: 分享照走
}

/** 分享 = 后端开一条 24 小时免登录的 uuid 链接 (应答带封面地址), 有系统
    分享就发 URL (歌名 - 歌手 + 链接 + 封面缩略图), 没有就复制链接。 */
async function shareByLink(kind, id, title, text) {
  let url = "";
  let artwork = null;
  try {
    const made = await fetchJSON("/music/api/shares", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ kind, id }),
    });
    url = `${location.origin}/music/share/${made.token}`;
    artwork = made.artwork;         // 1.8.47: 这份分享的封面 (面板缩略图)
  } catch (error) {
    toast(`分享链接没生成: ${error.message}`);
    return;
  }
  if (typeof navigator.share === "function") {
    const cover = artwork ? await shareCoverFile(artwork) : null;
    try {
      await navigator.share(cover ? { files: [cover], title, text, url }
                                  : { title, text, url });
    } catch (_error) { /* 用户取消/环境拒绝: 不算失败 */ }
    return;
  }
  let copied = false;
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(url);
      copied = true;
    } else {
      const input = document.createElement("textarea");
      input.value = url;
      document.body.appendChild(input);
      input.select();
      copied = document.execCommand("copy");
      input.remove();
    }
  } catch (_error) { /* 复制失败走下面的提示 */ }
  toast(copied ? "链接已复制, 24 小时内有效" : "这个环境分享不了");
}

async function shareTrack(track) {
  await shareByLink("track", track.track_id, track.title,
                    `${track.title} - ${track.artist}`);
}

/** 列表页的分享钮: 分享整个播放列表 (打开的人能看能听整张)。 */
async function sharePlaylist(playlist) {
  await shareByLink("playlist", playlist.playlist_id, playlist.name,
                    `播放列表「${playlist.name}」`);
}

/** 专辑页的分享钮 (1.8.33 用户点名): 分享整张专辑, 打开的人能看能听全碟。 */
async function shareAlbum(album) {
  await shareByLink("album", album.album_id, album.title,
                    `专辑「${album.title}」`);
}
