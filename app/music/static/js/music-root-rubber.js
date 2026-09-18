// music-root-rubber — My Music 根层右划到头的橡皮筋 (1.8.23, 用户点名):
// 主页是唯一根层, 右划到底也没有可退的层 —— 手势别落空: 内容跟手阻尼让位
// (越拉越费劲, 拉到天边也只让 140px), 松手带着回弹曲线弹回原位, 底部顺带
// 一条「到头了」。与推入层右划返回 (music-pane-swipe) / 气泡右划收层
// (music-bubble-swipe) 分好地盘: 有层盖着时 #main 收不到触摸, 这里只在
// 根层 (pushStack 空) 生效。左滑删除的行横拖归它自己 (右划若正开着删除
// 钮, 是「收起删除钮」), 起手在那行上的不掺和。
"use strict";
/* global $, paneMotion, pushStack, toast */
/* exported bindRootRubber */

const ROOT_RUBBER_MAX = 140;    // 阻尼渐近上限 (px): 拉得越远每像素换的越少

/** 阻尼让位 (iOS 橡皮筋同族公式): dx 无限大也让位无限逼近 140px。 */
function rootRubberOffset(dx) {
  return ROOT_RUBBER_MAX * (1 - 1 / (dx / ROOT_RUBBER_MAX + 1));
}

/** 根层右划: 横竖先分家 (竖向交还滚动, 左向归左滑删除/别的), 右向坐实才
    接管。移动的是 #main (整列内容) —— #root-view 在 main 里, main 是
    overflow-y:auto 的滚动器, 子元素横移会把 main 撑出横向滚动条, 移
    main 自己则由固定壳 (html/body overflow:hidden) 裁掉, 干净。
    松手: 回弹曲线弹回 (过冲一点再稳住, 橡皮筋的「弹」), 拉过 36px 出
    「到头了」; 拖动中 paneMotion() 续期 —— 变换层从气泡/船坞键底下扫过
    是 WebKit 磨砂重影的配方, 运动期换实底 (推入层同款)。 */
function bindRootRubber() {
  const main = $("#main");
  let swallowClick = false;      // 拖过的松手 click 吞掉 (别开播/别进列表)

  main.addEventListener("pointerdown", (event) => {
    swallowClick = false;        // 新按下 = 上一手势翻篇 (触屏拖完不补 click)
    if (pushStack.length) return;                     // 有层盖着: 轮不到根层
    if (event.pointerType === "mouse" && event.button !== 0) return;
    const wrap = event.target.closest(".swipe-wrap");
    if (wrap && wrap.classList.contains("revealed")) return;  // 删除钮开着: 归它
    const startX = event.clientX;
    const startY = event.clientY;
    let horizontal = false;
    let decided = false;
    const signals = new AbortController();        // 拆掉 cleanup ↔ 手柄的互相引用
    const cleanup = () => signals.abort();
    const move = (ev) => {
      const dx = ev.clientX - startX;
      const dy = ev.clientY - startY;
      if (!decided) {
        if (Math.abs(dx) < 8 && Math.abs(dy) < 8) return;
        decided = true;
        horizontal = dx > 0 && Math.abs(dx) > Math.abs(dy);
        if (!horizontal) { cleanup(); return; }   // 竖向/左向: 交还
        try {
          main.setPointerCapture(ev.pointerId);   // 拖出窗口也收得到 up
        } catch (_error) { /* 抓不到也能拖; 出界松手由下一次按下兜底 */ }
        main.style.transition = "none";           // 跟手期不走过渡
      }
      paneMotion();                 // 拖动中: 磨砂暂撤续期 (重影对策)
      main.style.transform
        = `translateX(${rootRubberOffset(Math.max(0, dx))}px)`;
    };
    const bounce = () => {
      main.style.transition = "transform .45s cubic-bezier(.3, 1.3, .4, 1)";
      main.style.transform = "";
      paneMotion();                 // 弹回这段也是运动, 磨砂暂撤罩满全程
    };
    const end = (ev) => {
      cleanup();
      if (!horizontal) return;
      swallowClick = true;          // 拖过的松手 click 吞掉 (不开播不进页)
      if (ev.clientX - startX >= 36) toast("到头了");
      bounce();
    };
    const cancel = () => {
      cleanup();
      if (horizontal) bounce();     // 浏览器接管 (滚动等): 原样弹回, 不提示
    };
    main.addEventListener("pointermove", move, { signal: signals.signal });
    main.addEventListener("pointerup", end, { signal: signals.signal });
    main.addEventListener("pointercancel", cancel, { signal: signals.signal });
  });
  // 拖完尾随的 click (鼠标拖拽松手会补发): 吞掉, 别把歌开了
  main.addEventListener("click", (event) => {
    if (!swallowClick) return;
    swallowClick = false;
    event.stopPropagation();
    event.preventDefault();
  }, true);
}
