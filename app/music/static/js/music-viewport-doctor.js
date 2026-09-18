// music-viewport-doctor — My Music 视口体检 (1.8.10): 盯着「页面高度」本身。
// 1.8.9 修底部黑带没断根 (用户再报): 键盘收起时 iOS 连 innerHeight 都带着
// 走一小段动画 (录屏量出冻在满高-41pt 的中间值), 收层若在动画半路移除
// DOM, 「长回去」那最后一下更新就丢了 —— 页面从此矮一截, fixed 船坞跟着
// 浮起, 屏底露出系统黑底。本模块三件事:
//   ① settled() 收层的真判据: 独立模式 iPhone 等 innerHeight 回到见过的
//      满高才算键盘收稳 (1.8.9 的判据 vv.height ≥ innerHeight 在高度自己
//      动的时候恒真, 等了白等 —— 1.8.10 换判据, 见 removePaneWhenSettled);
//   ② 冻矮自愈: 常驻隐形输入框走一趟 focus→blur 逼系统重算 (定时器里
//      iOS 未必肯弹键盘, 再借用户下一次触屏补一趟, 体检窗按钮也是一手);
//   ③ 冻矮超过 0.7s 亮体检窗 (music-viewport-hud.js 管「说」: 屏幕上亮
//      现场数字, 每行流水同时回传服务器日志 —— 复现完直接读档分析)。
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

  // ---------- 自愈探针: 常驻隐形输入框 (样式在 music-base.css), 从不移除 ----------
  let probe = null;
  if (patient()) {
    probe = document.createElement("input");
    probe.id = "kb-repair";
    probe.type = "text";
    probe.tabIndex = -1;
    probe.autocomplete = "off";
    probe.setAttribute("autocapitalize", "off");
    probe.setAttribute("autocorrect", "off");
    probe.setAttribute("aria-hidden", "true");
    document.body.appendChild(probe);
  }

  // ---------- 体检窗接线 (现场数字/修复/满高由这里注入, 屏显+回传归 HUD) ----------
  let repairs = 0;
  let gestureArmed = false;
  let said = [];                       // 流水留底 (拼进现场数字最后几行)
  function stat() {
    return [
      "My Music 1.8.10 视口体检 (现场已回传, 也可截图)",
      `screen ${window.screen.width}x${window.screen.height} dpr ${window.devicePixelRatio}`,
      `inner ${window.innerHeight} / 满高 ${full} (差 ${full - window.innerHeight})`,
      `vv ${vv ? `${Math.round(vv.height)} top ${Math.round(vv.offsetTop)}` : "无"}`,
      `scrollY ${window.scrollY} · 已修 ${repairs} 次`,
      "",
      ...said,
    ].join("\n");
  }
  function say(line) {
    said.push(`${new Date().toTimeString().slice(0, 8)} ${line}`);
    said = said.slice(-9);
    ViewportHUD.say(line);             // HUD: 屏显刷新 + 排进回传发件箱
  }
  function repair() {
    if (repairs >= 3) return;               // 别闪个没完
    repairs += 1;
    say(`自修 #${repairs}: 探针 focus→blur`);
    ViewportHUD.send();                     // 修复是大事, 不攒批当场送
    probe.focus();
    setTimeout(() => probe.blur(), 150);
  }
  function armGesture() {
    if (gestureArmed) return;
    gestureArmed = true;
    addEventListener("pointerdown", () => {  // 定时器没手势未必唤得动键盘
      gestureArmed = false;
      if (full - window.innerHeight > 12) repair();
    }, { once: true });
  }
  ViewportHUD.wire({ stat, repair, full: () => full });

  // ---------- 冻矮判定: 值还动着先等半秒, 定住了才算实锤 ----------
  let freezeTimer = 0;
  let freezeSnap = -1;
  const keyboardGone = () => !vv || vv.height >= window.innerHeight - 12;
  function check() {
    if (!patient()) return;
    const nowLandscape = landscape();
    if (nowLandscape !== seenLandscape) {
      seenLandscape = nowLandscape;
      full = window.innerHeight;             // 转屏: 满高按新方向重立
    }
    noteFull();
    if (!(keyboardGone() && full - window.innerHeight > 12)) {
      freezeSnap = -1;
      clearTimeout(freezeTimer);
      if (keyboardGone()) {
        repairs = 0;                         // 健在: 下回赖账重新给满三回
        ViewportHUD.hide();
      }
      return;
    }
    if (freezeSnap !== window.innerHeight) {
      freezeSnap = window.innerHeight;
      clearTimeout(freezeTimer);
      freezeTimer = setTimeout(() => {
        freezeSnap = -1;
        if (!patient() || !keyboardGone()) return;
        if (full - window.innerHeight <= 12) return;
        say(`冻矮实锤 inner=${window.innerHeight}`);
        repair();
        armGesture();
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
  check();
  return { settled, check };
})();
