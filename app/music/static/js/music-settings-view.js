// music-settings-view — My Music 设置视图 (1.8.17 改版, 用户点名): 跟搜索页
// 同款左右滑子页 —— 通用 (账号/曲库/重扫) / 歌词 (联网补词) / 统计 / 更新;
// 1.8.57 普通账号只见 账号/统计/更新 (管理员配置整个收走, 用户点名), 账号块
// (自助改名/改密码) 拆去 music-settings-account.js。拆自 music.js, 住推入层
// (菜单「设置」进来), 渲染目标由调用方给。
"use strict";
/* global checkScanStatus, escapeHTML, fetchJSON,
          renderChangelogView, renderSettingsAccount, renderStatsView,
          toast, userRescanPending: writable */
/* exported renderSettingsView, userRescanPending */

// ------------------------------------------------------------ 设置页
// 统计/更新子页复用各自的视图函数 (PANE_VIEWS 路由不变, 上次停在哪页
// 开局照旧回跳); 曲库/歌词表单只给管理员渲染 (1.8.57 普通账号连歌词页签
// 一起收走, 不再摆只读的锁)。曲库路径改了服务器会立刻重新扫描整个曲库。
// 元素查找全收在本层 target 里: 旧层滑出还挂着 DOM 的 420ms 里 $() 全局
// 找会抓错层 (搜索页 1.8.6 的教训); 统计子页同场可能还叠着独立的统计层
// (#stats-body 撞名), 更是非收不可。

async function renderSettingsView(target) {
  target.innerHTML = `
    <div class="settings-shell">
      <div class="pane-title">软件设置</div>
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
  const me = await fetchJSON("/api/me").catch(() => null);
  if (!target.isConnected) return;               // 等数据的空档层已收走
  const editable = !!(me && me.is_admin);        // 管理员才出得起设置表单
  if (!editable) {        // 1.8.57 用户点名: 普通账号不看音乐库的设置 ——
    target.querySelector('[data-set-tab="lyrics"]').remove();   // 歌词页整页
    page("lyrics").remove();                                     // 都是管理员
  }                                                              // 配置, 连页
  let settings;                                                 // 签一并收走
  try {
    settings = await fetchJSON("/music/api/settings");
  } catch (error) {
    const text = `<p class="stat-empty">设置拿不到: ${escapeHTML(error.message)}</p>`;
    if (editable) page("lyrics").innerHTML = text;
    page("general").innerHTML = editable ? text : "";
    renderSettingsAccount(page("general"), me);  // 设置塌了, 账号块照常能用
    return;
  }
  if (!target.isConnected) return;
  const saveRow = '<div class="set-save-row"><button class="action primary set-save">保存设置</button></div>';
  page("general").innerHTML = editable ? `
    <div class="settings-block">
      <div class="settings-title">音乐库</div>
      <div class="settings-field">
        <label for="set-dir">曲库路径</label>
        <input id="set-dir" spellcheck="false" autocomplete="off"
               placeholder="${escapeHTML(settings.music_directory_default)}"
               value="${escapeHTML(settings.music_directory)}">
        <small>服务器上存放音乐的目录 (留空用默认); 改了会立刻重新扫描整个曲库</small>
      </div>
      <button class="settings-row" id="set-rescan"
              title="增量重扫曲库 (没变的文件只 stat 不读标签)">重新扫描曲库</button>
    </div>
    ${saveRow}` : "";                     // 普通账号: 通用页只剩账号块
  renderSettingsAccount(page("general"), me);   // 账号块插最前 (1.8.57)
  if (!editable) return;                         // 下面的表单只在管理员位
  // 歌词厂商 (1.8.57 用户点名「多提供几个厂商」): 空键 = 自动依次试;
  // 老库存了 auto/没见过的键也归「自动」, 别让键上没灯
  const provider = ["lrclib", "netease", "qq"].includes(
    settings.lyrics_api_provider) ? settings.lyrics_api_provider : "";
  const provs = [["", "自动"], ["lrclib", "LRCLIB"],
                 ["netease", "网易云"], ["qq", "QQ 音乐"]];
  page("lyrics").innerHTML = `
    <div class="settings-block">
      <div class="settings-title">联网补歌词</div>
      <div class="settings-field switch-row">
        <label>库里没歌词时上网求一遍</label>
        <button class="switch${settings.lyrics_api_enabled ? " on" : ""}"
                id="set-lyrics-on" role="switch"
                aria-checked="${settings.lyrics_api_enabled}"><i></i></button>
      </div>
      <div class="settings-field">
        <label>歌词厂商</label>
        <div class="set-prov" id="set-prov">
          ${provs.map(([key, label]) => `<button type="button" data-prov="${key}"${key === provider ? ' class="on"' : ""}>${label}</button>`).join("")}
        </div>
        <small>自动 = 网易云 → QQ → LRCLIB 依次试到求到为止</small>
      </div>
      <div class="settings-field" id="set-lyrics-base-row"${provider !== "lrclib" ? " hidden" : ""}>
        <label for="set-lyrics-base">LRCLIB 接口地址</label>
        <input id="set-lyrics-base" spellcheck="false" autocomplete="off" inputmode="url"
               placeholder="${escapeHTML(settings.lyrics_api_default)}"
               value="${escapeHTML(settings.lyrics_api_base)}">
        <small>LRCLIB 兼容接口可换地址 (其他厂商走官方接口); 求到的歌词写回曲库, 离线也能看</small>
      </div>
    </div>
    ${saveRow}`;
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
  const toggle = target.querySelector("#set-lyrics-on");
  toggle.addEventListener("click", () => {
    const on = toggle.getAttribute("aria-checked") !== "true";
    toggle.setAttribute("aria-checked", String(on));
    toggle.classList.toggle("on", on);
  });
  // 厂商键: 点亮自己; 地址行只有 LRCLIB 用得上, 换家就收起
  target.querySelectorAll("#set-prov button").forEach((chip) => {
    chip.addEventListener("click", () => {
      target.querySelector("#set-prov .on").classList.remove("on");
      chip.classList.add("on");
      target.querySelector("#set-lyrics-base-row").hidden =
        chip.dataset.prov !== "lrclib";
    });
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
            lyrics_api_provider: target.querySelector("#set-prov .on").dataset.prov,
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
