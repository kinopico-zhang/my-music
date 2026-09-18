// music-viewport-doctor — My Music 视口体检 (1.8.14): 盯着「页面高度」本身。
// 病 (四轮回传实锤, 独立模式 iPhone): 键盘弹起 innerHeight 跟着缩
// (812→415), 收起那一下 WebKit 把「还原高度」记成 415+偏移半路值 (771/776,
// 差的那截就是黑带), 页面里翻面/meta 踢/键盘往返/收键按住全无效 (1.8.11/
// 1.8.13 回传: 记账读的是苹果自家的数, 页面钉什么都没用), 刷新换文档也不行
// (坏值跟着 webview 走), 划掉重开只有三成灵 (回传实测 5 次开局 3 次带病)。
// 病根在起手不在收手: 键盘弹起时「焦点元素被挡住」→ iOS 滚文档让位 → 收起
// 按这个半路滚位记账。1.8.14 的治法在 music-global-events.js (预抬: 键盘
// 起手前把搜索栏抬到屏幕上部, 焦点元素一直在明处, 让位一下都不滚 —— 借鉴
// my-tesla 费用弹窗, 输入框居中, 同机同系统实测无恙); 本模块管「诊断+回传」:
//   ① 判据: 键盘开着 = 焦点在输入框 (独立模式里 vv 与 inner 永远相等,
//      互比是空转 —— 1.8.10 误诊过还抢了用户焦点);
//   ② 体检窗 (music-viewport-hud.js 管「说」): 现场数字 + 回传服务器日志
//      (data/viewport-doctor.jsonl); 治不了时直说真话 —— 回传实测「再进
//      一次搜索、点键盘收起键收掉、再返回」当场复原 (重启不保证灵)。
"use strict";
/* global ViewportHUD */
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
      "My Music 1.8.14 视口体检 (现场已回传)",
      `screen ${window.screen.width}x${window.screen.height} dpr ${window.devicePixelRatio}`,
      `inner ${window.innerHeight} / 满高 ${full} (差 ${full - window.innerHeight})`,
      `vv ${vv ? `${Math.round(vv.height)} top ${Math.round(vv.offsetTop)}` : "无"}`,
      `scrollY ${window.scrollY} · 焦点 ${typing() ? "输入框" : "无"}`,
      "治不了就再进搜索, 点键盘收起键收掉再返回 (重启不保证灵)",
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
        if (!patient() || typing() || !sick()) return;
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
