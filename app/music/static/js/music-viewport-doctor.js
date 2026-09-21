// music-viewport-doctor — My Music 视口体检 (1.8.16): 盯着「页面高度」本身。
// 病 (七轮诊疗, 独立模式 iPhone): 键盘弹起 innerHeight 跟着缩 (812→415),
// 收起那一下 WebKit 把「还原高度」记成 415+偏移半路值 (771, 差的那截
// 就是黑带), 页面里翻面/meta 踢/键盘往返/收键按住/预抬/层内配滚动器
// 全无效 (1.8.11/1.8.13/1.8.14/1.8.15 回传: 让位就是滚文档, 页内怎么
// 布置都不看), 刷新换文档也不行 (坏值跟着 webview 走), 划掉重开只有
// 三成灵 (回传实测 5 次开局 3 次带病)。1.8.16 定案 (用户实测病愈): 病根
// 在文档本身锁死 (html/body overflow:hidden 固定壳), 让位滚进去是幽灵
// 滚, 收键把幽灵滚位记进还原高度; 健康对照 (my-tesla 费用弹窗 /
// my-money 记账弹层, 同机同系统实测无恙) 的文档天生可滚, 让位是合法
// 滚动、收键走苹果日常百测的还原路径。治法 = 键盘期间解锁文档 (在
// music-global-events.js; 搜索页 1.8.15 的层内滚动结构留着没坏处)。
// 1.8.32 自愈 (用户点名「彻底解决」): 回传日志实锤 —— 会话内的病 1.8.16
// 已治好 (键盘往返全程干净), 剩下的是冷开那一刻: iOS 的还原高度跨进程
// 赖账, 约一半开局直接带 771 (满高 812, 每次正好差 41), 整程一声事件
// 不响、永不自愈, 只能划掉重开碰运气 (用户实测「反复重启才可以」;
// 开局健康则整程不再犯)。WebKit 写毒拦不住, 但布局自己说了算: 冻矮时
// 壳高直接钉记档的满高 (--shell-h, music-base.css 消费), 黑带当场补回
// —— 开局即愈, 不用用户动手; 回满自动撤。红框体检窗 1.8.43 整个撤了
// (用户点名「打点就偷偷打点就行了」), 只留静默回传。
// 本模块管「诊断+自愈+回传」:
//   ① 判据: 键盘开着 = 焦点在输入框 (独立模式里 vv 与 inner 永远相等,
//      互比是空转 —— 1.8.10 误诊过还抢了用户焦点);
//   ② 静默回传 (music-viewport-hud.js 管「发」): 每行流水回传服务器日志
//      (data/viewport-doctor.jsonl), 屏幕上什么都不弹 —— 红框 1.8.43 撤
//      了, 治不了的现场也只进日志。
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

  // ---------- 冻矮自愈 (1.8.32): 布局别信 webview 的还原高度 ----------
  // 满高钳在屏内 (竖屏取长边/横屏取短边): 防基线本身被瞬时值带高,
  // 补偿铺出屏外反而截掉底栏。
  const capOf = () => landscape() ? Math.min(screen.width, screen.height)
                                  : Math.max(screen.width, screen.height);
  function shellH(on) {   // 冻矮: 壳高钉真满高 (music-base.css 消费)
    const root = document.documentElement;
    if (on) root.style.setProperty(
      "--shell-h", Math.min(full, capOf()) + "px");
    else root.style.removeProperty("--shell-h");
  }

  // ---------- 回传接线 (打点静默走, 屏幕上什么都不弹) ----------
  function say(line) {
    ViewportHUD.say(line);             // 排进回传发件箱 (1.8.43: 屏显撤了)
  }

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
      shellH(false);                   // 冻矮补偿撤掉 (壳高回真 100dvh)
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
        const patched = Math.min(full, capOf());
        shellH(true);   // 自愈: 壳高钉真满高, 冷开冻矮当场补 (不用用户动手)
        say(`冻矮实锤 inner=${window.innerHeight} 差${full - window.innerHeight} 补${patched}`);
        if (patched <= window.innerHeight) say("补不上: 现场已回传");   // 只进日志, 红框撤了
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
  setInterval(check, 1500);   // 冻矮后一声事件不响: 慢心跳兜底 (自愈用, 不刷屏)

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
