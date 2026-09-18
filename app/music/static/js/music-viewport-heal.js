// music-viewport-heal — 视口治疗的手法 (1.8.11, 医生是 music-viewport-doctor):
// 病: iOS 独立模式键盘一开 innerHeight 跟着缩, 收起后冻在矮值不回来
// (1.8.10 回传实锤 812→771, 差的 41 就是黑带)。WebKit 上游老病 (cordova
// #1575 都标了 webkit bug), scrollTo/摘焦点/visualViewport 监听/换 100%
// 高度链, 都是社区试过没用的路。验方 (cederhook, dev.to「Fixing the iOS
// standalone-PWA keyboard bug that shrinks your viewport for good」): 对
// 满视口高的元素做 display none→'' 翻面, 中间夹一次同步 reflow, 逼 WebKit
// 把视口高度重算回来; 翻面有一帧闪, 磨砂罩子罩严再动手。被翻的元素必须
// 真满高且在文档流里 (fixed 的不算), 所以翻 #main / body。本模块只有
// 「手」: 病情由医生判, 现场数字由 HUD 记 (每步成效都会落服务器日志)。
"use strict";
/* global ViewportHUD */
/* exported ViewportHeal */

const ViewportHeal = (() => {
  let veil = null;
  function ensureVeil() {       // 磨砂罩: 淡入罩严 → 动手 → 缓缓掀开
    if (veil) return;
    const sheet = document.createElement("style");
    sheet.textContent = "#kb-veil{position:fixed;inset:0;z-index:900;"
      + "opacity:0;pointer-events:none;background:rgba(20,18,21,.3);"
      + "backdrop-filter:blur(26px);transition:opacity .22s ease-out}";
    document.head.appendChild(sheet);
    veil = document.createElement("div");
    veil.id = "kb-veil";
    document.body.appendChild(veil);
  }

  // 翻面 (验方原样): 满高元素 display none→'' 夹同步 reflow, 滚位存还
  function flip(el, note) {
    if (!el) return;
    ensureVeil();
    veil.style.transition = "opacity .22s ease-out";
    veil.style.opacity = "1";
    setTimeout(() => {          // 罩子淡入 .22s, 严实了才动手
      const keep = el.style.display;
      const st = el.scrollTop;
      el.style.display = "none";
      void el.offsetHeight;     // 同步 reflow, 两步之间不绘制
      el.style.display = keep;
      el.scrollTop = st;
      ViewportHUD.say(`${note} 翻面 i${window.innerHeight}`);
      setTimeout(() => {        // 掀罩放慢半拍, 掩住回弹的顿挫
        veil.style.transition = "opacity .55s cubic-bezier(.32,.72,0,1)";
        veil.style.opacity = "0";
      }, 160);
    }, 240);
  }

  // 键盘往返: 手势上下文才唤得动键盘 (定时器唤不动, 1.8.10 回传实锤),
  // 真弹起来了稳一拍再收 —— 收键盘肯走完整动画, 高度才还得回来
  function roundtrip(probe, note) {
    if (!probe) return;
    const start = window.innerHeight;
    probe.focus();
    let waited = 0;
    const poll = setInterval(() => {
      waited += 100;
      if (start - window.innerHeight > 100) {  // 键盘真起来了: 稳一拍再收
        clearInterval(poll);
        setTimeout(() => {
          probe.blur();
          setTimeout(() => ViewportHUD.say(
            `${note} 键盘往返 i${window.innerHeight}`), 700);
        }, 300);
      } else if (waited > 1500) {              // 唤不动: 认了, 别干等
        clearInterval(poll);
        probe.blur();
        ViewportHUD.say(`${note} 键盘唤不动 i${window.innerHeight}`);
      }
    }, 100);
  }

  // meta 踢: 视口 meta 摘 80ms 再戴回去, 逼整块视口重算 (压箱底的大锤,
  // 有一瞬整页重排 —— 排在翻面之后, 前面成了它就不用出场)
  function metaKick(note) {
    const meta = document.querySelector('meta[name="viewport"]');
    if (!meta) return;
    const parent = meta.parentNode;
    const next = meta.nextElementSibling;
    meta.remove();
    setTimeout(() => {
      parent.insertBefore(meta, next);
      ViewportHUD.say(`${note} meta踢 i${window.innerHeight}`);
    }, 80);
  }

  return { flip, roundtrip, metaKick };
})();
