// music-downloads-pane — My Music 已下载独立页 (1.8.0 起): 下载管理
// (统计行/逐首大小/多选删除/左滑删除与取消) + 点行开播。
// 拆自 music-library-views (1.8.76: 下载面板与资料库专辑/艺人页分家,
// views 顶到 200 行帽按逻辑再切一刀, 代码逐字节未动); 1.8.77 统计行
// 加自动缓存用量一行 (music-autocache-integration 的私仓, LRU 自动让位)。
"use strict";
/* global $, autoCache, autoCacheEnabled, bindDownloadsSelect, bindLibraryBody,
          bindSwipeDelete, cancelDownloadAll, downloadRingHTML, downloads,
          downloadsEnabled, escapeHTML, formatBytes, listPlaceholderHTML,
          playerStart, syncDownloadsSelect, toast */
/* exported playDownloadedRow, refreshDownloadsBody, renderDownloadsBody,
            renderDownloadsPane */

/** 已下载页: 下载管理 (统计行/逐首大小/多选删除/左滑删除与取消)。 */
function renderDownloadsPane(target) {
  target.innerHTML = `
    <div class="pane-title">下载管理</div>
    <div class="lib-body" id="dl-pane-body"></div>`;
  const body = $("#dl-pane-body");
  bindLibraryBody(body);
  bindDownloadsSelect(target);   // 多选删除 (1.8.6): 绑 pane 层, 正文重铺不丢
  // 左滑删除 (1.8.17 用户点名, 替掉行尾删除钮): 绑 pane 层, 正文重铺不丢;
  // 曲库只读铁律不变 —— 这页删的只是下载缓存, 碰不到库里一个字节
  bindSwipeDelete(target, async (wrap) => {
    const trackId = Number(wrap.dataset.dlWrap);
    const busy = Boolean(wrap.querySelector(".busy"));
    if (busy) cancelDownloadAll();   // 批量下载在跑: 这首取消即整批叫停
    try {
      await downloads.removeDownload(trackId);
      toast(busy ? "已取消下载" : "已删除下载");
    } catch (error) {
      toast(`删除失败: ${error.message}`);
    }
  });
  renderDownloadsBody(body);
}

/** 已下载栏点行开播 (队列 = 已下载列表, 下载中的除外)。 */
function playDownloadedRow(trackId) {
  const tracks = downloads.entries().filter((entry) => !entry.state)
    .map((entry) => ({ ...entry, playable: true, lyrics_available: false,
                       file_format: "flac" }));
  const index = tracks.findIndex((track) => track.track_id === trackId);
  if (index >= 0) playerStart(tracks, index);
}

let downloadsRenderToken = 0;   // 重铺计数: 让在途的异步统计结果作废

/** "已下载"页 = 下载管理: 合计大小/每首大小/多选删除/左滑删除与取消
 *  (1.8.17 行尾删除钮和「全部删除」撤掉, 用户点名; 明文 HTTP 下没有
 *  这一套, 说清楚)。 */
function renderDownloadsBody(body) {
  if (!downloadsEnabled) {
    body.innerHTML = listPlaceholderHTML(
      "离线下载需要 HTTPS 环境 (当前是明文 HTTP); 局域网在线听不受影响");
    return;
  }
  const entries = downloads.entries();
  if (!entries.length) {
    // 1.8.77 自动缓存 (播放预取顺手落盘) 与手动下载分栏: 没有手动下载
    // 也把这行带出来 —— 不然统计行只认手动下载, 私仓用着却看不见
    body.innerHTML = listPlaceholderHTML(
      "还没有下载的歌曲; 曲目行右侧的下载标就是下载")
      + '<div class="dl-stats"><span class="dl-stats-main">'
      + '<small id="dl-autocache" hidden></small></span></div>';
    fillDownloadsStats(body);
    return;
  }
  body.innerHTML = `
    <div class="dl-stats">
      <span class="dl-stats-main">
        <strong id="dl-total">统计中…</strong>
        <small id="dl-quota"></small>
        <small id="dl-autocache" hidden
          title="播放时自动缓存下一曲; 满了自动清最久没听的"></small>
      </span>
      <span class="dl-actions">
        <button class="dl-clear" id="dl-select-delete" hidden aria-label="删除选中"><svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="M4 7h16M9.5 7V4.5h5V7M6.5 7l.7 12.5h9.6l.7-12.5M10 10.5v6M14 10.5v6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
        <button class="dl-clear" id="dl-select-toggle">多选</button>
      </span>
    </div>
    ${entries.map(downloadRowHTML).join("")}`;
  syncDownloadsSelect(body);   // 选择模式开着时整页重铺: 圈/勾按 state 补
  if (!entries.some((entry) => entry.state)) fillDownloadsStats(body);
  // 有下载在跑: 等完成再量, 免得白量 (收批时 refreshDownloadsBody 补)
}

/** 单行模板 (整页重铺与原地补丁共用)。1.8.17 改左滑删除: 行住进
 *  .swipe-wrap (行本体必须是 button, 左滑那套样式/手势认它), 删除钮
 *  垫在右缘底下; 1.8.18 封面裹进 .dl-art (多选的勾画在封面上)。 */
function downloadRowHTML(entry) {
  return `
    <div class="swipe-wrap" data-dl-wrap="${entry.track_id}">
      <button type="button" class="dl-row${entry.state ? " busy" : ""}" data-dl-row="${entry.track_id}">
        <span class="dl-art">${entry.state ? '<span class="t-art">♪</span>'
          : `<img class="t-art" loading="lazy" decoding="async" alt=""
                src="/music/media/tracks/${entry.track_id}/artwork"
                onerror="this.replaceWith(Object.assign(document.createElement('span'),{className:'t-art',textContent:'♪'}))">`}</span>
        <span class="t-main">
          <span class="t-title"><span class="t-title-text">${escapeHTML(entry.title || `曲目 ${entry.track_id}`)}</span></span>
          <small>${escapeHTML(entry.artist || "下载中…")}</small>
        </span>
        ${entry.state
          ? downloadRingHTML(entry.state.progress, 18)
          : `<span class="dl-state" data-dl-size="${entry.track_id}">…</span>`}
      </button>
      <button type="button" class="swipe-del" aria-label="${entry.state ? "取消下载" : "删除下载"}">${entry.state ? "取消" : "删除"}</button>
    </div>`;
}

/** 下载状态原地刷新 (1.8.5 修「下载中, 已下好行的封面闪」): 整页重铺会把
 *  所有行连同封面换成新 <img>, 解码间隙闪一下 —— 下载进度一秒触发好几
 *  次, 封面就一直闪。行集合没变 (同序同 id) 时只动该动的行: 进行中的换
 *  进度环, 刚下完的单行换新, 其余一根毫毛不碰。(1.8.17 行住进
 *  .swipe-wrap: 对照/换新都在 wrap 一级, 别把行抠出来裸换。) */
function refreshDownloadsBody(body) {
  const entries = downloads.entries();
  const wraps = body.querySelectorAll("[data-dl-wrap]");
  const sameSet = wraps.length === entries.length && entries.every(
    (entry, index) => Number(wraps[index].dataset.dlWrap) === entry.track_id);
  if (!sameSet) { renderDownloadsBody(body); return; }   // 行集合变了才重铺
  entries.forEach((entry, index) => {
    const wrap = wraps[index];
    const row = wrap.querySelector("[data-dl-row]");
    if (row.classList.contains("busy") === Boolean(entry.state)) {
      if (entry.state) {
        const ring = row.querySelector(".dl-ring");
        if (ring) ring.outerHTML = downloadRingHTML(entry.state.progress, 18);
      }
    } else {
      wrap.outerHTML = downloadRowHTML(entry);   // 忙闲翻转 (下完/重下): 整行换新
    }
  });
  if (!entries.some((entry) => entry.state)) fillDownloadsStats(body);   // 收批补统计
}

/** 统计与每首大小 (异步, 在途期间又重铺过就作废); 1.8.77 加自动缓存
 *  用量一行 (同步, 索引口径)。 */
async function fillDownloadsStats(body) {
  const token = ++downloadsRenderToken;
  const usage = await downloads.storageUsage();
  if (token !== downloadsRenderToken) return;         // 期间又重铺了, 结果作废
  const total = body.querySelector("#dl-total");
  if (total) {
    total.textContent = `${usage.entries.length} 首 · ${formatBytes(usage.totalBytes)}`;
  }
  for (const row of usage.entries) {
    const size = body.querySelector(`[data-dl-size="${row.track_id}"]`);
    if (size) size.textContent = formatBytes(row.bytes);
  }
  const auto = body.querySelector("#dl-autocache");
  if (auto) {
    const autoUsage = autoCacheEnabled && autoCache ? autoCache.usage() : null;
    if (autoUsage && autoUsage.count) {
      auto.textContent = `自动缓存 ${autoUsage.count} 首 · ${formatBytes(autoUsage.totalBytes)}`;
      auto.hidden = false;
    } else {
      auto.hidden = true;
    }
  }
  if (navigator.storage && navigator.storage.estimate) {
    navigator.storage.estimate().then((estimate) => {
      if (token !== downloadsRenderToken) return;
      const quota = body.querySelector("#dl-quota");
      if (quota && estimate && estimate.quota) {
        quota.textContent = `占手机存储 ${formatBytes(estimate.usage || 0)}`;
      }
    }).catch(() => {});
  }
}
