// music-global-events — My Music 全局事件绑定 (船坞键/封面文件/Esc) + 蜂窝流量浏览器适配器。
// 拆自 music.js (结构化重构), 1.8.0 页签栏撤掉: 搜索键/菜单键在这里接线。
"use strict";
/* global $, SCAN_POLL_INTERVAL_MS, bindDockMenu, checkScanStatus, closeDockMenu,
          closeFullPlayer, closePushStack, coverUploadPlaylistId, createCellularMonitor,
          navigate, playerOpen, pushStack, uploadPlaylistCover */
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
  // 键盘避让 (1.8.3 搜索栏钉页底): iOS 键盘只盖不缩布局, visualViewport
  // 量出键盘高写进 --kb-h (CSS 把搜索栏抬到键盘上沿); 没有输入框在焦点上
  // 时归零 —— 捏拉缩放同样会缩 visualViewport, 别误抬。安卓
  // interactive-widget=resizes-content 布局自己缩, 量出来是 0, 两不误伤。
  if (window.visualViewport) {
    // 满高基准 (1.8.9): 布局视口被冻矮时 innerHeight 自己就是矮的, 得拿
    // 「见过的最高个」作对照 —— 开局先看档里记的 (上回健在时的满高, 防
    // webview 带着冻矮的视口跨重启), 之后长高了就刷新; 转过屏按新方向
    // 重立 (横竖的满高不能混着比)
    const landscape = () => window.matchMedia("(orientation: landscape)").matches;
    let seenLandscape = landscape();
    let fullInner = window.innerHeight;
    try {
      const saved = JSON.parse(localStorage.getItem("music.fullInner") || "null");
      if (saved && saved.landscape === seenLandscape) {
        fullInner = Math.max(fullInner, saved.height || 0);
      }
    } catch (_error) { /* 隐私模式读不了就只信开局值 */ }
    const noteFull = () => {
      if (window.innerHeight <= fullInner) return;
      fullInner = window.innerHeight;
      try {
        localStorage.setItem("music.fullInner",
          JSON.stringify({ height: fullInner, landscape: seenLandscape }));
      } catch (_error) { /* 存不进就算了, 内存里那份还在 */ }
    };
    // 修视口的探针: 常驻 DOM 的隐形输入框 (样式在 music-base.css: 1px
    // 见方全透明钉在视口内 —— 在视口内 iOS 才不为它滚动), 拿它走一趟
    // focus→blur, 逼手机把键盘那一套视口尺寸重算回来 (键盘会闪一下,
    // 换黑带消失, 值)。探针从不移除 —— 移除聚焦过的输入框正是视口冻矮
    // 的配方。定时器里的 focus 未必唤得动 iOS 键盘 (没手势), 所以再埋
    // 一手: 用户下一次触屏时借着手势补一趟。一回赖账最多修三次 (别闪个
    // 没完), 修回来清零
    const probe = document.createElement("input");
    probe.id = "kb-repair";
    probe.type = "text";
    probe.tabIndex = -1;
    probe.autocomplete = "off";
    probe.setAttribute("autocapitalize", "off");
    probe.setAttribute("autocorrect", "off");
    probe.setAttribute("aria-hidden", "true");
    document.body.appendChild(probe);
    let repairs = 0;
    let gestureArmed = false;
    const repairViewport = () => {
      if (repairs >= 3) return;
      repairs += 1;
      probe.focus();
      setTimeout(() => probe.blur(), 150);
    };
    const armGestureRepair = () => {
      if (gestureArmed) return;
      gestureArmed = true;
      addEventListener("pointerdown", () => {
        gestureArmed = false;
        if (fullInner - window.innerHeight > 12) repairViewport();
      }, { once: true });
    };
    const lift = () => {
      const active = document.activeElement;
      const typing = active && active.tagName === "INPUT";
      const keyboard = typing
        ? Math.max(0, window.innerHeight - visualViewport.height
                   - visualViewport.offsetTop)
        : 0;
      document.documentElement.style.setProperty("--kb-h", `${keyboard}px`);
      // 键盘收走后 iOS 赖账有两种风味, 哪种赖下都是回主页底部一块黑、
      // 页面没充满屏, 还会被 iOS 会话恢复原样带回来 (重启 app 也不消,
      // 用户追了两个版本):
      // ① 键盘避让把文档滚了 (overflow:hidden 拦不住) —— 文档滚位
      //   (scrollY) 赖着非零, 视口偏移反而是 0 (1.8.5 只查偏移, 漏的正是这味);
      // ② 视口停在偏移上 (offsetTop/Left 非零, 1.8.5 修过的那味)。
      // 文档永不滚是本应用铁律 (固定壳), 任何非零都是脏账 —— 焦点不在
      // 输入框里就一律归零复位
      if (!typing && (window.scrollX || window.scrollY
                      || visualViewport.offsetLeft
                      || visualViewport.offsetTop)) {
        window.scrollTo(0, 0);
      }
      // ③ 第三味 (1.8.9 录屏逐帧定位, 1.8.7 修不掉的那味): 键盘收起动画
      //    走到半路时收走聚焦过的层, 布局视口整个冻在没收满的矮个上 ——
      //    不是滚位 (顶部纹丝不动, ①②的复位都够不着), fixed 船坞和
      //    100dvh 一起垫高, 屏底一条纯黑。没键盘 (视口回到 innerHeight
      //    附近) 却比满高矮一截就是它 —— iOS 独有的病 (安卓布局自己缩,
      //    innerHeight 天生会动), 别误修
      if (!typing && visualViewport.height >= window.innerHeight - 12) {
        const nowLandscape = landscape();
        if (nowLandscape !== seenLandscape) {
          seenLandscape = nowLandscape;
          fullInner = window.innerHeight;
        }
        noteFull();
        if (/iP(hone|ad|od)/.test(navigator.userAgent)
            || (navigator.platform === "MacIntel"
                && navigator.maxTouchPoints > 1)) {
          if (fullInner - window.innerHeight > 12) {
            repairViewport();
            armGestureRepair();
          } else {
            repairs = 0;   // 健在: 下回再赖账重新给满三回
          }
        }
      }
    };
    visualViewport.addEventListener("resize", lift);
    visualViewport.addEventListener("scroll", lift);
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

