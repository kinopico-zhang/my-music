// music-hero-snap — 封面收缩的停稳补程 (拆自 music-hero-collapse, 文件顶
// 200 行帽): 滚动事件停稳 160ms 后自动补程 —— 过半滑到底收齐、不到半弹
// 回 (1.8.34 七改, 你报的「…要点第二下才行」: 收拢靠惯性滚完, iOS 把惯性
// 中的头一下点按吞成「停滚」); 手指按着不补, … 开着照补 (顶栏钉死)。
// 1.8.140 拆出独立模块并加 heroSnapHold (特斯拉车机实报「切歌时界面上下
// 跳动」): 车机上「轻拨列表就点歌」正中补程窗口 —— 落指点歌那拍列表还
// 在惯性滑, 停稳后补程落闸, 整个列表又自己滑走半程。点歌 (loadTrack) 那
// 拍把挂着的补程全撤: 列表停在用户放的地方, 下次滚动照旧停稳补程。锁屏
// 键位/连播也走 loadTrack, 顺带受益 (没人看着也别乱动)。
"use strict";
/* global heroCtrls, heroTouching */
/* exported heroSnapArm, heroSnapHold */

// 滚动器 → 补程计时器。Map (原 WeakMap): heroSnapHold 要一次撤光所有
// 挂着的补程, WeakMap 没法遍历; 条目只在补程挂着时存在 (落闸/重挂自删),
// 死层的计时器落闸时有 isConnected 兜底, 不漏。
const heroSnapTimers = new Map();

/** 滚动事件到达时 (重)挂补程: 每个滚动事件刷新 160ms 的停稳窗口。 */
function heroSnapArm(scroller) {
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

/** 一次撤光挂着的补程 (切歌那拍, 见文件头 1.8.140 注)。 */
function heroSnapHold() {
  for (const timer of heroSnapTimers.values()) clearTimeout(timer);
  heroSnapTimers.clear();
}
