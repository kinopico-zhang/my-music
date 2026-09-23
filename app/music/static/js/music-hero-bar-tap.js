// music-hero-bar-tap — 收缩顶栏被吞点按的修法 (1.8.46 十改三轮, 你报的
// 「惯性里点 播放/… 只是把列表停住, 停稳后第二下才灵, 两轮修完还是不行,
// 感觉下面的列表把点击按钮事件劫持了」): 感觉是对的 —— iOS 把惯性中的
// 点按整个吞给滚动器, touchstart 压根不派给滚动器内容 (SO 49468413:
// 惯性期间约 500ms 不派), 挂在页头上/提到 document 上的补发都收不到,
// touch-action 也拦不住 (二轮白改)。船坞键从没这毛病, 因为它在滚动器
// 外面 —— 这轮照方抓药: 层根 (滚动器外) 铺一条接点条, 开闸 (p≥0.8,
// heroBarTick 给层挂 .bar-catch) 后正好罩住收拢簇, 点按按矩形认出底下
// 的真键补一发 click —— 惯性里也灵。接点区带 touch-action: none (点按
// 不当滚动手势, click 必来); 桌面端 CSS 摘了接点权 (悬停归真键)。
// 配套留着 document 级兜底补发 (pointer+touch 双通道, 同一下只记一回):
// 接点条没罩住的场合 (操作行/开 … 后的额外键/还在飞的键) 靠它, 认键按
// 落点现场查 elementsFromPoint 只认视觉最上层那个层的页头; 真点按 20ms
// 内必到 (来了就撤记, 不会重发)。
"use strict";
/* global jellyButton */
/* exported heroTapRectBtn, wireHeroBarTapRecovery */

/** 在条里按矩形认键 (rect 跟着飞行变换走, 淡尽的键不抢, 四边放宽 8px
    容停滚瞬间的错位)。接点条和兜底补发共用这一段认键。 */
function heroTapRectBtn(bar, x, y) {
  for (const b of bar.querySelectorAll("button")) {
    if (parseFloat(getComputedStyle(b).opacity) < 0.3) continue;
    const r = b.getBoundingClientRect();
    if (x >= r.left - 8 && x <= r.right + 8
        && y >= r.top - 8 && y <= r.bottom + 8) return b;
  }
  return null;
}

/** 按手指落点认键 (只认视觉最上层那个层里的页头): 开着闸的键/操作行的
    键/封面角标就是最上层元素本身; 接点条罩着/还在飞的键 pe:none 穿透,
    退回在其条里按矩形认。最上层不在任何层里 (遮罩/船坞) 不抢。 */
function heroTapBtnAt(x, y) {
  const top = document.elementsFromPoint(x, y)[0];
  const pane = top && top.closest ? top.closest(".push-pane") : null;
  const head = pane ? pane.querySelector(".hero-head") : null;
  if (!head) return null;
  const direct = top.closest("button");
  if (direct && head.contains(direct)) return direct;
  const bar = head.querySelector(".hero-bar-actions");
  return bar ? heroTapRectBtn(bar, x, y) : null;
}

let heroTapWired = false;                // document 级兜底监听只挂一回

/** 在层根 (滚动器外) 铺接点条 + 给整个应用挂被吞点按的兜底补发
    (wireHeroBarActions 每回接线都调; 接点条一层只铺一条)。 */
function wireHeroBarTapRecovery(scope) {
  const pane = scope.closest(".push-pane");
  if (pane && !pane.querySelector(".hero-bar-catch")) {
    const strip = document.createElement("div");
    strip.className = "hero-bar-catch";
    strip.innerHTML = "<div><span></span></div>";  // 列壳 (860 列) + 接点区
    strip.addEventListener("click", (e) => {
      const head = pane.querySelector(".hero-head");
      const bar = head && head.querySelector(".hero-bar-actions");
      const btn = bar && heroTapRectBtn(bar, e.clientX, e.clientY);
      if (btn) { jellyButton(btn); btn.click(); }   // 果冻 + 冒泡照常分派
    });
    pane.appendChild(strip);            // 铺在层根: 滚动器外, 不被惯性劫持
  }
  if (heroTapWired) return;
  heroTapWired = true;
  let eaten = null, ex = 0, ey = 0, tries = 0;
  const down = (e) => {
    const p = e.changedTouches ? e.changedTouches[0] : e;
    ex = p.clientX; ey = p.clientY; eaten = null;   // 新一下 = 新意图
  };
  const up = (e) => {
    const p = e.changedTouches ? e.changedTouches[0] : e;
    if (eaten) return;                   // pointer+touch 双报: 同一下只记一回
    if (Math.hypot(p.clientX - ex, p.clientY - ey) >= 10) return;
    const btn = heroTapBtnAt(p.clientX, p.clientY);
    if (!btn) return;
    const inBar = !!btn.closest(".hero-bar-actions");
    eaten = btn; tries = 0;
    setTimeout(function fire() {
      if (eaten !== btn) return;                 // 换意图 / 真点按来了: 不补
      const head = btn.isConnected ? btn.closest(".hero-head") : null;
      if (inBar && (!head || !head.classList.contains("bar-live"))) {
        if (tries++ < 12) setTimeout(fire, 90);  // 键还在飞/补程在滑: 等收齐
        else eaten = null;                       // 滑回首了键没了: 不补
        return;
      }
      eaten = null;
      jellyButton(btn);                  // 合成点按也给果冻反馈 (1.8.48)
      btn.click();
    }, 220);
  };
  for (const ev of ["pointerdown", "touchstart"]) {
    document.addEventListener(ev, down, { passive: true });
  }
  for (const ev of ["pointerup", "pointercancel", "touchend", "touchcancel"]) {
    document.addEventListener(ev, up, { passive: true });
  }
  document.addEventListener("click", () => { eaten = null; }, true);  // 真来了不补
}
