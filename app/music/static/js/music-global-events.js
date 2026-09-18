// music-global-events — My Music 全局事件绑定 (船坞键/封面文件/Esc)。
// 拆自 music.js (结构化重构), 1.8.0 页签栏撤掉: 搜索键/菜单键在这里接线。
// (1.8.17 蜂窝流量上报整个撤了 —— 设置页改版, 月账没了消费方。)
"use strict";
/* global $, SCAN_POLL_INTERVAL_MS, bindDockMenu, checkScanStatus,
          closeDockMenu, closeFullPlayer, closePushStack, coverUploadPlaylistId,
          navigate, playerOpen, pushStack,
          uploadPlaylistCover, ViewportHUD */
/* exported bindGlobalEvents */

// ------------------------------------------------------------ 启动

function bindGlobalEvents() {
  // 底部船坞: 搜索键进搜索层 (顺手聚焦输入框 —— 老放大镜按钮的手感;
  // 导航是同步渲染, 走到这儿输入框已经在页面上了)。聚焦收窄到顶层层的
  // 输入框: 旧搜索层滑出还挂着 DOM 的 420ms 里, $() 全局找会抓到旧层
  // 那枚 (聚焦即被移除, 键盘/视口状态全乱) —— 1.8.6 修重进搜索失灵
  $("#dock-search").addEventListener("click", () => {
    navigate("search");
    const top = pushStack[pushStack.length - 1];
    const input = top && top.pane.querySelector("#search-input");
    if (input) input.focus();
  });
  bindDockMenu();
  $("#cover-file").addEventListener("change", () => {
    if (coverUploadPlaylistId) uploadPlaylistCover(coverUploadPlaylistId);
  });
  // 后台自动增量重扫的探针: 页面可见时每 30 秒问一次状态
  setInterval(() => {
    if (!document.hidden) checkScanStatus();
  }, SCAN_POLL_INTERVAL_MS);
  // 电脑上的"返回": Esc 依序收上弹菜单 → 播放页 → 顶层二级页 (手机上有右划,
  // 电脑总不能指望鼠标拖页面; 浏览器返回键在应用里已没有可退的条目)
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape" || event.repeat) return;
    if (!$("#pop-menu").hidden) closeDockMenu();
    else if (playerOpen) closeFullPlayer();
    else if (pushStack.length) closePushStack(pushStack.length - 1);
  });
  // 键盘避让 (1.8.16 文档解锁 · 用户实测病愈): 六轮失败回传实锤 —— iOS
  // 让位就是滚文档, 页面里
  // 怎么布置都拦不住 (1.8.11 抢账 / 1.8.13 收键按住 / 1.8.14 预抬 / 1.8.15
  // 给足层内滚动器+撑高, 让位照滚原值 315/356)。健康对照 (my-tesla 费用
  // 弹窗 / my-money 记账弹层, 同机同系统实测无恙) 的差别只剩最后一个:
  // 它们的文档本身可滚 (正常网页 min-height 那套), 让位滚文档是合法滚动,
  // 收键走的是苹果日常百测的还原路径; 本应用文档是固定壳 (html/body
  // overflow:hidden), 让位滚成幽灵滚, 收键把幽灵滚位记进还原高度
  // (812 冻成 771 = 黑带)。对策 = 键盘期间解锁文档 + 给文档真高度 (一切
  // 可见物都是 fixed, 解锁肉眼无感), 高度回满再锁回固定壳; 焦点走了键盘
  // 赖着不收的 2.5s 死线强制回锁 (回锁绝不能抢在收键半路 —— 右划返回时
  // 焦点先走键盘后收, 收键的还原必须全程发生在可滚文档上)。
  if (window.visualViewport) {
    let kbFull = 0;    // 这轮键盘的满屏高 (--kb-full 撑高与文档解锁共用标尺)
    let blurredAt = 0; // 焦点什么时候离开的 (键盘赖着不收的回锁死线用)
    const lift = () => {
      const active = document.activeElement;
      const typing = active && (active.tagName === "INPUT"
                                || active.tagName === "TEXTAREA");
      // 撑高/解锁只伺候键盘: 高度回满 (键盘收走了) 或焦点离开超死线才撤
      // (光看焦点离开就回锁会在右划返回的收键半路拆台)
      if (kbFull && (window.innerHeight >= kbFull - 40
                     || (!typing && Date.now() - blurredAt > 2500))) {
        kbFull = 0;
        document.documentElement.style.removeProperty("--kb-full");
        // 文档回锁: 还原固定壳 (html/body overflow:hidden + 100dvh)
        document.documentElement.style.removeProperty("overflow");
        document.documentElement.style.removeProperty("height");
        document.body.style.removeProperty("height");
        document.body.style.removeProperty("min-height");
        if (typeof ViewportHUD !== "undefined") ViewportHUD.say("回锁");
      }
      // 键盘收走后 iOS 赖账的前两味, 哪种赖下都是回主页底部一块黑、页面
      // 没充满屏, 还会被 iOS 会话恢复原样带回来 (重启 app 也不消):
      // ① 键盘避让把文档滚了 (overflow:hidden 拦不住) —— 文档滚位
      //   (scrollY) 赖着非零, 视口偏移反而是 0 (1.8.5 只查偏移, 漏的正是这味);
      // ② 视口停在偏移上 (offsetTop/Left 非零, 1.8.5 修过的那味)。
      // 文档永不滚是本应用铁律 (固定壳), 任何非零都是脏账 —— 焦点不在
      // 输入框里就一律归零复位。第三味 (高度本身冻在半路, 1.8.10) 归
      // music-viewport-doctor.js 管。
      if (!typing && (window.scrollX || window.scrollY
                      || visualViewport.offsetLeft
                      || visualViewport.offsetTop)) {
        window.scrollTo(0, 0);
      }
    };
    visualViewport.addEventListener("resize", lift);
    visualViewport.addEventListener("scroll", lift);
    // 解锁: 焦点一进输入框立刻拆文档锁 (抢在键盘起手之前 —— 让位起手
    // 那一滚必须落在可滚文档上) + 给文档真高度 + 层内撑高; 键盘已开着
    // (焦点换了个框) 不重复拆
    document.addEventListener("focusin", (event) => {
      const el = event.target;
      if (!el || (el.tagName !== "INPUT" && el.tagName !== "TEXTAREA")) return;
      if (!window.matchMedia("(display-mode: standalone)").matches
          || !/iP(hone|ad|od)/.test(navigator.userAgent)) return;  // 桌面/安卓的账不这么记
      if (kbFull) return;
      kbFull = window.innerHeight;
      blurredAt = 0;
      document.documentElement.style.setProperty("--kb-full", `${kbFull}px`);
      const root = document.documentElement;
      root.style.overflow = "auto";
      root.style.height = "auto";
      document.body.style.height = "auto";
      document.body.style.minHeight = `${kbFull}px`;
      if (typeof ViewportHUD !== "undefined") ViewportHUD.say(`解锁${kbFull}`);
      setTimeout(() => {    // 650ms 没见矮 (实体键盘/起手被拦): 当无事回锁
        if (kbFull && window.innerHeight >= kbFull - 40) lift();
      }, 650);
    });
    // 键盘收走的收尾经常一声事件都不响 (最后那下 resize 响在收干净之前,
    // 从此再没人喊 lift): 焦点一离开输入框就迟几拍各补一次 —— 层滑出/
    // 移除的 420ms 也罩在这个窗口里, 搜索页键盘没收就右划关掉 (100%
    // 复现的底部黑区) 赖下的账当场清
    document.addEventListener("focusout", () => {
      blurredAt = Date.now();   // 回锁死线起算 (键盘赖着不收也有个头)
      setTimeout(lift, 350);
      setTimeout(lift, 900);
      setTimeout(lift, 1800);
    });
    // 开局/回前台/会话恢复: iOS 可能在页面亮出来之后才把脏滚位塞回来
    // (重启 app 黑区还在的元凶) —— 页面一亮相就清一次账
    lift();
    addEventListener("pageshow", lift);
    document.addEventListener("visibilitychange", () => {
      if (!document.hidden) lift();
    });
  }
  // 滚动自己管: iOS 重启/回退会"恢复"上次的滚位 —— 固定壳应用能被恢复的
  // 只有脏账 (文档本来就不该滚), 关掉恢复, 清账的活 lift() 包了
  if ("scrollRestoration" in history) history.scrollRestoration = "manual";
}

