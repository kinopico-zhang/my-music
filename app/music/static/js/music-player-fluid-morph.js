// music-player-fluid-morph — 播放气泡 ⇄ 全屏播放页的流体胶囊形变 (1.8.63,
// 用户点名 + AI 描述词「实现胶囊按钮向弹窗面板的流体形态变换, 尺寸与圆角
// 采用高阻尼流体曲线无缝过渡」; 1.8.64 用户回评「展开动画再慢一点, 细节
// 多一些」): 点播放气泡, 播放页像水滴一样从气泡的胶囊轮廓原位延展成整页
// 面板 —— 几何五件套 (left/top/width/height/border-radius) 加皮肤 (胶囊的
// 影子/半透明底色) 走同一条高阻尼流体曲线 (先快后缓, 无过冲), 铺开途中
// 底色从胶囊的半透明磨砂灰渐变成播放页的纯黑; 内容分层进场 (样式在
// music-fluid-morph.css)。收起反过来: 内容先退场, 面板收拢回胶囊 ——
// 尺寸/圆角/影子/底色全落回气泡的模样再交还, 快一拍 (进场可以慢, 出场
// 要干脆)。拖拽的收起不走形变 —— 手上有惯性, 滑出才是连续的动作语言。
"use strict";
/* global $ */
/* exported FLUID_CLOSE_MS, FLUID_MS, fluidCollapse, fluidExpand, fluidReset */

const FLUID_MS = 640;        // 铺开时长: 水滴展开一拍 (1.8.64 放缓)
const FLUID_CLOSE_MS = 480;  // 收回时长: 快一拍, 出场别拖
// 高阻尼流体曲线: 与全屏页滑入同款 (强减速无过冲 —— 到位即停, 不晃)
const FLUID_CURVE = "cubic-bezier(.32,.72,0,1)";
let fluidSeq = 0;       // 形变序号: 中途改戏 (开到一半又收) 旧收尾作废

/** 可依的气泡: 没在播 (气泡 hidden) 或量不出矩形就不形变, 调用方退回
    滑入/滑出。胶囊的圆角/影子/底色一并读来当皮肤 (不硬编码)。 */
function fluidBubble() {
  const bubble = $("#mini-player");
  if (!bubble || bubble.hidden) return null;
  const rect = bubble.getBoundingClientRect();
  if (rect.width < 4 || rect.height < 4) return null;
  const style = getComputedStyle(bubble);
  const radius = parseFloat(style.borderTopLeftRadius);
  return {
    rect,
    skin: {
      radius: Number.isFinite(radius) ? radius : 23,
      shadow: style.boxShadow,
      bg: style.backgroundColor,
    },
  };
}

/** 摆一个几何位: 五件套 + 皮肤一起写, transform 恒 none (形变期间不吃
    样式表的滑入滑出位移)。皮肤 = 胶囊的模样 (起位/收位) 或播放页本色
    (落位: 无影 + 纯黑底, 读自样式表 —— 清行内后零跳变)。 */
function fluidPose(player, left, top, width, height, skin) {
  player.style.left = `${left}px`;
  player.style.top = `${top}px`;
  player.style.width = `${width}px`;
  player.style.height = `${height}px`;
  player.style.borderRadius = `${skin.radius}px`;
  player.style.boxShadow = skin.shadow;
  player.style.backgroundColor = skin.bg;
  player.style.transform = "none";
}

function fluidClear(player) {   // 清行内形变样式, 回样式表世界 (inset:0/纯黑)
  player.style.transition = "";
  player.style.left = player.style.top = "";
  player.style.width = player.style.height = "";
  player.style.borderRadius = "";
  player.style.boxShadow = "";
  player.style.backgroundColor = "";
  player.style.transform = "";
}

function fluidGo(player, ms) {  // 放形变: 七件套各自挂上流体曲线
  player.style.transition = ["left", "top", "width", "height", "border-radius",
                             "box-shadow", "background-color"]
    .map((prop) => `${prop} ${ms}ms ${FLUID_CURVE}`).join(", ");
}

/** 开: 播放页从气泡的胶囊轮廓原位延展成全屏 (水滴铺开), 落位收尾自己管
    (计时器带序号闸)。返回 false = 没有可依的气泡, 调用方退回滑入。 */
function fluidExpand(player) {
  const bubble = fluidBubble();
  if (!bubble) return false;
  const seq = ++fluidSeq;
  fluidClear(player);               // 清上一场残留, 先回样式表世界量目标位
  // 落位皮肤 = 播放页本色 (无影 + 样式表的底色); 全屏目标位: 此刻还隐在
  // 屏外 (translateY(100%) 或已 .open), 平移不改 left/width/height ——
  // 量出来就是落位后的 inset:0 矩形, 收尾零跳变
  const computed = getComputedStyle(player);
  const endSkin = { radius: 0, shadow: "none", bg: computed.backgroundColor };
  const target = player.getBoundingClientRect();
  $("#mini-player").style.visibility = "hidden";   // 胶囊由形变中的面板接管
  player.classList.add("morphing"); // 内容让位: 面板先长成, 内容再分层进场
  player.style.transition = "none"; // 起点这一拍不过渡
  fluidPose(player, bubble.rect.left, bubble.rect.top, bubble.rect.width,
            bubble.rect.height, bubble.skin);
  void player.offsetWidth;          // 强制起点先落地 (rAF 在安静页会饿死)
  fluidGo(player, FLUID_MS);
  fluidPose(player, 0, 0, target.width, target.height, endSkin);
  setTimeout(() => {                // 长成过半: 内容分层回场 (面板还在收尾)
    if (seq !== fluidSeq) return;
    player.classList.add("revealed");
  }, FLUID_MS * 0.45);
  setTimeout(() => {                // 落位: 清行内, 样式表 (inset:0) 无缝接手
    if (seq !== fluidSeq) return;
    fluidReset(player);
  }, FLUID_MS);
  return true;
}

/** 收: 播放页收拢回气泡的胶囊轮廓 (水滴收回 —— 尺寸/圆角/影子/底色全落
    回气泡的模样, 再由调用方交还真身), 落位后的清场交调用方
    (closeFullPlayer 的收尾计时里调 fluidReset)。返回 false = 退回滑出。 */
function fluidCollapse(player) {
  const bubble = fluidBubble();
  if (!bubble) return false;
  ++fluidSeq;                       // 作废在途形变的收尾计时
  player.classList.remove("revealed");   // 内容先退场, 面板再收
  player.classList.add("morphing");
  fluidGo(player, FLUID_CLOSE_MS);  // 从当下几何位 (含开场半路) 无缝收拢
  fluidPose(player, bubble.rect.left, bubble.rect.top, bubble.rect.width,
            bubble.rect.height, bubble.skin);
  return true;
}

/** 清场: 作废在途收尾, 清行内形变样式, 撤形变标记, 交还气泡。落位与退路
    (滑入/滑出/拖拽) 都靠它回到干净的样式表世界。 */
function fluidReset(player) {
  fluidSeq++;
  fluidClear(player);
  player.classList.remove("morphing", "revealed");
  $("#mini-player").style.visibility = "";
}
