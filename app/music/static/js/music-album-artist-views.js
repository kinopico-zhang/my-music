// music-album-artist-views — My Music 专辑详情页 + 艺人详情页 (推入层内容)。
// 拆自 music.js (结构化重构: 代码逐字节未动, 经典脚本按 music.html 里的顺序加载, 跨模块引用走全局)。
"use strict";
/* global ICON_ACTION_PLAY, ICON_ACTION_SHARE, ICON_ACTION_SHUFFLE, ICON_DOWNLOAD,
          PLACEHOLDER_ARTWORK, albumArtworkURL, albumCardHTML, artistArtworkURL,
          bindHeroCollapse, bindTrackLists, describeDuration, downloadAllFromUI,
          downloadsEnabled, escapeHTML, fetchJSON, heroBarHTML,
          listPlaceholderHTML, navigate, playerStart, pushPaneTarget, shareAlbum,
          syncPlayerIndicators, toast, trackArtHTML, trackRowHTML,
          wireHeroBarActions */
/* exported renderAlbumView, renderArtistView */

// ------------------------------------------------------------ 专辑页

async function renderAlbumView(albumId, target) {
  target = target || pushPaneTarget();    // 二级层薄层; 兜底 #main (无层时)
  target.innerHTML = listPlaceholderHTML("加载中…");
  let page = null;
  try {
    page = await fetchJSON(`/music/api/albums/${albumId}`);
  } catch (error) {
    target.innerHTML = listPlaceholderHTML(`加载失败: ${error.message}`);
    return;
  }
  const album = page.album;
  const playable = page.tracks.filter((track) => track.playable);
  const metaText = [album.year || "",
    describeDuration(album.duration_seconds, album.track_count)]
    .filter(Boolean).join(" · ");
  target.innerHTML = `
    <div class="hero-head">
      <div class="album-hero">
        <img alt="" src="${albumArtworkURL(album)}"
             onerror="this.onerror=null;this.src='${PLACEHOLDER_ARTWORK}'">
        <div class="hero-txt">
          <h2>${escapeHTML(album.title)}</h2>
          <div class="hero-sub">
            <button class="hero-artist" data-artist-id="${album.artist_id}">${escapeHTML(album.artist_name)}</button>
            ${metaText ? `<small class="hero-meta">· ${escapeHTML(metaText)}</small>` : ""}
          </div>
        </div>
      </div>
      <div class="action-row">
        <button class="action icon primary" id="album-play" title="播放"
                aria-label="播放" ${playable.length ? "" : "disabled"}>
          ${ICON_ACTION_PLAY}</button>
        <button class="action icon" id="album-shuffle" title="随机播放"
                aria-label="随机播放" ${playable.length ? "" : "disabled"}>
          ${ICON_ACTION_SHUFFLE}</button>
        ${downloadsEnabled ? `
        <button class="action icon" id="album-download" title="下载全部"
                aria-label="下载全部" ${playable.length ? "" : "disabled"}>
          ${ICON_DOWNLOAD}</button>` : ""}
        <button class="action icon" id="album-share" title="分享"
                aria-label="分享">${ICON_ACTION_SHARE}</button>
      </div>
      ${heroBarHTML({ play: !!playable.length, shuffle: !!playable.length,
                      ...(downloadsEnabled ? { download: !!playable.length } : {}),
                      share: true })}
    </div>
    <div class="track-list" id="album-tracks">
      ${page.tracks.map((track) => trackRowHTML(track, trackArtHTML(track), "art")).join("")}
    </div>`;
  target.querySelector(".hero-artist").addEventListener("click", (event) => {
    navigate(`artist/${event.currentTarget.dataset.artistId}`);
  });
  const playAlbum = () => playerStart(page.tracks, page.tracks.indexOf(playable[0]));
  const shuffleAlbum = () => playerStart(page.tracks, page.tracks.indexOf(playable[0]), true);
  target.querySelector("#album-play").addEventListener("click", playAlbum);
  target.querySelector("#album-shuffle").addEventListener("click", shuffleAlbum);
  const albumDownload = target.querySelector("#album-download");
  if (albumDownload) {
    albumDownload.addEventListener("click", () => downloadAllFromUI(page.tracks));
  }
  const shareThisAlbum = () => shareAlbum(album);
  target.querySelector("#album-share").addEventListener("click", shareThisAlbum);
  // 顶栏动作条 (1.8.45): 收缩后 播放 + … 两颗在封面同行右靠, 与操作行同一套闭包
  wireHeroBarActions(target, {
    play: playAlbum, shuffle: shuffleAlbum,
    download: () => downloadAllFromUI(page.tracks), share: shareThisAlbum,
  });
  bindTrackLists(target.querySelector("#album-tracks"), () => page.tracks);
  bindHeroCollapse(target);              // 1.8.34 封面收缩顶栏 (上划钉成顶栏)
  syncPlayerIndicators();
}

// ------------------------------------------------------------ 艺人页

async function renderArtistView(artistId, target) {
  target = target || pushPaneTarget();    // 二级层薄层; 兜底 #main (无层时)
  target.innerHTML = listPlaceholderHTML("加载中…");
  let page = null;
  try {
    page = await fetchJSON(`/music/api/artists/${artistId}`);
  } catch (error) {
    target.innerHTML = listPlaceholderHTML(`加载失败: ${error.message}`);
    return;
  }
  const artist = page.artist;
  target.innerHTML = `
    <div class="hero-head">
      <div class="artist-hero">
        <img alt="" src="${artistArtworkURL(artist)}"
             onerror="this.onerror=null;this.src='${PLACEHOLDER_ARTWORK}'">
        <div class="hero-txt">
          <h2>${escapeHTML(artist.name)}</h2>
          <div class="hero-sub"><small class="hero-meta">${artist.album_count} 张专辑 · ${artist.track_count} 首</small></div>
        </div>
      </div>
      <div class="action-row">
        <button class="action icon primary" id="artist-play" title="播放"
                aria-label="播放">${ICON_ACTION_PLAY}</button>
        <button class="action icon" id="artist-shuffle" title="随机播放"
                aria-label="随机播放">${ICON_ACTION_SHUFFLE}</button>
      </div>
      ${heroBarHTML({ play: true, shuffle: true })}
    </div>
    <div class="section-head">专辑</div>
    <div class="album-grid" id="artist-albums">
      ${page.albums.map(albumCardHTML).join("")}
    </div>`;
  const playArtist = async (shuffle) => {
    try {
      const albumPages = await Promise.all(page.albums.map(
        (album) => fetchJSON(`/music/api/albums/${album.album_id}`)));
      const tracks = albumPages.flatMap((albumPage) => albumPage.tracks);
      if (!tracks.length) { toast("这位艺人还没有能播的曲目"); return; }
      playerStart(tracks, 0, shuffle);
    } catch (error) {
      toast(`加载失败: ${error.message}`);
    }
  };
  target.querySelector("#artist-play").addEventListener("click", () => playArtist(false));
  target.querySelector("#artist-shuffle").addEventListener("click", () => playArtist(true));
  wireHeroBarActions(target, {          // 顶栏动作条 (1.8.45): 就两颗, 不收 …
    play: () => playArtist(false), shuffle: () => playArtist(true),
  });
  target.querySelector("#artist-albums").addEventListener("click", (event) => {
    const card = event.target.closest("[data-album-id]");
    if (card) navigate(`album/${card.dataset.albumId}`);
  });
  bindHeroCollapse(target);              // 1.8.34 封面收缩顶栏 (上划钉成顶栏)
}

