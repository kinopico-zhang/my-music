// music-top-pane — My Music 播放排行页 (1.8.31 新增, 用户点名): 菜单
// 「播放排行」进来的推入层, 本周/本月/今年三个榜左右滑切换 (设置页同款
// 壳法: 大标题 + 页签钉住, 正文横向 snap 三页各自竖滚)。行右缘只显示
// 该区间内的播放次数 —— 时长/下载标都不出 (用户点名); 引导位是名次。
// 数据按 play_events 流水算, 老库已有的播放没流水 —— 榜从记流水这天起算。
"use strict";
/* global bindTrackLists, fetchJSON, listPlaceholderHTML, pageState,
          syncPlayerIndicators, trackRowHTML */
/* exported renderTopPane */

// ------------------------------------------------------------ 播放排行页

// 三个榜 (数组序即页序): label 进页签, empty 是该区间没听过歌时的占位话
const TOP_PERIODS = [
  { key: "week", label: "本周", empty: "这周还没听过歌" },
  { key: "month", label: "本月", empty: "这个月还没听过歌" },
  { key: "year", label: "今年", empty: "今年还没听过歌" },
];

function renderTopPane(target) {
  target.innerHTML = `
    <div class="top-shell">
      <div class="pane-title">播放排行</div>
      <div class="top-tabs" id="top-tabs">
        ${TOP_PERIODS.map((period, index) => `
        <button type="button"${index === 0 ? ' class="on"' : ""}
                data-top-period="${period.key}">${period.label}</button>`).join("")}
      </div>
      <div id="top-body">
        ${TOP_PERIODS.map((period) => `
        <div class="top-page" data-top-page="${period.key}">${listPlaceholderHTML("加载中…")}</div>`).join("")}
      </div>
    </div>`;
  bindTopTabs(target);
  for (const period of TOP_PERIODS) loadTopPage(target, period);
}

/** 页签 ↔ 滑动互切 (设置页 bindSetTabs 同款): 点页签滑过去,
    手滑到哪页点亮哪页。 */
function bindTopTabs(target) {
  const body = target.querySelector("#top-body");
  const tabs = target.querySelector("#top-tabs");
  const highlight = (index) => {
    tabs.querySelector(".on").classList.remove("on");
    if (tabs.children[index]) tabs.children[index].classList.add("on");
  };
  tabs.addEventListener("click", (event) => {
    const button = event.target.closest("[data-top-period]");
    if (!button) return;
    const index = [...tabs.children].indexOf(button);
    highlight(index);
    body.scrollTo({ left: index * body.clientWidth, behavior: "smooth" });
  });
  body.addEventListener("scroll", () => {
    const index = Math.round(body.scrollLeft / (body.clientWidth || 1));
    if (!tabs.children[index] || tabs.children[index].classList.contains("on")) return;
    highlight(index);
  }, { passive: true });
}

/** 拉一个榜铺进自己的页: 名次占引导位 (播放中照旧顶成动条), 行右缘是
    区间内播放次数 (trailingHTML 顶掉时长位), plain 连下载标一起收走。
    三榜各自拉各自的 (拿不到只塌自己那一页), 点行开播的队列语境按页记。 */
async function loadTopPage(target, period) {
  let tracks = null;
  try {
    tracks = (await fetchJSON(`/music/api/plays/top?period=${period.key}`)).tracks;
  } catch (_error) { /* 下面占位文案兜底 */ }
  const element = target.querySelector(`[data-top-page="${period.key}"]`);
  if (!element || !element.isConnected) return;   // 层已被换掉/收走
  if (!tracks) {
    element.innerHTML = listPlaceholderHTML("排行拿不到, 稍后再试");
    return;
  }
  bindTrackLists(element, () => pageState.topPanes[period.key] || []);
  pageState.topPanes[period.key] = tracks;
  element.innerHTML = tracks.length
    ? tracks.map((track, index) => trackRowHTML(
        track, `<i class="top-rank">${index + 1}</i>`, "",
        `×${track.play_count}`, true)).join("")
    : listPlaceholderHTML(period.empty);
  syncPlayerIndicators();
}
