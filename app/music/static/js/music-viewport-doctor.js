// music-viewport-doctor — My Music 视口体检 (1.8.13): 盯着「页面高度」本身。
// 病 (三轮回传实锤, iOS 18.7 独立模式): 键盘弹起 innerHeight 跟着缩
// (812→415), 收起那一下 WebKit 把「还原高度」记成 415+偏移半路值 (771/776,
// 差的那截就是黑带), 页面里翻面/meta 踢/键盘往返全无效, 刷新换文档也不行
// (坏值跟着 webview 走); 滚位/偏移两味 1.8.7 已治好。本模块管「诊断+调度」:
//   ① 判据: 键盘开着 = 焦点在输入框 (iOS 18 独立模式里 vv 与 inner 永远
//      相等, 互比是空转 —— 1.8.10 误诊过还抢了用户焦点);
//   ② 治疗 (手法在 music-viewport-heal.js): 键盘一收就把视口偏移「按住」
//      在键盘整个高度上, 让那笔记账记成满高 (验方见 heal 头注);
//   ③ 体检窗 (music-viewport-hud.js 管「说」): 现场数字 + 回传服务器日志
//      (data/viewport-doctor.jsonl); 治不了时直说 —— 划掉重开应用秒复原
//      (回传实测: 换新文档没用, 坏值跟着 webview 走, 只有新 webview 干净)。
"use strict";
/* global ViewportHUD, ViewportHeal */
/* exported ViewportDoctor */

const ViewportDoctor = (() => {
  const vv = window.visualViewport;
  // 只有独立模式 iPhone 会病: 浏览器 Safari 的工具栏自己收放, innerHeight
  // 天生会动, 满高基准立不住; 安卓 interactive-widget 布局自己缩, 是正常。
  const patient = () => window.matchMedia("(display-mode: standalone)").matches
    && (/iP(hone|ad|od)/.test(navigator.userAgent)
        || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1));
  const landscape = () => window.matchMedia("(orientation: landscape)").matches;
  const typing = () => {               // 键盘开着的唯一可靠信号: 焦点在输入框
    const el = document.activeElement;
    return !!el && (el.tagName === "INPUT" || el.tagName === "TEXTAREA"
      || el.isContentEditable);
  };

  // ---------- 满高基准: 见过的最高个 (存档跨重启, 转屏按新方向重立) ----------
  let seenLandscape = landscape();
  let full = window.innerHeight;
  try {
    const saved = JSON.parse(localStorage.getItem("music.fullInner") || "null");
    if (saved && saved.landscape === seenLandscape) {
      full = Math.max(full, saved.height || 0);
    }
  } catch (_error) { /* 隐私模式读不了就只信开局值 */ }
  function noteFull() {
    if (window.innerHeight <= full) return;
    full = window.innerHeight;
    try {
      localStorage.setItem("music.fullInner",
        JSON.stringify({ height: full, landscape: seenLandscape }));
    } catch (_error) { /* 存不进就算了, 内存里那份还在 */ }
  }
  const sick = () => full - window.innerHeight > 12;  // 冻矮: 比满高矮一截

  // ---------- 体检窗接线 (现场数字由这里注入, 屏显+回传归 HUD) ----------
  let said = [];                       // 流水留底 (拼进现场数字最后几行)
  function stat() {
    return [
      "My Music 1.8.13 视口体检 (现场已回传)",
      `screen ${window.screen.width}x${window.screen.height} dpr ${window.devicePixelRatio}`,
      `inner ${window.innerHeight} / 满高 ${full} (差 ${full - window.innerHeight})`,
      `vv ${vv ? `${Math.round(vv.height)} top ${Math.round(vv.offsetTop)}` : "无"}`,
      `scrollY ${window.scrollY} · 焦点 ${typing() ? "输入框" : "无"}`,
      "治不了就划掉重开应用 (秒复原)",
      "",
      ...said,
    ].join("\n");
  }
  function say(line) {
    said.push(`${new Date().toTimeString().slice(0, 8)} ${line}`);
    said = said.slice(-9);
    ViewportHUD.say(line);             // HUD: 屏显刷新 + 排进回传发件箱
  }
  ViewportHUD.wire({ stat });

  // ---------- 冻矮判定: 焦点不在输入框 + 比满高矮 12px + 值定住 0.7s ----------
  let freezeTimer = 0;
  let freezeSnap = -1;
  let declared = false;                // 实锤一次就闩住, 回满才解 (别刷屏)
  function check() {
    if (!patient()) return;
    const nowLandscape = landscape();
    if (nowLandscape !== seenLandscape) {
      seenLandscape = nowLandscape;
      full = window.innerHeight;       // 转屏: 满高按新方向重立
    }
    noteFull();
    if (window.innerHeight >= full - 12) {     // 健在 (真回满): 清账收窗
      freezeSnap = -1;
      declared = false;
      clearTimeout(freezeTimer);
      ViewportHUD.hide();
      return;
    }
    if (typing()) {                            // 键盘还开着: 矮是应该的
      freezeSnap = -1;
      clearTimeout(freezeTimer);
      return;
    }
    if (declared) return;
    if (freezeSnap !== window.innerHeight) {
      freezeSnap = window.innerHeight;
      clearTimeout(freezeTimer);
      freezeTimer = setTimeout(() => {
        freezeSnap = -1;
        if (!patient() || typing() || window.innerHeight >= full - 12) return;
        declared = true;
        say(`冻矮实锤 inner=${window.innerHeight} 差${full - window.innerHeight}`);
        ViewportHUD.show();
      }, 700);
    }
  }

  if (vv) {
    vv.addEventListener("resize", () => {
      say(`resize i${window.innerHeight} v${Math.round(vv.height)}`);
      check();
    });
    vv.addEventListener("scroll", check);
  }
  document.addEventListener("focusin", (event) => {
    say(`focus ${event.target.tagName}#${event.target.id || "-"}`);
  });
  document.addEventListener("focusout", () => {
    say("focusout");
    // 收键按住 (1.8.13 验方): 键盘还开着 (innerHeight 矮着) 且焦点真走了,
    // 就把偏移钉在键盘整个高度上陪它收完 —— 「还原高度」那笔记账只在收起
    // 起手那一下记 (见 heal 头注), 钉住了就记成满高
    if (patient() && !typing() && sick()) {
      ViewportHeal.holdDuringDismissal(full - window.innerHeight, full, "收键");
    }
    setTimeout(check, 350);
    setTimeout(check, 900);
    setTimeout(check, 1800);
  });
  addEventListener("pageshow", check);
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) check();
  });
  setInterval(check, 1500);   // 冻矮后一声事件不响: 慢心跳兜底 (也刷体检窗数字)

  function settled() {
    if (!patient()) return !vv || vv.height >= window.innerHeight - 12;
    return window.innerHeight >= full - 12;  // 高度真回满才算键盘收稳
  }

  // 开局报数 (带上这趟文档怎么来的: 冷开 navigate/刷新 reload/回退
  // back_forward —— 12:33 那趟连开三次 812/771/812 的谜团靠它拆)
  const nav = (performance.getEntriesByType("navigation")[0] || {}).type || "?";
  say(`开局 i${window.innerHeight} 满高${full} ${nav}`);
  check();
  return { settled, check };
})();
