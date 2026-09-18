// music-pane-swipe — My Music 推入层右划返回手势: 面板任意位置起手, 横竖先分家
// (竖向交还滚动), 拖过三分之一或带甩劲松手就收层, 否则弹回。
// 拆自 music-push-panes.js (1.8.6: 文件超 200 行按域再拆); 1.8.18 加了
// 分页容器的触摸看门 (最左页右划让回右划返回, 用户点名 —— 见 bindPaneSwipe)。
"use strict";
/* global paneMotion, pushStack, removePaneWhenSettled, saveLastRoute,
          unlockRootScroll */
/* exported bindPaneSwipe */

/** 右划返回: 面板任意位置起手, 横竖先分家 (竖向交还滚动); 拖过三分之一
    或带甩劲松手就收层, 否则弹回。收层是纯视图收层, 不碰浏览器历史
    (一个地址走全程)。
    左缘的归属按环境各安其位: 主屏图标打开 (standalone) 没有系统手势,
    整条左缘 (含屏幕最边) 都是这里的; 浏览器里苹果把最边上一小条握在
    系统手里 (整页截图滑走, 网页收不到触摸, preventDefault/Navigation
    API 都掐不动 —— 试过两轮, 别再试), 那一条之外的左缘归这里。 */
function bindPaneSwipe(pane) {
  // 分页容器的手势分家 (搜索四子页 1.8.3 / 设置四子页 1.8.17) 分两层:
  // 起手在页里的横拖归原生切页, 不归右划返回 —— 但 1.8.18 用户点名
  // 「最左页右划要退出整个设置/搜索」: 原生平移会把横拖整个抢走
  // (pointercancel), 右划返回死在半路。所以在最左页 (scrollLeft 0)
  // 加一层触摸看门: 右向坐实 (过 6px, 抢在浏览器自家 slop 之前) 的
  // 那一下 preventDefault 掐掉原生平移 —— 手势让回下面这层右划返回;
  // 左向 (切去第二页)/竖向 (滚页)/不在最左页, 看门不掺和, 照旧全交原生
  let guardId = null;       // 看门正盯的触摸; null = 没在看
  let guardStartX = 0, guardStartY = 0;
  let guardRight = false;   // 右向坐实后这个触摸的 touchmove 全掐
  pane.addEventListener("touchstart", (event) => {
    if (event.touches.length !== 1) { guardId = null; return; }
    const pager = event.target.closest("#search-body.paged, #settings-body");
    if (!pager || pager.scrollLeft > 0) { guardId = null; return; }
    guardId = event.touches[0].identifier;
    guardStartX = event.touches[0].clientX;
    guardStartY = event.touches[0].clientY;
    guardRight = false;
  }, { passive: true });
  pane.addEventListener("touchmove", (event) => {
    if (guardId === null) return;
    const touch = [...event.changedTouches].find(
      (item) => item.identifier === guardId);
    if (!touch) return;
    if (guardRight) { event.preventDefault(); return; }   // 右向: 归右划返回
    const dx = touch.clientX - guardStartX;
    const dy = touch.clientY - guardStartY;
    if (Math.abs(dx) < 6 && Math.abs(dy) < 6) return;
    guardRight = dx > 0 && Math.abs(dx) > Math.abs(dy);
    if (guardRight) event.preventDefault();
  }, { passive: false });
  pane.addEventListener("touchend", (event) => {
    if (guardId !== null && [...event.changedTouches].some(
      (item) => item.identifier === guardId)) {
      guardId = null;      // 这场看完, 下一场重新认方向
    }
  });
  pane.addEventListener("pointerdown", (event) => {
    if (event.pointerType === "mouse" && event.button !== 0) return;
    // 滚到别的页上照旧归原生切页 (鼠标拖不动 snap 容器, 最左页不用看门
    // 也能走下面这条右划返回)
    const pager = event.target.closest("#search-body.paged, #settings-body");
    if (pager && pager.scrollLeft > 0) return;
    const startX = event.clientX;
    const startY = event.clientY;
    let horizontal = false;
    let decided = false;
    let lastX = startX;
    let lastT = event.timeStamp;
    const signals = new AbortController();        // 拆掉 cleanup ↔ 手柄的互相引用
    const cleanup = () => signals.abort();
    const move = (ev) => {
      const dx = ev.clientX - startX;
      const dy = ev.clientY - startY;
      if (!decided) {
        if (Math.abs(dx) < 8 && Math.abs(dy) < 8) return;
        decided = true;
        horizontal = dx > 0 && Math.abs(dx) > Math.abs(dy);
        if (!horizontal) { cleanup(); return; }   // 竖向: 交还滚动
        // 横向坐实这一下就把焦点摘走 (键盘从拖动第一下就开始收, 和原生
        // 返回手势一个脾气) —— 别等松手收层才被动失焦: 1.8.9 录屏逐帧
        // 量出, 键盘收起动画走到半路时移除聚焦过的层, 手机会把「页面该
        // 多高」忘在半路, 底部从此一条黑带 (早收早稳, 收层那步就撞不上)
        if (pane.contains(document.activeElement)) document.activeElement.blur();
        pane.setPointerCapture(ev.pointerId);
        pane.style.transition = "none";
      }
      paneMotion();                 // 拖动中: 气泡磨砂持续暂撤 (每下续期)
      pane.style.transform = `translateX(${Math.max(0, dx)}px)`;
      lastX = ev.clientX;
      lastT = ev.timeStamp;
    };
    const end = (ev) => {
      cleanup();
      if (!horizontal) return;      // 点按/竖向: 不归这里管
      const dx = Math.max(0, ev.clientX - startX);
      const width = pane.offsetWidth || 1;
      const flick = ev.timeStamp - lastT < 100 && lastX - startX > 40;
      pane.style.transition = "";
      pane.style.transform = "";
      if (dx <= width / 3 && !flick) {
        paneMotion();               // 弹回也是一段运动, 磨砂照旧暂撤
        return;                     // 没拖够: 弹回 (.open 的 0)
      }
      paneMotion();                 // 滑出途中气泡暂撤磨砂 (重影对策)
      pane.classList.remove("open");              // 从当前位置滑出
      pushStack.pop();
      // 焦点在本层 (如搜索输入框): 摘走再滑出, 键盘跟手收下 (同 closePushStack;
      // 起手那一处先摘过的话这里就是空跑)
      if (pane.contains(document.activeElement)) document.activeElement.blur();
      removePaneWhenSettled(pane);   // 键盘收稳才移除 DOM (1.8.9, 见定义处)
      if (!pushStack.length) unlockRootScroll();
      saveLastRoute();              // 手势收层也记停在哪页 (开局回跳)
    };
    const cancel = () => {
      cleanup();
      if (horizontal) {
        paneMotion();               // 弹回也是一段运动, 磨砂照旧暂撤
        pane.style.transition = "";
        pane.style.transform = "";
      }
    };
    pane.addEventListener("pointermove", move, { signal: signals.signal });
    pane.addEventListener("pointerup", end, { signal: signals.signal });
    pane.addEventListener("pointercancel", cancel, { signal: signals.signal });
  });
}
