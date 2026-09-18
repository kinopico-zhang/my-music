// music-viewport-heal — 视口治疗的手法 (1.8.12, 医生是 music-viewport-doctor)。
// 病 (1.8.11 回传实锤, iOS 18.7 独立模式): 键盘收起那一下, WebKit 把「还原
// 高度」记坏成 771 (满高 812, 差的 41 就是黑带), 之后页面里什么招都掰不动
// 它 —— 翻面/meta 踢十一连发全是 771 原地不动, 连用户真实开合键盘三轮也只
// 回落到 771 (键盘落下永远认那个坏值)。社区验方 (cederhook 翻面) 在这台
// 机器上无效, 键盘往返也死了。能清这笔账的只剩换一份新文档: 开局回传实测
// 是干净的 812。所以手法只剩一招「深修」: 存个标记刷新页面, 医生读到标记
// 报数, 回传日志里看它灵不灵 (不灵的话下一步只剩重启应用, 也让日志说话)。
"use strict";
/* global ViewportHUD */
/* exported ViewportHeal */

const ViewportHeal = (() => {
  // 深修: 刷新换新文档 (布局视口随新文档复位)。播放现场本来就有 5 秒一存的
  // 档 (队列/曲目/进度, pagehide 也存), 回来停在原曲原秒, 点播放键接着听;
  // 页面路径有记忆, 回到原来那页。深修前后的数字都进回传, 复位成没成一目了然。
  function reloadDeep() {
    try {
      localStorage.setItem("music.deepRepairAt", String(Date.now()));
    } catch (_error) { /* 存不进也照样刷, 只是归来没标记可报 */ }
    ViewportHUD.say(`深修 开工 i${window.innerHeight} (刷新复位)`);
    ViewportHUD.send();              // 刷新前当场送 (keepalive 能扛过卸载)
    location.reload();
  }
  return { reloadDeep };
})();
