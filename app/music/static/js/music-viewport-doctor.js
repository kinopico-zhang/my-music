// music-viewport-doctor — My Music 视口体检 (1.8.11): 盯着「页面高度」本身。
// 病 (1.8.10 回传实锤, iOS 18 独立模式): 键盘弹起 innerHeight 跟着缩
// (812→415), 收起后冻在矮值 (771, 差的 41 就是黑带) 不回来 —— WebKit 老病
// (cordova #1575 同族); 滚位/偏移两味 1.8.7 已治好。本模块管「诊断 + 调度」:
//   ① 判据: 键盘开着 = 焦点在输入框 (iOS 18 独立模式里 vv 与 inner 永远
//      相等, 互比是空转 —— 1.8.10 误诊过还抢了用户焦点; 实锤后闩住不重复喊);
//   ② 治疗 (手法在 music-viewport-heal.js): 收键盘 +140ms 早治 (满高元素
//      翻面, 社区验方), 仍矮 0.7s 实锤冻矮 → 修复阶梯 (翻面→身体翻面→
//      [手势]键盘往返→meta 踢);
//   ③ 体检窗 (music-viewport-hud.js 管「说」): 现场数字 + 回传服务器日志。
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
  let aRepairs = 0;                    // 自动档修复次数 (回满清零)
  let gRepairs = 0;                    // 手势档修复次数
  let lastRepair = 0;
  let gestureArmed = false;
  let said = [];                       // 流水留底 (拼进现场数字最后几行)
  function stat() {
    return [
      "My Music 1.8.11 视口体检 (现场已回传)",
      `screen ${window.screen.width}x${window.screen.height} dpr ${window.devicePixelRatio}`,
      `inner ${window.innerHeight} / 满高 ${full} (差 ${full - window.innerHeight})`,
      `vv ${vv ? `${Math.round(vv.height)} top ${Math.round(vv.offsetTop)}` : "无"}`,
      `scrollY ${window.scrollY} · 焦点 ${typing() ? "输入框" : "无"}`,
      `已修 自动${aRepairs} 手势${gRepairs}`,
      "点这扇窗任意处 = 立即修复",
      "",
      ...said,
    ].join("\n");
  }
  function say(line) {
    said.push(`${new Date().toTimeString().slice(0, 8)} ${line}`);
    said = said.slice(-9);
    ViewportHUD.say(line);             // HUD: 屏显刷新 + 排进回传发件箱
  }

  // 修复阶梯 (手法在 heal): ① #main 翻面 ② body 翻面 ③ 键盘往返 —— 只有
  // 手势唤得动键盘 (1.8.10 回传实锤), 自动档跳过 ④ meta 踢。各档间隔够
  // 日志看清每一步的成效; 点体检窗 = force: 不计次只防连击。
  function repair(opts) {
    const gesture = !!(opts && opts.gesture);
    const force = !!(opts && opts.force);
    if (!patient() || !sick()) return;
    const now = Date.now();
    if (now - lastRepair < (force ? 1500 : 2500)) return;
    if (!force && (gesture ? gRepairs >= 3 : aRepairs >= 2)) return;
    if (gesture) gRepairs += 1; else aRepairs += 1;
    lastRepair = now;
    const tag = `${gesture ? "手势" : "自动"}#${gesture ? gRepairs : aRepairs}`;
    say(`修复 ${tag} 开工 i${window.innerHeight} 差${full - window.innerHeight}`);
    ViewportHUD.send();                // 修复是大事, 不攒批当场送
    ViewportHeal.flip(document.getElementById("main"), tag);
    setTimeout(() => { if (sick()) ViewportHeal.flip(document.body, `${tag}②`); }, 1400);
    if (gesture) setTimeout(() => {
      if (sick()) ViewportHeal.roundtrip(probe, `${tag}③`);
    }, 2800);
    setTimeout(() => { if (sick()) ViewportHeal.metaKick(`${tag}④`); }, 4400);
  }
  function armGesture() {
    if (gestureArmed) return;
    gestureArmed = true;
    addEventListener("pointerdown", () => {  // 定时器没手势未必唤得动键盘
      gestureArmed = false; repair({ gesture: true });
    }, { once: true });
  }
  ViewportHUD.wire({ stat, repair, full: () => full });

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
      aRepairs = 0;
      gRepairs = 0;
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
  document.addEventListener("focusout", (event) => {
    say("focusout");
    // 早治 (验方的时机): 收键盘动画里就翻面, 黑带来不及露头; 动画本来就
    // 干净的 (值回满高) sick() 拦住, 罩子都不亮。探针自己的收起不掺和
    // (那是键盘往返在干活, 别去搅局)。
    if (event.target && event.target.id !== "kb-repair") {
      setTimeout(() => { if (!typing() && sick())
        ViewportHeal.flip(document.getElementById("main"), "收尾"); }, 140);
      setTimeout(() => { if (!typing() && sick())
        ViewportHeal.flip(document.getElementById("main"), "收尾2"); }, 450);
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
  check();
  return { settled, check };
})();
