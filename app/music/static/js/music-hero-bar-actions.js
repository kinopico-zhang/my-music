// music-hero-bar-actions — 收缩顶栏右侧的动作条 (1.8.45, 用户点名「五个按钮
// 收缩成 播放 和 … 两个按钮, 和封面放在一行右对齐; … 放在边上, 点击后
// 随机/下载/分享/删除 出来顶替它、把播放按钮往左边挤; 挤占了标题的空间,
// 标题和副标题就通过阴影过渡一下表示被遮住了」)。
// 1.8.46 换岗重做 (用户点名「控制按钮平移不要闪现, 要通过路径丝滑平移
// 过去」): 这套键由 heroBarMeasure/heroBarTravel 沿路径从操作行的键位
// 平移进顶栏槽位, 起飞位与行键逐像素重合 —— 换岗无闪。
// 1.8.46 三改: 收拢键按路程错峰走弧线飞进 …、到场前自淡, 途中两两
// 不叠 (tests/js/hero-bar-travel.test.mjs 按真机几何逐帧验过)。
"use strict";
/* global ICON_ACTION_MORE, ICON_ACTION_PLAY, ICON_ACTION_SHUFFLE, ICON_DOWNLOAD,
          ICON_ACTION_SHARE, ICON_ACTION_TRASH, wireHeroBarTapRecovery */
/* exported heroBarHTML, heroBarMeasure, heroBarTick, heroBarTravel,
          wireHeroBarActions */

const HERO_BAR_LABELS = {
  shuffle: "随机播放", download: "下载全部", share: "分享", delete: "删除列表",
};

function heroBarHTML(acts) {
  // 图标表在函数里取全局 (node 单测 require 本件时 ICON_ 尚不存在)
  const icons = {
    shuffle: ICON_ACTION_SHUFFLE, download: ICON_DOWNLOAD, share: ICON_ACTION_SHARE,
    delete: ICON_ACTION_TRASH,
  };
  const btn = (key, icon, label, on) =>
    `<button class="bar-btn${key === "play" ? " primary" : ""}" data-bar-act="${key}"` +
    ` title="${label}" aria-label="${label}"${on ? "" : " disabled"}>${icon}</button>`;
  const extras = Object.entries(acts).filter(([key]) => key !== "play")
    .map(([key, on]) => btn(key, icons[key], HERO_BAR_LABELS[key], !!on))
    .join("");
  return `<div class="hero-bar-actions"><span class="bar-sheen"` +
    ` aria-hidden="true"></span>${btn("play", ICON_ACTION_PLAY, "播放", !!acts.play)}` +
    (Object.keys(acts).length >= 3
      ? `<button class="bar-btn more" data-bar-more title="更多操作"` +
        ` aria-label="更多操作">${ICON_ACTION_MORE}</button>` +
        `<span class="bar-extras">${extras}</span>`
      : extras) +
    `</div>`;
}

function wireHeroBarActions(scope, handlers) {
  const head = scope.querySelector(".hero-head");
  const bar = head && head.querySelector(".hero-bar-actions");
  if (!bar || bar.dataset.wired) return;
  bar.dataset.wired = "1";
  bar.addEventListener("click", (event) => {
    const btn = event.target.closest("button");
    if (!btn) return;
    if (btn.dataset.barMore !== undefined) {
      head.classList.toggle("bar-open");
      return;
    }
    const run = handlers[btn.dataset.barAct];
    if (run) run();
    head.classList.remove("bar-open");      // 动作键: 干完活收回去
  });
  // 八改~十改: 惯性里被 iOS 吞掉的点按 (你报的「点 …/播放 停稳后第二下
  // 才灵」) 由独立小件接手 —— 根子是 iOS 把惯性中的点按整个吞给滚动器,
  // 页头上的监听救不了; 小件在滚动器外铺接点条 + document 级兜底,
  // 逻辑见 music-hero-bar-tap.js
  wireHeroBarTapRecovery(scope);
}

/** 进度回话 (hero-collapse 每帧调, back = 上滑往回飞): 到位 (p≥0.8, 与
    飞行结束同一刻) 才开闸可点, 同一刻也给层根挂 .bar-catch —— 接点条
    (滚动器外, 十改三轮) 这时才接点; 往回飞过 0.9 先收 … 菜单, 给收合
    动画留一截滚动余量。 */
function heroBarTick(head, p, back) {
  head.classList.toggle("bar-live", p >= 0.8);
  const pane = head.closest(".push-pane");
  if (pane) pane.classList.toggle("bar-catch", p >= 0.8);   // 接点条开闸
  if (back && p < 0.9) head.classList.remove("bar-open");
}

// 错峰到场的间隔 (行程 k 的份额): 后到的键追到离 … 不足一键宽时, 先到的
// 已淡尽 (配合 HERO_BAR_FADE) —— 谁也压不着谁
const HERO_BAR_STEP = 0.22;
// 到场前自淡的末段 (各自行程 u 的份额): 落进 … 那一刻正好淡尽
const HERO_BAR_FADE = 0.32;

/** 收拢键的错峰排程 + 弧线 (纯几何, node 单测直测): 按到 … 的路程排序,
    近的先到场 (arr 小); 各自带一条垂直于弦、向右下弓出的弧 (法向 × 弓高
    × sin(πe), 两端归零)。领头弓得最大、追兵越小 —— 加上错峰, 途中任意
    时刻两颗可见键不叠 (间距算法见 tests/js/hero-bar-travel)。 */
function heroBarPlanLanes(flyers) {
  const sink = flyers.filter((f) => f.fade);
  for (const f of sink) {
    f.len = Math.hypot(f.tx - f.fx, f.ty - f.fy) || 1;
  }
  sink.sort((a, b) => a.len - b.len);
  sink.forEach((f, r) => {
    f.arr = 1 - (sink.length - 1 - r) * HERO_BAR_STEP;
    const bow = Math.max(6, 24 - 6 * r);
    f.bx = ((f.fy - f.ty) / f.len) * bow;   // 弦的法向: 弦朝右上, 法向朝右下
    f.by = ((f.tx - f.fx) / f.len) * bow;
  });
}

/** 键在行程 k 处的中心位 (纯几何): 各键按自家 arr 错峰 —— u = k/arr,
    到场后钉在 … 上 (u 封顶 1); e 为 smoothstep 缓动; 弧线按 sin(πe)
    两端归零。返回 [x, y, u, e]。 */
function heroBarPointAt(f, k) {
  const u = Math.min(1, k / f.arr);
  const e = u * u * (3 - 2 * u);
  const arc = Math.sin(Math.PI * e);
  return [f.fx + (f.tx - f.fx) * e + f.bx * arc,
          f.fy + (f.ty - f.fy) * e + f.by * arc, u, e];
}

/** 量条的自然槽位 + 操作行键的起飞位 (heroCollect 的自然态里调): 先收 …
    菜单、摘净行内样式再量。播放键飞进自家槽; 有 … 键的页其余行键收拢进
    …, 没有的 (艺人) 各飞各的槽; 行键与条键按序配对 (两套同源同序)。顺手
    把收拢态的条宽量给 heroCollect (标题缩放让位用)。 */
function heroBarMeasure(head, rowButtons, headRect) {
  const info = { bar: null, barRowW: 0, moreBtn: null, flyers: [] };
  const bar = head.querySelector(".hero-bar-actions");
  if (!bar || !rowButtons.length) return info;
  info.bar = bar;
  head.classList.remove("bar-open");       // 量宽前先收菜单, 展开态不算数
  const btns = [...bar.querySelectorAll("button")];
  for (const btn of btns) { btn.style.transform = ""; btn.style.opacity = ""; }
  const center = (el) => {
    const r = el.getBoundingClientRect();
    return [r.left - headRect.left + r.width / 2,
            r.top - headRect.top + r.height / 2, r.width];
  };
  const play = bar.querySelector("[data-bar-act]");
  const more = bar.querySelector(".bar-btn.more");
  info.moreBtn = more;
  info.barRowW = play ? bar.clientWidth - play.offsetLeft : 0;
  const extras = more ? [...bar.querySelectorAll(".bar-extras button")]
    : btns.filter((btn) => btn !== play);
  const flyer = (el, fromEl, toEl, s1, fade) => {
    const [lx, ly, lw] = center(el);
    const [fx, fy, fw] = fromEl ? center(fromEl) : [lx, ly, lw];
    const [tx, ty] = center(toEl);
    const s0 = lw ? fw / lw : 1;
    info.flyers.push({ el, lx, ly, fx, fy, tx, ty, s0,
      s1: fade ? s0 : s1, fade, base: el.disabled ? 0.4 : 1,
      arr: 1, bx: 0, by: 0 });             // 错峰/弧线由 heroBarPlanLanes 排
  };
  flyer(play, rowButtons[0], play, 1, false);
  const sink = !!more;                     // 收拢进 … (艺人页没有 …, 各飞各的)
  extras.forEach((el, i) =>
    flyer(el, rowButtons[i + 1] || (sink ? more : el), sink ? more : el,
          1, sink));
  heroBarPlanLanes(info.flyers);           // 收拢键排错峰与弧线 (1.8.46 三改)
  return info;
}

/** 收缩行程里条键的路径动画 (heroApply 每帧调, smoothstep 缓动): 行程
    前段 (p 0.05→0.8) 播放键平移进自家槽, 收拢键沿弧线错峰飞进 …、到场
    前自淡, … 键从底下显形接住; p=0 或到位 (p≥0.8, 与 .bar-live 开闸同
    一刻) 行内全摘回纯 CSS —— 禁用态/… 开合都交还 CSS 管。 */
function heroBarTravel(ctrl, p) {
  if (!ctrl.bar) return;
  ctrl.head.classList.toggle("bar-fly", p > 0 && p < 0.8);
  const rest = () => {
    for (const f of ctrl.flyers) { f.el.style.transform = ""; f.el.style.opacity = ""; }
    if (ctrl.moreBtn) { ctrl.moreBtn.style.transform = ""; ctrl.moreBtn.style.opacity = ""; }
  };
  if (p <= 0) { rest(); return; }
  const t = Math.min(1, Math.max(0, (p - 0.05) / 0.75));
  if (t >= 1) { rest(); return; }          // 到位: 常态交还 CSS
  const k = t * t * (3 - 2 * t);
  for (const f of ctrl.flyers) {
    const [x, y, u, e] = heroBarPointAt(f, k);
    f.el.style.transform =
      `translate(${(x - f.lx).toFixed(2)}px, ${(y - f.ly).toFixed(2)}px)` +
      ` scale(${(f.s0 + (f.s1 - f.s0) * e).toFixed(4)})`;
    if (f.fade) {                          // 到场前自淡: 落进 … 那一刻淡尽
      const gone = Math.min(1, Math.max(0, (u - 1 + HERO_BAR_FADE) / HERO_BAR_FADE));
      f.el.style.opacity = (f.base * (1 - gone)).toFixed(3);
    }
  }
  if (ctrl.moreBtn) {                      // … 键: 头一颗落位前后显形接场
    const mo = Math.min(1, Math.max(0, (k - 0.2) / 0.8));
    ctrl.moreBtn.style.opacity = mo.toFixed(3);
    ctrl.moreBtn.style.transform = `scale(${(0.6 + 0.4 * mo).toFixed(3)})`;
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { HERO_BAR_STEP, HERO_BAR_FADE, heroBarPlanLanes,
                     heroBarPointAt };
}
