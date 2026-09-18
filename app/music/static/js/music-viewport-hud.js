// music-viewport-hud — 视口体检窗 + 回传 (1.8.11, 配合 music-viewport-doctor):
// 冻矮时亮相的现场数字小窗 (平时绝不出现), 每行流水同时排进发件箱回传
// 服务器 (data/viewport-doctor.jsonl) —— 手机上复现完, 日志已经在服务器上
// 等人来读, 不用截图。本模块只管「说」: 屏幕上说什么、往服务器发什么,
// 病情的判断 (满高基准/冻矮判定/修复探针) 都在医生那里, 通过 wire() 注入。
"use strict";
/* exported ViewportHUD */

const ViewportHUD = (() => {
  let stat = () => "";
  let repair = () => {};
  let full = () => window.innerHeight;
  let outbox = [];
  let hud = null;
  let hudBody = null;
  let probeBar = null;
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
      // 1.8.11: 挪出顶部刘海/状态栏的模糊地带 (1.8.10 弹在 top:8px, 用户
      // 点不到); 整扇窗都可点 = 立即修复 (按钮只是个样子, 冒泡上来一样算)
      sheet.textContent = "#doctor-hud{position:fixed;"
        + "top:calc(env(safe-area-inset-top) + 8px);left:8px;z-index:999;"
        + "max-width:80vw;padding:8px 10px;border:1px solid #fa2d48;border-radius:8px;"
        + "background:rgba(0,0,0,.92);color:#f5f5f7;font:11px/1.6 ui-monospace,monospace;"
        + "white-space:pre-wrap;word-break:break-all;cursor:pointer}"
        + "#doctor-hud button{display:block;margin:0 0 8px;padding:10px 26px;"
        + "border:1px solid #fa2d48;border-radius:999px;color:#fa2d48;"
        + "font:600 14px/1 ui-monospace,monospace;background:rgba(250,45,72,.12)}"
        + "#doctor-probe{position:fixed;left:0;right:0;height:5px;"
        + "background:#ff3b30;z-index:998}";
      document.head.appendChild(sheet);
      hud = document.createElement("div");
      hud.id = "doctor-hud";
      const fix = document.createElement("button");
      fix.type = "button";
      fix.textContent = "立即修复";
      hudBody = document.createElement("div");
      hud.append(fix, hudBody);
      hud.addEventListener("click", () => repair({ gesture: true, force: true }));
      probeBar = document.createElement("div");   // 画布探针: 画得进黑带说明
      probeBar.id = "doctor-probe";               // CSS 还能把页面撑满 (还有救)
      probeBar.style.top = `${full() - 6}px`;
      document.body.append(hud, probeBar);
    }
    hudBody.textContent = stat();
    hud.hidden = false;
    probeBar.hidden = false;
    clearInterval(hudTick);              // 亮着期间每秒刷现场数字
    hudTick = setInterval(() => {
      if (!hud.hidden) hudBody.textContent = stat();
    }, 1000);
    send();                              // 亮相的现场先送一批
  }
  function hide() {
    if (hud) {
      hud.hidden = true;
      probeBar.hidden = true;
      clearInterval(hudTick);
    }
  }
  function wire(options) {
    stat = options.stat;                       // 医生注入: 现场数字/修复/满高
    repair = options.repair;
    full = options.full;
  }
  addEventListener("pagehide", send);
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) send();               // 切后台就送, 别等系统杀页
  });
  return { say, show, hide, send, wire };
})();
