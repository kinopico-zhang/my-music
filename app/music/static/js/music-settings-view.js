// music-settings-view — My Music 设置视图 (1.8.17 改版, 用户点名): 跟搜索页
// 同款左右滑子页 —— 通用 (账号/曲库/重扫) / 歌词 (联网补词) / 统计 / 更新;
// 蜂窝流量月账整个撤掉 (前端采集与后端接口一起拆了)。拆自 music.js
// (结构化重构), 住推入层 (菜单「设置」进来), 渲染目标由调用方给。
"use strict";
/* global checkScanStatus, clearLastRoute, escapeHTML, fetchJSON,
          renderChangelogView, renderStatsView, toast, userRescanPending: writable */
/* exported renderSettingsView, userRescanPending */

// ------------------------------------------------------------ 设置页
// 统计/更新子页复用各自的视图函数 (PANE_VIEWS 路由不变, 上次停在哪页
// 开局照旧回跳); 表单 (路径/开关/地址) 只有管理员能改 —— 普通账号只读。
// 曲库路径改了服务器会立刻重新扫描整个曲库。
// 元素查找全收在本层 target 里: 旧层滑出还挂着 DOM 的 420ms 里 $() 全局
// 找会抓错层 (搜索页 1.8.6 的教训); 统计子页同场可能还叠着独立的统计层
// (#stats-body 撞名), 更是非收不可。

async function renderSettingsView(target) {
  target.innerHTML = `
    <div class="settings-shell">
      <div class="pane-title">设置</div>
      <div class="set-tabs" id="set-tabs">
        <button type="button" class="on" data-set-tab="general">通用</button>
        <button type="button" data-set-tab="lyrics">歌词</button>
        <button type="button" data-set-tab="stats">统计</button>
        <button type="button" data-set-tab="changelog">更新</button>
      </div>
      <div id="settings-body">
        <div class="set-page" data-set-page="general"><p class="stat-empty">加载中…</p></div>
        <div class="set-page" data-set-page="lyrics"><p class="stat-empty">加载中…</p></div>
        <div class="set-page" data-set-page="stats"></div>
        <div class="set-page" data-set-page="changelog"></div>
      </div>
    </div>`;
  const page = (name) => target.querySelector(`[data-set-page="${name}"]`);
  bindSetTabs(target);
  // 统计/更新各自拉各自的数据 (拿不到也只塌自己那一页)
  renderStatsView(page("stats"));
  renderChangelogView(page("changelog"));
  let settings;
  try {
    settings = await fetchJSON("/music/api/settings");
  } catch (error) {
    const text = `<p class="stat-empty">设置拿不到: ${escapeHTML(error.message)}</p>`;
    page("general").innerHTML = text;
    page("lyrics").innerHTML = text;
    return;
  }
  if (!target.isConnected) return;               // 等数据的空档层已收走
  const me = await fetchJSON("/api/me").catch(() => null);
  if (!target.isConnected) return;
  const editable = !!(me && me.is_admin);        // 管理员才出得起保存钮
  const lock = editable ? "" : " disabled";
  const saveOrNote = editable
    ? '<div class="set-save-row"><button class="action primary set-save">保存设置</button></div>'
    : '<p class="settings-note">仅管理员可修改设置, 普通账号只读。</p>';
  page("general").innerHTML = `
    <div class="settings-block">
      <div class="settings-title">账号</div>
      ${me && me.name ? `<div class="settings-user"><svg viewBox="0 0 24 24" width="17" height="17" aria-hidden="true"><path d="M12 11.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7zM5.5 20a6.5 6.5 0 0 1 13 0" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg><span>${escapeHTML(me.name)}</span>${me.is_admin ? "<em>管理员</em>" : ""}</div>` : ""}
      <button class="settings-row logout" id="set-logout">退出登录</button>
    </div>
    <div class="settings-block">
      <div class="settings-title">音乐库</div>
      <div class="settings-field">
        <label for="set-dir">曲库路径</label>
        <input id="set-dir" spellcheck="false" autocomplete="off"${lock}
               placeholder="${escapeHTML(settings.music_directory_default)}"
               value="${escapeHTML(settings.music_directory)}">
        <small>服务器上存放音乐的目录 (留空用默认); 改了会立刻重新扫描整个曲库</small>
      </div>
      <button class="settings-row" id="set-rescan"
              title="增量重扫曲库 (没变的文件只 stat 不读标签)">重新扫描曲库</button>
    </div>
    ${saveOrNote}`;
  page("lyrics").innerHTML = `
    <div class="settings-block">
      <div class="settings-title">联网补歌词</div>
      <div class="settings-field switch-row">
        <label>库里没歌词时上网求一遍</label>
        <button class="switch${settings.lyrics_api_enabled ? " on" : ""}"
                id="set-lyrics-on" role="switch"${lock}
                aria-checked="${settings.lyrics_api_enabled}"><i></i></button>
      </div>
      <div class="settings-field">
        <label for="set-lyrics-base">歌词 API 地址</label>
        <input id="set-lyrics-base" spellcheck="false" autocomplete="off" inputmode="url"${lock}
               placeholder="${escapeHTML(settings.lyrics_api_default)}"
               value="${escapeHTML(settings.lyrics_api_base)}">
        <small>LRCLIB 兼容接口; 求到的歌词会写回曲库, 离线也能看</small>
      </div>
    </div>
    ${saveOrNote}`;
  target.querySelector("#set-rescan").addEventListener("click", async () => {
    try {
      await fetchJSON("/music/api/rescan", { method: "POST" });
      userRescanPending = true;      // 这轮收尾要出提示 (后台自动扫的不出)
      toast("开始扫描曲库");
      checkScanStatus();
    } catch (error) {
      toast(error.message);
    }
  });
  target.querySelector("#set-logout").addEventListener("click", async () => {
    clearLastRoute();         // 上次停的页清档: 下个人别落进我的页面 (1.8.3)
    if (window.caches) {
      // 离线列表数据档也带走 (1.8.4): 换账号不能看着上个人的播放列表
      await caches.delete("music-data-v1").catch(() => {});
    }
    try { await fetch("/music/api/logout", { method: "POST" }); }
    catch (_error) { /* 清 cookie 失败也照样走 */ }
    location.href = "/music/login";
  });
  if (!editable) return;
  const toggle = target.querySelector("#set-lyrics-on");
  toggle.addEventListener("click", () => {
    const on = toggle.getAttribute("aria-checked") !== "true";
    toggle.setAttribute("aria-checked", String(on));
    toggle.classList.toggle("on", on);
  });
  // 通用/歌词两页各一枚保存钮, 按哪枚都存整份 (两页的输入框同场都在)
  for (const button of target.querySelectorAll(".set-save")) {
    button.addEventListener("click", async () => {
      button.disabled = true;
      try {
        await fetchJSON("/music/api/settings", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            music_directory: target.querySelector("#set-dir").value.trim(),
            lyrics_api_enabled: toggle.getAttribute("aria-checked") === "true",
            lyrics_api_base: target.querySelector("#set-lyrics-base").value.trim(),
          }),
        });
        toast("设置已保存");
        checkScanStatus();      // 曲库路径换过的话, 扫描已起: 进度条接上
      } catch (error) {
        toast(`没保存上: ${error.message}`);
      } finally {
        button.disabled = false;
      }
    });
  }
}

/** 页签 ↔ 滑动互切 (搜索页 bindSearchTabs 同款): 点页签滑过去,
    手滑到哪页点亮哪页。 */
function bindSetTabs(target) {
  const body = target.querySelector("#settings-body");
  const tabs = target.querySelector("#set-tabs");
  const highlight = (index) => {
    tabs.querySelector(".on").classList.remove("on");
    if (tabs.children[index]) tabs.children[index].classList.add("on");
  };
  tabs.addEventListener("click", (event) => {
    const button = event.target.closest("[data-set-tab]");
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
