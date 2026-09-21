// music-hero-collapse — 封面收缩顶栏 (1.8.34, 用户点名「上划时封面边缩边
// 挪向左上角, 按钮挪到右上角, 到位钉成顶栏, 列表从底下滚过; 下滑对称还
// 原; 动画要细腻」): 专辑/播放列表/艺人页头包进 .hero-head 钉在推入层顶。
// 版式沿革: 1.8.40 两行 (短列表垫底补行程) → 1.8.42 左对齐 → 1.8.45 单行
// (标题缩放让位, 见 music-hero-bar-actions.js) → 1.8.46 行键沿路径换岗 +
// 停稳自动补程。实现口径 (细腻的根): sticky 钉住 + 布局高度恒定, 收缩全程
// 只写 transform/opacity (零重排), 滚动位置线性直驱; 行程 = 页头自然高 −
// 顶栏高 (music-push-panes.css); 目标位全按 padTop 量, 不写死。
"use strict";
/* global heroBarMeasure, heroBarTick, heroBarTravel */
/* exported bindHeroCollapse */

const HERO_MINI = 44;      // 收缩后封面边长 (标题文字跟在右边)
const HERO_BAR = 52;       // 顶栏单行内容高 = 封面 44 + 呼吸 8, 与 CSS 里
                           // calc(var(--top-clear) + 52px) 的 52 同源
const heroCtrls = new WeakMap();   // 滚动器 → 控制器 (重铺换元素, 监听只绑一次)
const heroPending = new Set();     // 每帧最多一次重绘 (滚动事件按帧节流)
const heroSnapTimers = new WeakMap();   // 滚动器 → 停稳补程的计时器 (七改)
const heroTouching = new WeakSet();     // 手指还按着的滚动器 (长按不动别补程)

/** 渲染完专辑/播放列表/艺人页后挂线: 量自然位, 当场对齐当前滚位 (重铺后
    滚位还在, 得原样还原)。页面结构不完整 (加载失败占位) 就不挂。 */
function bindHeroCollapse(scroller) {
  const ctrl = heroCollect(scroller);
  if (!ctrl) return;
  heroCtrls.set(scroller, ctrl);
  if (!scroller.dataset.heroCollapse) {
    scroller.dataset.heroCollapse = "1";
    scroller.addEventListener("scroll", () => heroSchedule(scroller),
                              { passive: true });
    // 手指按着 (长按/拖住) 不补程: 别从人家手底下把页面滚走
    for (const [ev, fn] of [["touchstart", "add"], ["touchend", "delete"],
                            ["touchcancel", "delete"]]) {
      scroller.addEventListener(ev, () => heroTouching[fn](scroller),
                                { passive: true });
    }
  }
  heroApply(scroller);
}

/** 滚动事件 → 每帧一次重绘 (passive, 不拦滚动); 停稳 (160ms 无滚动事件)
    自动补程 (七改, 你报的「…/播放键要点第二下」): 过半滑到底收齐、不到
    半弹回, 只管行程中间、深处翻列表不拽回 (九改); 手指按着不补; … 开着
    照补 (顶栏钉死不动)。 */
function heroSchedule(scroller) {
  if (heroPending.has(scroller)) return;
  heroPending.add(scroller);
  requestAnimationFrame(() => {
    heroPending.delete(scroller);
    heroApply(scroller);
  });
  clearTimeout(heroSnapTimers.get(scroller));
  heroSnapTimers.set(scroller, setTimeout(() => {
    heroSnapTimers.delete(scroller);
    const ctrl = heroCtrls.get(scroller);
    if (heroTouching.has(scroller) || !ctrl || !ctrl.head.isConnected) return;
    const t = scroller.scrollTop;         // 九改: 已收齐 (≥dist) = 人在翻列
    const target = t >= ctrl.dist - 2 ? t // 表, 不拽回列表顶; 只管行程中间
      : t > ctrl.dist / 2 ? ctrl.dist : 0;
    if (Math.abs(t - target) > 2) {
      scroller.scrollTo({ top: target, behavior: "smooth" });
    }
  }, 160));
}

/** 收集页头元素 + 量自然位 (FLIP: 目标位与自然位的差, 按滚动进度插值)。
    量之前先摘掉上一轮的行内样式 —— 重测时元素可能还带着变换。 */
function heroCollect(scroller) {
  const head = scroller.querySelector(".hero-head");
  const hero = head && head.querySelector(".album-hero, .artist-hero");
  const row = head && head.querySelector(".action-row");
  const cover = hero && hero.querySelector(".pl-cover-btn, img");
  const text = hero && hero.querySelector(".hero-txt");
  const title = text && text.querySelector("h2");
  const sub = text && text.querySelector(".hero-sub");
  if (!head || !hero || !row || !cover || !text || !title) return null;
  const rowButtons = [...row.querySelectorAll("button")];
  // 主/副标题各自搬 (1.8.42 左对齐): 分开量、分开落, 左缘都贴封面右边
  const movers = sub ? [title, sub] : [title];
  // 还走淡出的只剩封面以外的散块 (兜底, 现在三个页头都没有) 和封面钮里
  // 的换封面角标 (跟着缩到 44 会糊成一团)
  const fades = [...hero.children].filter((el) => el !== cover && el !== text);
  const hint = hero.querySelector(".cover-hint");
  if (hint) fades.push(hint);
  for (const el of [cover, ...movers, row, ...rowButtons, ...fades]) {
    el.style.transform = "";
    el.style.opacity = "";
    el.style.pointerEvents = "";
  }
  head.style.removeProperty("--hero-p");
  const headRect = head.getBoundingClientRect();
  const coverRect = cover.getBoundingClientRect();
  const titleRect = title.getBoundingClientRect();
  const subRect = sub ? sub.getBoundingClientRect() : null;
  const rowRect = row.getBoundingClientRect();
  const padTop = parseFloat(getComputedStyle(head).paddingTop) || 0;
  // 页头坐标 (sticky 钉住, 头不动, 全按头内相对位算 —— 层滑入途中的
  // transform 平移被头/子元素同吃, 相对位不受扰)
  const contentLeft = rowRect.left - headRect.left;        // 内容盒左缘 (row 块占满内容宽)
  const contentW = rowRect.width;
  // 顶栏动作条 (1.8.45 让位 + 1.8.46 路径换岗): 量收拢态条宽 (标题缩放
  // 让位用) + 条键的槽位/行键的起飞位, 见 music-hero-bar-actions.js
  const barInfo = heroBarMeasure(head, rowButtons, headRect);
  // 纱钉收拢簇左缘 (五改) + 接点条对位 (十改三轮): 量收拢态簇宽写在层根,
  // 纱 (头里) 和接点条 (层根, 滚动器外) 都按它对位; 无层兜底时写回头上
  (head.closest(".push-pane") || head)
    .style.setProperty("--bar-row-w", `${Math.ceil(barInfo.barRowW)}px`);
  // 两行的共用目标尺: 宽按更宽那条算 (都放得下), 高按整摞 (标题 + 副标题
  // + 中缝) 塞进 44; 天生放得下就不缩 (原字号进顶栏)
  const lineW = Math.max(titleRect.width, subRect ? subRect.width : 0);
  const stackH = subRect ? subRect.bottom - titleRect.top : titleRect.height;
  const textScale = Math.min(1,
    (contentW - HERO_MINI - 12 - barInfo.barRowW - 10) / Math.max(1, lineW),
    HERO_MINI / Math.max(1, stackH));
  // 落点: 两条线左缘都对齐封面右边 12px, 整摞在上行 44 里垂直居中
  const textX = contentLeft + HERO_MINI + 12;
  const stackY = padTop + (HERO_MINI - stackH * textScale) / 2;
  const ctrl = {
    head, cover, movers, row, rowButtons, fades, title, sub,
    width: scroller.clientWidth,                          // 转屏/改窗宽后懒重测的哨兵
    dist: head.offsetHeight - padTop - HERO_BAR,          // 收缩行程
    p: undefined,
    coverTx: contentLeft - (coverRect.left - headRect.left),   // 封面左上角 → 内容盒左上角
    coverTy: padTop - (coverRect.top - headRect.top),
    scale: HERO_MINI / coverRect.width,                   // 44px (origin 左上, 一边缩一边靠角)
    // 标题/副标题各自的目标位: 左缘同贴封面右边, 副标题顶 = 摞顶 + 原缝缩放
    titleTx: textX - (titleRect.left - headRect.left),
    titleTy: stackY - (titleRect.top - headRect.top),
    subTx: subRect ? textX - (subRect.left - headRect.left) : 0,
    subTy: subRect
      ? stackY + (subRect.top - titleRect.top) * textScale
        - (subRect.top - headRect.top) : 0,
    textScale,
    ...barInfo,
  };
  ctrl.cover.style.transformOrigin = "0 0";
  for (const el of movers) el.style.transformOrigin = "0 0";
  // 短列表补行程 (1.8.40): 滚到底也够不着行程的页, 差多少垫多少底部空隙
  // (--hero-extra, 加在船坞让位之上)。量法先归零再「补一步量一步」收敛:
  // scrollHeight 会被 clientHeight 钳住, 一步量不全 (两首歌的歌单曾卡半路)
  scroller.style.setProperty("--hero-extra", "0px");
  let extra = 0;
  for (let i = 0; i < 4; i++) {
    const shortfall = ctrl.dist - (scroller.scrollHeight - scroller.clientHeight);
    if (shortfall <= 0) break;
    extra += shortfall;
    scroller.style.setProperty("--hero-extra", `${Math.ceil(extra)}px`);
  }
  return ctrl.dist > 24 ? ctrl : null;   // 页头太矮收不动: 不挂, 行为照旧
}

/** 按滚动进度 p (0 自然位 → 1 顶栏位) 插值写样式。p 直驱不缓动 —— 手指
    拖到哪跟到哪; 小字/角标 0.6 行程内先走完, 血线 (CSS, --hero-p) 收尾。 */
function heroApply(scroller) {
  let ctrl = heroCtrls.get(scroller);
  if (!ctrl) return;
  if (!ctrl.head.isConnected || ctrl.width !== scroller.clientWidth) {
    ctrl = heroCollect(scroller);      // 转屏/改窗宽: 重新量 (滚位不动, 原样对齐)
    if (!ctrl) { heroCtrls.delete(scroller); return; }
    heroCtrls.set(scroller, ctrl);
  }
  const p = ctrl.dist > 0
    ? Math.min(1, Math.max(0, scroller.scrollTop / ctrl.dist)) : 0;
  if (p === ctrl.p) return;
  heroBarTick(ctrl.head, p, p < ctrl.p);  // 开闸; 上滑往回飞才收 … 菜单
  ctrl.p = p;
  heroBarTravel(ctrl, p);                 // 条键沿路径平移换岗 (1.8.46)
  if (p <= 0) {                        // 自然位: 行内样式全摘, 回纯 CSS
    ctrl.head.style.removeProperty("--hero-p");
    for (const el of [ctrl.cover, ...ctrl.movers, ctrl.row,
                      ...ctrl.rowButtons, ...ctrl.fades]) {
      el.style.transform = "";
      el.style.opacity = "";
      el.style.pointerEvents = "";
    }
    return;
  }
  ctrl.head.style.setProperty("--hero-p", p.toFixed(3));
  ctrl.cover.style.transform =
    `translate(${(ctrl.coverTx * p).toFixed(2)}px, ${(ctrl.coverTy * p).toFixed(2)}px)` +
    ` scale(${(1 - p * (1 - ctrl.scale)).toFixed(4)})`;
  const textMove = (el, tx, ty) => {   // 两行各自搬: 同尺缩放, 左缘都贴封面右边
    el.style.transform =
      `translate(${(tx * p).toFixed(2)}px, ${(ty * p).toFixed(2)}px)` +
      ` scale(${(1 - p * (1 - ctrl.textScale)).toFixed(4)})`;
  };
  textMove(ctrl.title, ctrl.titleTx, ctrl.titleTy);
  if (ctrl.sub) textMove(ctrl.sub, ctrl.subTx, ctrl.subTy);
  // 操作行的键一进收缩就藏 (1.8.46): 顶栏那套从它们的键位起飞接班,
  // 起飞位逐像素重合 —— 两套不同屏; 藏着的键也不再截点
  for (const btn of ctrl.rowButtons) {
    btn.style.opacity = "0";
    btn.style.pointerEvents = "none";
  }
  for (const el of ctrl.fades) {       // 小字/角标先走完 (0.6 行程), 上飘一点, 淡尽不再挡点
    el.style.opacity = String(Math.max(0, 1 - p * 1.7));
    el.style.transform = `translateY(${(-18 * p).toFixed(2)}px)`;
    el.style.pointerEvents = p > 0.35 ? "none" : "";
  }
}
