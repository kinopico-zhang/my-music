// music-settings-account — 设置页的账号块 (1.8.57, 用户点名「设置界面, 账号
// 可以改名字和密码」): 当前账号 + 行内改登录名 / 改密码 (账号自助接口: 改名
// uuid 不动会话不掉线, 改密码先验旧密码) + 退出登录 (从视图模块搬来)。块插
// 在通用页最前, 所有账号都能用, 不看管理员脸色。
"use strict";
/* global clearLastRoute, escapeHTML, fetchJSON, toast */
/* exported renderSettingsAccount */

/** 账号块渲染 + 接线 (target = 通用子页容器, me = /api/me 的当前账号)。 */
function renderSettingsAccount(target, me) {
  target.insertAdjacentHTML("afterbegin", `
    <div class="settings-block">
      <div class="settings-title">账号</div>
      ${me && me.name ? `
      <div class="settings-user"><svg viewBox="0 0 24 24" width="17" height="17" aria-hidden="true"><path d="M12 11.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7zM5.5 20a6.5 6.5 0 0 1 13 0" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg><span id="set-user-name">${escapeHTML(me.name)}</span>${me.is_admin ? "<em>管理员</em>" : ""}</div>
      <button type="button" class="settings-row" id="set-rename">修改名称</button>
      <div class="set-editor" id="set-rename-box" hidden>
        <div class="settings-field">
          <label for="set-rename-input">新名称</label>
          <input id="set-rename-input" spellcheck="false" autocomplete="off" maxlength="20">
          <small>2~20 个字符, 不含空格; 改完不用重新登录</small>
        </div>
        <div class="set-save-row"><button type="button" class="action primary" id="set-rename-save">保存名称</button></div>
      </div>
      <button type="button" class="settings-row" id="set-pass">修改密码</button>
      <div class="set-editor" id="set-pass-box" hidden>
        <div class="settings-field">
          <label for="set-pass-old">旧密码</label>
          <input type="password" id="set-pass-old" autocomplete="current-password">
        </div>
        <div class="settings-field">
          <label for="set-pass-new">新密码</label>
          <input type="password" id="set-pass-new" autocomplete="new-password">
          <small>6~64 个字符; 改完不用重新登录</small>
        </div>
        <div class="settings-field">
          <label for="set-pass-again">再输一遍新密码</label>
          <input type="password" id="set-pass-again" autocomplete="new-password">
        </div>
        <div class="set-save-row"><button type="button" class="action primary" id="set-pass-save">保存密码</button></div>
      </div>` : ""}
      <button type="button" class="settings-row logout" id="set-logout">退出登录</button>
    </div>`);
  const row = (selector) => target.querySelector(selector);
  const boxes = [row("#set-rename-box"), row("#set-pass-box")];
  // 两枚编辑器互斥, 点行开关: 开的收起, 收的展开 (顺手聚焦第一格)
  const toggleBox = (box) => {
    const opening = box.hidden;
    for (const other of boxes) other.hidden = true;
    if (opening) {
      box.hidden = false;
      box.querySelector("input").focus();
    }
  };
  row("#set-rename").addEventListener("click", () => toggleBox(boxes[0]));
  row("#set-pass").addEventListener("click", () => toggleBox(boxes[1]));
  row("#set-rename-save").addEventListener("click", async (event) => {
    const button = event.currentTarget;
    const input = row("#set-rename-input");
    const name = input.value.trim();
    if (!name) { toast("先填新名称"); return; }
    button.disabled = true;
    try {
      const updated = await fetchJSON("/api/account/name", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      row("#set-user-name").textContent = updated.name;   // 行上当场换新名
      toast("名称已改");
      input.value = "";
      boxes[0].hidden = true;
    } catch (error) {
      toast(error.message);      // 名称被占/不合规矩: 服务器的话直说
    } finally {
      button.disabled = false;
    }
  });
  row("#set-pass-save").addEventListener("click", async (event) => {
    const button = event.currentTarget;
    const fields = ["#set-pass-old", "#set-pass-new", "#set-pass-again"]
      .map((id) => row(id));
    if (fields.some((field) => !field.value)) { toast("先把三个框都填上"); return; }
    if (fields[1].value !== fields[2].value) { toast("两次输入的新密码不一样"); return; }
    button.disabled = true;
    try {
      await fetchJSON("/api/account/password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ old_password: fields[0].value,
                               new_password: fields[1].value }),
      });
      toast("密码已改");
      for (const field of fields) field.value = "";
      boxes[1].hidden = true;
    } catch (error) {
      toast(error.message);      // 旧密码不对/新密码太短: 服务器的话直说
    } finally {
      button.disabled = false;
    }
  });
  row("#set-logout").addEventListener("click", async () => {
    clearLastRoute();         // 上次停的页清档: 下个人别落进我的页面 (1.8.3)
    if (window.caches) {
      // 离线列表数据档也带走 (1.8.4): 换账号不能看着上个人的播放列表
      await caches.delete("music-data-v1").catch(() => {});
    }
    try { await fetch("/music/api/logout", { method: "POST" }); }
    catch (_error) { /* 清 cookie 失败也照样走 */ }
    location.href = "/music/login";
  });
}
