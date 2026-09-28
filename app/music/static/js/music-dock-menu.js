// music-dock-menu — My Music 底部菜单键: 上弹菜单 (播放列表/专辑/艺人/最近播放/已下载/设置) 的开关与导航。
// 1.8.0 页签栏撤掉, 原页签的导航职能收进这枚菜单 (用户点名「点击菜单按钮,
// 纵向向上弹出菜单」)。
// 1.8.109 修用户实报「pc 菜单弹出的位置和左下角菜单按钮太远」: 船坞行在
// 大屏居中 (max-width 1040), 菜单键离屏左缘几百 px, 而弹层钉死屏左 8px ——
// 开时现量键的 x, 弹层跟着键走 (transform-origin 的 23px 锚心也回正);
// 手机窄屏量出来与基线同值, 触摸端观感一字节不变。
"use strict";
/* global $, navigate */
/* exported bindDockMenu, closeDockMenu */

// ------------------------------------------------------------ 上弹菜单

function bindDockMenu() {
  $("#dock-menu").addEventListener("click", (event) => {
    const menu = $("#pop-menu");
    const opening = menu.hidden;
    if (opening) {
      // 锚到键正上方 (1.8.109 修用户实报「菜单弹层离键太远」, 详见文件头):
      // 现量键的 x —— 手机窄屏量出来与基线同值, 触摸端观感一字节不变
      const keyX = event.currentTarget.getBoundingClientRect().left;
      menu.style.left = `${keyX}px`;
    }
    menu.hidden = !opening;
    $("#pop-mask").hidden = !opening;
  });
  // 点背景收起 (遮罩盖全屏, 也是菜单外任何位置的兜底)
  $("#pop-mask").addEventListener("click", closeDockMenu);
  $("#pop-menu").addEventListener("click", (event) => {
    const button = event.target.closest("[data-pop-nav]");
    if (!button) return;
    closeDockMenu();     // 先收菜单再导航: 层滑入时菜单不在场
    navigate(button.dataset.popNav);
  });
}

/** 收起上弹菜单 (选完条目 / 点背景 / Esc 都走这里)。 */
function closeDockMenu() {
  $("#pop-menu").hidden = true;
  $("#pop-mask").hidden = true;
}
