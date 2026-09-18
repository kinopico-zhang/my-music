// music-viewport-heal — 视口治疗的手法 (1.8.13, 医生是 music-viewport-doctor)。
// 病 (三轮回传实锤, iOS 18.7 独立模式): 键盘收起那一下, WebKit 把「还原高度」
// 记成 键盘弹起时的 innerHeight + 收起起手时的视口偏移 —— 两回都是 415+356
// (冻在 771/776), 而正确答案 812 = 415+397 (偏移本该是键盘的整个高度):
// 收起动画起手那一刻偏移已经被系统回滚了一截, 账就照那个半路值记走了。
// 翻面/meta 踢/键盘往返全试过无效 (1.8.11 回传), 刷新换文档也不行 (1.8.12:
// 归来还是矮的, 坏值跟着 webview 走), 只有划掉重开是真复位。所以 1.8.13 的
// 手法是「按住」: 键盘一收 (focusout) 就把视口偏移同步钉回键盘的整个高度,
// 一帧一帧跟系统的回滚抢, 让那笔记账记到满高上; 记好了 (innerHeight 回满)
// 就松手归位。松手那行的数字把成效记进回传: i812 = 按住了, i771 = 没按住。
"use strict";
/* global ViewportHUD */
/* exported ViewportHeal */

const ViewportHeal = (() => {
  let holding = false;

  // 键盘开着的判据 (与医生同款): 焦点在输入框 —— 按住期间焦点又回来了 =
  // 键盘其实没走 (用户点了下一个输入框), 撤手别搅局
  const typing = () => {
    const el = document.activeElement;
    return !!el && (el.tagName === "INPUT" || el.tagName === "TEXTAREA"
      || el.isContentEditable);
  };

  // 按住: 焦点一走 (键盘开始收) 同步把偏移钉到键盘整个高度 (overlap), 抢在
  // 收起动画起手之前; 之后每帧跟系统的回滚抢 (rAF 重设), innerHeight 回满
  // (账记对了) 或 1 秒上限就松手, 归位滚回 0 (1.8.7 lift 的活, 这里顺手做,
  // lift 见到 holding() 会避开)。全局事件层因此也要认这个旗。
  function holdDuringDismissal(overlap, full, note) {
    if (holding || overlap < 40 || overlap > 600) return;  // 不像键盘的高度
    holding = true;
    window.scrollTo(0, overlap);          // 同步先钉上, 抢在动画起手前
    ViewportHUD.say(`${note} 按住 y${overlap} 开工 i${window.innerHeight}`);
    const start = Date.now();
    const hold = () => {
      if (typing()) {                     // 键盘没走: 撤, 别跟避让滚动打架
        holding = false;
        ViewportHUD.say(`${note} 撤手 (焦点回来了) i${window.innerHeight}`);
        window.scrollTo(0, 0);
        return;
      }
      const healed = window.innerHeight >= full - 12;
      if (healed || Date.now() - start > 1000) {
        holding = false;
        const y = window.scrollY;         // 松手时的偏移: 397=按住了, 0=被系统抹了
        ViewportHUD.say(`${note} 松手 i${window.innerHeight} y${y}`
          + (healed ? " 回满" : ""));
        window.scrollTo(0, 0);
        return;
      }
      if (window.scrollY !== overlap) window.scrollTo(0, overlap);
      requestAnimationFrame(hold);
    };
    requestAnimationFrame(hold);
  }
  return { holdDuringDismissal, holding: () => holding };
})();
