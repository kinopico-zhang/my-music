// music-lyrics-edit — 调整歌词面板 (1.8.133, 播放页 ⋯ 菜单进来): 底部弹层
// 盖在歌词视图上 —— 界面就是正在播的那页歌词, 面板开着照常跟唱。搜到的
// 候选点一下就换上 (听着不对再换), 时间轴微调 ±0.5 秒即点即生效 (本地
// 先动, 静下来 0.7 秒再落库 —— 连点只存最后一笔, 收面板时兜底存一次)。
"use strict";
/* global $, escapeHTML, fetchJSON, highlightActiveLyric,
          loadLyrics, lyricsCache, lyricsOffsets, onTrackChange, openLyricsView,
          parseLyrics, syncLyricsButton, toast */
/* exported closeLyricsEditSheet, openLyricsEditSheet */

const LYR_SOURCE_LABELS = { netease: "网易云", qq: "QQ 音乐", lrclib: "LRCLIB" };
const OFFSET_STEP_MS = 500;      // 一步半秒
const OFFSET_LIMIT_MS = 30000;   // 与服务端同一钳制

let lyricsEditTrackId = 0;   // 面板对着哪首 (换曲就收面板)
let lastCandidates = [];     // 最近一次搜到的候选 (行点击按序号取)
let searchSeq = 0;           // 搜索请求序号: 迟到的应答别盖新的
let applying = false;        // 套用请求在跑 (防连点双发)
let offsetSaveTimer = 0;     // 微调落库防抖句柄 (0 = 没有待存的)

/** ⋯ 菜单「调整歌词」: 开面板 (确保歌词视图开着 —— 预览就在那页上)。 */
function openLyricsEditSheet(track) {
  if (!track) return;
  lyricsEditTrackId = track.track_id;
  openLyricsView();
  $("#lyr-edit-query").value = `${track.title} ${track.artist}`.trim();
  $("#lyr-edit-list").innerHTML = "";
  $("#lyr-edit-status").textContent = "";
  syncOffsetRow();
  $("#lyr-edit-mask").hidden = false;
  $("#lyr-edit-sheet").hidden = false;
}

/** 收面板: 落库里还没存的微调先存上。 */
function closeLyricsEditSheet() {
  saveOffsetNow();
  lyricsEditTrackId = 0;
  lastCandidates = [];
  $("#lyr-edit-sheet").hidden = true;
  $("#lyr-edit-mask").hidden = true;
}

/** 微调一行: 值 + 灰钮规则 + 提示文案。 */
function syncOffsetRow() {
  const doc = lyricsCache.get(lyricsEditTrackId);
  const offset = lyricsOffsets.get(lyricsEditTrackId) || 0;
  $("#lyr-edit-offset-val").textContent = offset
    ? `${offset > 0 ? "延后" : "提前"} ${Math.abs(offset) / 1000} 秒` : "0 秒";
  const adjustable = !!(doc && doc.synced);   // 纯文本词没有时间轴可调
  $("#lyr-edit-earlier").disabled = !adjustable;
  $("#lyr-edit-later").disabled = !adjustable;
  $("#lyr-edit-reset").disabled = !adjustable || offset === 0;
  $("#lyr-edit-offset-hint").textContent = adjustable ? ""
    : doc ? "这套词没有时间轴, 微调不适用" : "这首还没有词, 先搜一套";
}

/** 微调一步: 本地先动 (高亮就地重算这一拍, 当场看得见效果), 防抖落库。 */
function bumpOffset(deltaMs) {
  const trackId = lyricsEditTrackId;
  if (!trackId) return;
  const next = (lyricsOffsets.get(trackId) || 0) + deltaMs;
  lyricsOffsets.set(trackId,
                    Math.max(-OFFSET_LIMIT_MS, Math.min(OFFSET_LIMIT_MS, next)));
  syncOffsetRow();
  highlightActiveLyric();
  clearTimeout(offsetSaveTimer);
  offsetSaveTimer = setTimeout(saveOffsetNow, 700);
}

/** 把当前微调存上服务器 (面板收起/静置时)。 */
function saveOffsetNow() {
  if (!offsetSaveTimer) return;   // 没有待存的
  clearTimeout(offsetSaveTimer);
  offsetSaveTimer = 0;
  const trackId = lyricsEditTrackId;
  fetchJSON(`/music/api/tracks/${trackId}/lyrics/offset`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ offset_ms: lyricsOffsets.get(trackId) || 0 }),
  }).catch(() => toast("微调没存上, 下次打开再试一次"));
}

/** 搜候选: 三家厂商并搜 (服务端转交), 行里点一下套用。 */
async function runLyricsSearch() {
  const trackId = lyricsEditTrackId;
  const query = $("#lyr-edit-query").value.trim();
  if (!trackId || !query) return;
  const seq = ++searchSeq;
  $("#lyr-edit-search").disabled = true;
  $("#lyr-edit-status").textContent = "搜索中…";
  $("#lyr-edit-list").innerHTML = "";
  try {
    const response = await fetchJSON(
      `/music/api/tracks/${trackId}/lyrics/candidates`
      + `?q=${encodeURIComponent(query)}`);
    if (seq !== searchSeq || trackId !== lyricsEditTrackId) return;
    lastCandidates = response.candidates || [];
    if (!lastCandidates.length) {
      $("#lyr-edit-status").textContent = "没搜到, 换个词试试";
      return;
    }
    $("#lyr-edit-status").textContent = "点一下哪份, 立刻换上";
    $("#lyr-edit-list").innerHTML = lastCandidates.map((candidate, index) => `
      <button type="button" class="lyr-edit-row" data-cand="${index}">
        <span class="a-main"><b>${escapeHTML(candidate.title)}</b>
        <small>${escapeHTML(candidate.artist || "未知艺人")} · ${
  escapeHTML(LYR_SOURCE_LABELS[candidate.source] || candidate.source)
}${candidate.synced === false ? " · 纯文本" : ""}</small></span>
      </button>`).join("");
  } catch (error) {
    if (seq !== searchSeq) return;
    $("#lyr-edit-status").textContent = `没搜到: ${error.message}`;
  } finally {
    if (seq === searchSeq) $("#lyr-edit-search").disabled = false;
  }
}

/** 套用选中的候选: 服务端取词写库 (清旧微调), 前端缓存换新就地重铺。 */
async function applyCandidate(index) {
  const trackId = lyricsEditTrackId;
  const candidate = lastCandidates[index];
  if (!trackId || !candidate || applying) return;
  applying = true;
  $("#lyr-edit-status").textContent = "换词中…";
  try {
    const response = await fetchJSON(
      `/music/api/tracks/${trackId}/lyrics/apply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: candidate.source, ref: candidate.ref }),
      });
    if (trackId !== lyricsEditTrackId) return;   // 面板已收/已换曲
    lyricsCache.set(trackId,
                    response.lyrics ? parseLyrics(response.lyrics) : null);
    lyricsOffsets.set(trackId, response.lyrics_offset_ms || 0);
    await loadLyrics();            // 缓存已换新, 重铺 + 高亮即时跟上
    syncLyricsButton();
    syncOffsetRow();
    $("#lyr-edit-status").textContent = "已换上, 听着不对再换一份";
  } catch (error) {
    $("#lyr-edit-status").textContent = `没换成: ${error.message}`;
  } finally {
    applying = false;
  }
}

$("#lyr-edit-mask").addEventListener("click", closeLyricsEditSheet);
$("#lyr-edit-close").addEventListener("click", closeLyricsEditSheet);
$("#lyr-edit-search").addEventListener("click", () => { void runLyricsSearch(); });
$("#lyr-edit-query").addEventListener("keydown", (event) => {
  if (event.key === "Enter") {          // 手机键盘「搜索」键
    event.preventDefault();
    void runLyricsSearch();
  }
});
$("#lyr-edit-earlier").addEventListener("click", () => bumpOffset(-OFFSET_STEP_MS));
$("#lyr-edit-later").addEventListener("click", () => bumpOffset(OFFSET_STEP_MS));
$("#lyr-edit-reset").addEventListener(
  "click", () => bumpOffset(-(lyricsOffsets.get(lyricsEditTrackId) || 0)));
$("#lyr-edit-list").addEventListener("click", (event) => {
  const button = event.target.closest("[data-cand]");
  if (button) void applyCandidate(Number(button.dataset.cand));
});
// 换曲: 面板对着的那首已经不是正在播的, 收掉 (候选/微调都是那首的事)
onTrackChange(() => {
  if (lyricsEditTrackId) closeLyricsEditSheet();
});
