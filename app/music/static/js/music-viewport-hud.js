// music-viewport-hud — 视口体检窗 + 回传 (1.8.13, 配合 music-viewport-doctor):
// 冻矮时亮相的现场数字小窗 (平时绝不出现), 治不了时给一句真话 (划掉重开
// 秒复原), 每行流水同时排进发件箱回传服务器 (data/viewport-doctor.jsonl)
// —— 手机上复现完, 日志已经在服务器上等人来读, 不用截图。本模块只管
// 「说」: 屏幕上说什么、往服务器发什么, 病情的判断 (满高基准/冻矮判定)
// 和治疗手法 (收键按住, music-viewport-heal) 都在医生那里, 通过 wire() 注入。
"use strict";
/* exported ViewportHUD */

const ViewportHUD = (() => {
  let stat = () => "";
  let outbox = [];
  let hud = null;
  let hudBody = null;
  let hudTick = 0;
  let sending = false;
  let flushTimer = 0;

  // 一行流水的现场快照 (字段与后端 ViewportEvent 对齐, 全部有封顶)
  function snapshot(line) {
    const vv = window.visualViewport;
    return { t: Date.now(), line: line.slice(0, 200),
             inner: window.innerHeight,
             vv: vv ? Math.round(vv.height) : 0,
             top: vv ? Math.round(vv.offsetTop) : 0,
             left: vv ? Math.round(vv.offsetLeft) : 0,
             scrollY: window.scrollY };
  }
  function say(line) {
    outbox.push(snapshot(line));
    outbox = outbox.slice(-96);
    if (hudBody) hudBody.textContent = stat();
    clearTimeout(flushTimer);                 // 攒 3 秒一批, 别一件事一发
    flushTimer = setTimeout(send, 3000);
  }
  function send() {
    if (sending || !outbox.length) return;
    sending = true;
    const batch = outbox;
    outbox = [];
    fetch("/music/api/viewport-log", {
      method: "POST",
      keepalive: true,                        // 离开页面那一批也要送到
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ua: navigator.userAgent,
                             events: batch.slice(-64) }),
    }).catch(() => {                           // 断网/服务器打盹: 退回箱里下回再发
      outbox = batch.concat(outbox).slice(-96);
    }).finally(() => { sending = false; });
  }
  function show() {
    if (!hud) {
      const sheet = document.createElement("style");
      // 挪出顶部刘海/状态栏的模糊地带 (1.8.10 弹在 top:8px 用户点不到);
      // 1.8.13 起没有按钮了 —— 刷新复位实测无效, 真话是划掉重开
      sheet.textContent = "#doctor-hud{position:fixed;"
        + "top:calc(env(safe-area-inset-top) + 8px);left:8px;z-index:999;"
        + "max-width:80vw;padding:8px 10px;border:1px solid #fa2d48;border-radius:8px;"
        + "background:rgba(0,0,0,.92);color:#f5f5f7;font:11px/1.6 ui-monospace,monospace;"
        + "white-space:pre-wrap;word-break:break-all}";
      document.head.appendChild(sheet);
      hud = document.createElement("div");
      hud.id = "doctor-hud";
      hudBody = document.createElement("div");
      hud.appendChild(hudBody);
      document.body.appendChild(hud);
    }
    hudBody.textContent = stat();
    hud.hidden = false;
    clearInterval(hudTick);              // 亮着期间每秒刷现场数字
    hudTick = setInterval(() => {
      if (!hud.hidden) hudBody.textContent = stat();
    }, 1000);
    send();                              // 亮相的现场先送一批
  }
  function hide() {
    if (hud) {
      hud.hidden = true;
      clearInterval(hudTick);
    }
  }
  function wire(options) {
    stat = options.stat;                       // 医生注入: 现场数字
  }
  addEventListener("pagehide", send);
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) send();               // 切后台就送, 别等系统杀页
  });
  return { say, show, hide, send, wire };
})();
