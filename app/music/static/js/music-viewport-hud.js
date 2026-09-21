// music-viewport-hud — 视口体检回传 (1.8.15, 配合 music-viewport-doctor)。
// 1.8.43 屏显体检窗整个撤了 (用户点名「删除调试的红框, 打点就偷偷打点
// 就行了, 别弹框了」): 冻矮 1.8.32 起开局自动补偿, 红框只剩「补不上时
// 教真话」一条路 —— 现在真话也进日志, 屏幕上什么都不弹; 每行流水照旧
// 排进发件箱回传服务器 (data/viewport-doctor.jsonl) —— 手机上复现完,
// 日志已经在服务器上等人来读, 不用截图。本模块只管「发」: 病情的判断
// (满高基准/冻矮判定/自愈) 都在医生那里; 治疗 (键盘期文档解锁在
// music-global-events.js, 冷开壳高补偿在 music-viewport-doctor.js)。
"use strict";
/* exported ViewportHUD */

const ViewportHUD = (() => {
  let outbox = [];
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
  addEventListener("pagehide", send);
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) send();               // 切后台就送, 别等系统杀页
  });
  return { say, send };
})();
