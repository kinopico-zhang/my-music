// music-viewport-doctor — My Music 视口体检 (1.8.12): 盯着「页面高度」本身。
// 病 (两轮回传实锤, iOS 18.7 独立模式): 键盘弹起 innerHeight 跟着缩
// (812→415), 收起后冻在矮值 (771, 差的 41 就是黑带) 不回来 —— WebKit 把
// 「键盘收起后的还原高度」记坏了, 页面里改不动它 (翻面/meta 踢/键盘往返
// 全试过无效); 滚位/偏移两味 1.8.7 已治好。本模块管「诊断 + 调度」:
//   ① 判据: 键盘开着 = 焦点在输入框 (iOS 18 独立模式里 vv 与 inner 永远
//      相等, 互比是空转 —— 1.8.10 误诊过还抢了用户焦点);
//   ② 治疗 (手法在 music-viewport-heal.js): 只有深修 (换新文档复位) 一招,
//      交给体检窗的按钮, 不自动刷 (正在听歌呢, 得用户点头);
//   ③ 体检窗 (music-viewport-hud.js 管「说」): 现场数字 + 回传服务器日志
//      (data/viewport-doctor.jsonl), 开局/深修归来都报数, 灵不灵有账可查。
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

  // ---------- 体检窗接线 (现场数字/深修/满高由这里注入, 屏显+回传归 HUD) ----------
  let deepRepairs = 0;
  let said = [];                       // 流水留底 (拼进现场数字最后几行)
  function stat() {
    return [
      "My Music 1.8.12 视口体检 (现场已回传)",
      `screen ${window.screen.width}x${window.screen.height} dpr ${window.devicePixelRatio}`,
      `inner ${window.innerHeight} / 满高 ${full} (差 ${full - window.innerHeight})`,
      `vv ${vv ? `${Math.round(vv.height)} top ${Math.round(vv.offsetTop)}` : "无"}`,
      `scrollY ${window.scrollY} · 焦点 ${typing() ? "输入框" : "无"}`,
      `深修 ${deepRepairs} 次`,
      "页面里救不回: 点「深度修复」刷新复位",
      "",
      ...said,
    ].join("\n");
  }
  function say(line) {
    said.push(`${new Date().toTimeString().slice(0, 8)} ${line}`);
    said = said.slice(-9);
    ViewportHUD.say(line);             // HUD: 屏显刷新 + 排进回传发件箱
  }
  function deepRepair() {
    if (!patient() || !sick()) return;
    deepRepairs += 1;
    ViewportHeal.reloadDeep();         // 手法在 heal 模块: 标记 + 刷新
  }
  ViewportHUD.wire({ stat, deepRepair });

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
        ViewportHUD.show();           // 深修按钮在窗上, 刷不刷新用户说了算
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
    // 键盘收起的实锤常迟半拍: 复查三遍 (350/900/1800ms)
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

  // 开局报数; 深修归来 (15 秒内带标记回来) 先报复位成没成, 再把标记清掉
  say(`开局 i${window.innerHeight} 满高${full}`);
  try {
    const at = Number(localStorage.getItem("music.deepRepairAt") || 0);
    if (at && Date.now() - at < 15000) {
      say(`深修归来 i${window.innerHeight} 满高${full}`
        + (window.innerHeight >= full - 12 ? " 复位成功" : " 还是矮的"));
      localStorage.removeItem("music.deepRepairAt");
    }
  } catch (_error) { /* 读不了就当没标记 */ }
  check();
  return { settled, check };
})();
