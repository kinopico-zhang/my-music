// music-global-events — My Music 全局事件绑定 (船坞键/封面文件/Esc) + 蜂窝流量浏览器适配器。
// 拆自 music.js (结构化重构), 1.8.0 页签栏撤掉: 搜索键/菜单键在这里接线。
"use strict";
/* global $, SCAN_POLL_INTERVAL_MS, bindDockMenu, checkScanStatus,
          closeDockMenu, closeFullPlayer, closePushStack, coverUploadPlaylistId,
          createCellularMonitor, navigate, playerOpen, pushStack,
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
  // 键盘避让 (1.8.15 换血): 病根五轮回传实锤 —— iOS 让位专滚焦点元素的
  // 最近滚动祖先; 搜索栏原先是钉死屏底的 fixed 件 (四周没有任何可滚的
  // 东西, 文档又是固定壳), 让位只好硬滚锁死的文档, 收键盘那笔坏账 (底部
  // 黑带) 就从这一滚记下。健康对照 (同机同系统实测): my-tesla 费用弹窗 /
  // my-money 记账弹层的输入框都住在可滚容器里, 让位滚的是容器, 文档
  // 纹丝不动。搜索页照此换血 (music-search.css: 页壳自己变滚动器, 页底
  // 一条 sticky 钉底), 这层只补一件: 键盘起手前把满屏高写进 --kb-full ——
  // 布局被键盘缩矮后页壳内容比可视区高, 让位的滚落在页壳里, 文档不沾账。
  if (window.visualViewport) {
    let kbFull = 0;   // 这轮焦点立下的满屏高 (--kb-full 的 JS 影子)
    const lift = () => {
      const active = document.activeElement;
      const typing = active && (active.tagName === "INPUT"
                                || active.tagName === "TEXTAREA");
      // 撑高只伺候键盘: 键盘收走了 (回到满屏高) 或焦点离开了就撤
      if (kbFull && (!typing || window.innerHeight >= kbFull - 40)) {
        kbFull = 0;
        document.documentElement.style.removeProperty("--kb-full");
        if (typeof ViewportHUD !== "undefined") ViewportHUD.say("键盘走撤撑");
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
    // 撑高: 焦点一进输入框立刻立满屏高 (抢在键盘起手之前 —— 页壳里的
    // 滚动器先有得滚, 让位才有处落); 键盘已开着 (焦点换了个框) 不重立
    document.addEventListener("focusin", (event) => {
      const el = event.target;
      if (!el || (el.tagName !== "INPUT" && el.tagName !== "TEXTAREA")) return;
      if (!window.matchMedia("(display-mode: standalone)").matches
          || !/iP(hone|ad|od)/.test(navigator.userAgent)) return;  // 桌面/安卓的账不这么记
      if (kbFull) return;
      kbFull = window.innerHeight;
      document.documentElement.style.setProperty("--kb-full", `${kbFull}px`);
      if (typeof ViewportHUD !== "undefined") ViewportHUD.say(`撑高${kbFull}`);
      setTimeout(() => {    // 650ms 没见矮 (实体键盘/起手被拦): 当无事撤撑
        if (kbFull && window.innerHeight >= kbFull - 40) lift();
      }, 650);
    });
    // 键盘收走的收尾经常一声事件都不响 (最后那下 resize 响在收干净之前,
    // 从此再没人喊 lift): 焦点一离开输入框就迟几拍各补一次 —— 层滑出/
    // 移除的 420ms 也罩在这个窗口里, 搜索页键盘没收就右划关掉 (100%
    // 复现的底部黑区) 赖下的账当场清
    document.addEventListener("focusout", () => {
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

// ------------------------------------------------------------ 蜂窝流量
// 只有能认出蜂窝网络的浏览器 (安卓 Chrome 的 navigator.connection) 才上报,
// iPhone 的 Safari 认不出网络类型, 记不上 (设置页有说明)。收口/上报的
// 节奏在 cellular-usage.js, 这里只给浏览器适配器。
if (window.performance && performance.getEntriesByType
    && typeof createCellularMonitor === "function") {
  createCellularMonitor({
    isCellular: () => {
      const connection = navigator.connection
        || navigator.mozConnection || navigator.webkitConnection;
      return !!connection && connection.type === "cellular";
    },
    takeEntries: () => performance.getEntriesByType("resource"),
    report: async (bytes) => {
      const response = await fetch("/music/api/cellular-usage", {
        method: "POST", keepalive: true,      // 离开页面那一笔也要送到
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ bytes }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
    },
    onHide: (flush) => {
      window.addEventListener("pagehide", flush);
      document.addEventListener("visibilitychange", () => {
        if (document.hidden) flush();     // 切后台就报, 别等系统杀页
      });
    },
    now: () => Date.now(),
  }).start();
}

