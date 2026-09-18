// music-swipe-delete — My Music 列表行左滑露出删除 (iOS 同款): 拖拽揭示/松手判定/尾随 click 吞除。
// 拆自 music.js (结构化重构), 1.8.23 改款 (用户报「左滑时左边的信息不见了」):
// 早先行整体左移、删除钮从底下露出来 —— 封面跟着行左移被左缘裁掉。现在行
// 原地不动, 删除钮从右缘滑上来盖在行尾内容上 (同色纱跟着延伸, 见同名 css)。
"use strict";
/* exported bindSwipeDelete */

// ------------------------------------------------------------ 左滑删除
// .swipe-wrap 的行左滑露出「删除」钮 (iOS 同款): 横向拖动跟手, 竖向让给
// 滚动 (行 touch-action: pan-y); 松手过半开/不过半弹回。一次只开一行,
// 点别处/滚动/滑另一行都收起, 开着的行点一下也是收起 (不进页不开播)。
// 与长按菜单共存: 长按计时器移动超 10px 自动作废, 这里 8px 内不接管。
// 只认左移: 右移是推入层返回手势 (bindPaneSwipe) 和 iOS 系统边缘返回的
// 地盘, 这里一抢 (setPointerCapture) 层就跟到一半被掐弹回 —— 1.7.0
// 后遗症, 用户点名"返回一半就取消"。根层右划另有橡皮筋 (music-root-rubber,
// 1.8.23): 删除钮开着的行 (revealed) 它也让开。
// 尾随 click 的吞法吸取长按菜单的教训 (3f5cd5f): 标记在新按下时清,
// 松手后设备不补发 click 也不至于粘住吞掉下一次真点击。
const SWIPE_REVEAL = 72;             // 删除钮宽度 (px)
let swipeOpenWrap = null;            // 开着的行 (null = 全收)
let swipeDrag = null;                // 拖拽进行中 {wrap,row,startX,startY,base,horizontal,offset,moved}
let swipeSuppressClick = false;      // 松手前横移过: 尾随的 click 吞掉

/** 移删除钮 + 顺手挂 revealed (1.8.23 改款: 行不动, 钮从右缘滑上来)。
    x=0 钮藏在右缘外, x=-72 全开 (可多拖 24px 橡皮筋); --veil (0→1)
    喂纱的浓度 = 拖开的比例, 拖多少显多少。revealed 挂在 wrap 一级
    (纱/把手都是 wrap 的家当)。 */
function setSwipeTransform(wrap, x) {
  const del = wrap.querySelector(".swipe-del");
  if (del) del.style.transform = `translateX(${SWIPE_REVEAL + x}px)`;
  wrap.style.setProperty("--veil", String(Math.min(1, -x / SWIPE_REVEAL)));
  wrap.classList.toggle("revealed", x < 0);
}

function closeSwipeRow() {
  if (!swipeOpenWrap) return;
  if (swipeOpenWrap.isConnected && swipeOpenWrap.querySelector(".swipe-del")) {
    setSwipeTransform(swipeOpenWrap, 0);
  }
  swipeOpenWrap = null;
}

// 任何滚动 (列表/推入层/页面) 都把开着的行收起来 —— 绑在 document 捕获层,
// scroll 不冒泡, 绑容器收不到祖先 (推入层) 的滚动。
document.addEventListener("scroll", closeSwipeRow, true);

function bindSwipeDelete(container, onDelete) {
  container.addEventListener("pointerdown", (event) => {
    swipeSuppressClick = false;                  // 新按下 = 上一手势翻篇
    if (swipeDrag) {                             // 出界松手没收到 up: 兜底归位
      swipeDrag.wrap.classList.remove("swiping");
      setSwipeTransform(swipeDrag.wrap, swipeDrag.base);
      swipeDrag = null;
    }
    const wrap = event.target.closest(".swipe-wrap");
    if (!wrap || !wrap.contains(event.target)) { closeSwipeRow(); return; }
    if (event.target.closest(".swipe-del")) return;    // 删除钮: 点按即删
    if (swipeOpenWrap && swipeOpenWrap !== wrap) closeSwipeRow();
    swipeDrag = { wrap, row: wrap.firstElementChild,
                  startX: event.clientX, startY: event.clientY,
                  base: swipeOpenWrap === wrap ? -SWIPE_REVEAL : 0,
                  horizontal: null, offset: 0, moved: false };
  });
  container.addEventListener("pointermove", (event) => {
    if (!swipeDrag) return;
    const dx = event.clientX - swipeDrag.startX;
    const dy = event.clientY - swipeDrag.startY;
    if (swipeDrag.horizontal === null) {
      if (Math.abs(dx) < 8 && Math.abs(dy) < 8) return;
      // 只认左移; 右移/竖移都撒手 (右移归推入层返回手势, 竖移归滚动)
      swipeDrag.horizontal = dx < 0 && Math.abs(dx) > Math.abs(dy);
      if (!swipeDrag.horizontal) { swipeDrag = null; return; }
      swipeDrag.wrap.classList.add("swiping");   // 拖动跟手, 松手才交给过渡
      try {
        swipeDrag.row.setPointerCapture(event.pointerId);  // 鼠标拖出容器也能收到 up
      } catch (_error) { /* 抓不到也能拖; 出界松手由下一次按下兜底 */ }
    }
    swipeDrag.moved = true;
    // 左移露钮 (可多拖 24px 橡皮筋), 右移最多推回 0
    swipeDrag.offset = Math.min(0, Math.max(-SWIPE_REVEAL - 24,
                                            swipeDrag.base + dx));
    setSwipeTransform(swipeDrag.wrap, swipeDrag.offset);
  });
  const settle = (cancelled) => {
    const drag = swipeDrag;
    swipeDrag = null;
    if (!drag || !drag.horizontal) return;
    drag.wrap.classList.remove("swiping");       // 回位/定住交给 CSS 过渡
    if (cancelled) {                              // 浏览器接管手势 (滚动等)
      setSwipeTransform(drag.wrap, drag.base);
      if (drag.base) swipeOpenWrap = drag.wrap;
      return;
    }
    swipeSuppressClick = drag.moved;              // 拖过的松手 click 不开播
    if (drag.offset < -SWIPE_REVEAL / 2) {
      setSwipeTransform(drag.wrap, -SWIPE_REVEAL);
      swipeOpenWrap = drag.wrap;
    } else {
      setSwipeTransform(drag.wrap, 0);
      if (swipeOpenWrap === drag.wrap) swipeOpenWrap = null;
    }
  };
  container.addEventListener("pointerup", () => settle(false));
  container.addEventListener("pointercancel", () => settle(true));
  // 捕获层吃两类点击: 删除钮 (不再冒泡给行点击/开播) 和滑完松手/开着的行
  // 上的尾随 click; 冒泡层的 bindTrackLists/导航因此看不见这两下。
  container.addEventListener("click", async (event) => {
    if (swipeSuppressClick) {
      swipeSuppressClick = false;
      event.stopPropagation();
      event.preventDefault();
      return;
    }
    const del = event.target.closest(".swipe-del");
    if (del) {
      event.stopPropagation();
      event.preventDefault();
      const wrap = del.closest(".swipe-wrap");
      swipeOpenWrap = null;
      await onDelete(wrap);
      return;
    }
    if (swipeOpenWrap && swipeOpenWrap.contains(event.target)) {
      closeSwipeRow();                            // 开着的行点一下 = 收起
      event.stopPropagation();
      event.preventDefault();
    }
  }, true);
}

