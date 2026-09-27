// handoff — My Music 后台连播提前接力的裁决 (1.8.100, 纯逻辑 node 直测)。
// iOS 在「上一曲停了、下一曲还没出声」的空窗里能把整页挂起: ended 里
// 同步 play() 也躲不开 —— play 真正出声在 WebKit 内部异步落地, 偶发整页
// 先被冻住, 元素假在播 (锁屏进度是浏览器按上次报的位置自估的), 一整首
// 没声, 过一阵锁屏卡片整个没了 (实报「第二首没声音, 进度条还在走」)。
// 裁决: 趁还剩零点几秒、声音还在响就先切 —— 会话活着, 换源即接上,
// 空窗根本不出现。前台不切 (自然播完零裁切), ended 路永远保底。
"use strict";

/** 提前量: 剩余降到这以内 (且 >0) 就动手, 歌尾至多裁掉这一段。 */
const HANDOFF_WINDOW_S = 0.45;
/** 剩余回到这之上 = 新曲时间轴, 接力资格复位 (末尾可再次触发)。 */
const HANDOFF_RESET_S = 1;

/**
 * 这一拍 timeupdate 要不要提前接力切下一曲?
 * @param {Object} state
 * @param {boolean} state.hidden     页面在后台 (前台自然播完, 零裁切)
 * @param {boolean} state.scrubbing  正在拖进度条 (别抢用户手里的操作)
 * @param {boolean} state.repeatOne  单曲循环 (ended 自己回开头, 不换曲)
 * @param {number} state.remaining   还剩几秒 (元素时长优先, 库时长兜底)
 * @param {boolean} state.spent      本曲末尾已接力过 (timeupdate 连拍只动一次手)
 * @returns {{handoff: boolean, spent: boolean}} handoff = 现在切;
 *   spent = 这拍之后接力资格的最新值 (剩余回到 1 秒之上复位)。
 */
function shouldHandoffEarly(state) {
  if (state.remaining > HANDOFF_RESET_S) {
    return { handoff: false, spent: false };   // 新曲时间轴: 资格复位
  }
  if (state.spent || !state.hidden || state.scrubbing || state.repeatOne) {
    return { handoff: false, spent: state.spent };
  }
  if (!(state.remaining > 0) || state.remaining > HANDOFF_WINDOW_S) {
    return { handoff: false, spent: state.spent };   // ≤0 交给 ended 保底
  }
  return { handoff: true, spent: true };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { HANDOFF_WINDOW_S, HANDOFF_RESET_S, shouldHandoffEarly };
}
