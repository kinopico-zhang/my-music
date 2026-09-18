// music-app-boot — My Music 开局: 绑全局事件, 旧深链消化一次, 回到上次停的页。
// 拆自 music.js (结构化重构: 代码逐字节未动, 经典脚本按 music.html 里的顺序加载, 跨模块引用走全局)。
"use strict";
/* global bindGlobalEvents, navigate, parseRoute, readLastRoute */

bindGlobalEvents();
// 旧深链只消化一次 (#playlist/5 之类 → 按它开局), 随即把 URL 洗成光杆
// /music —— 之后全程一个地址, 应用内导航不再碰浏览器历史 (系统侧滑/
// 返回键没有可退的条目, 整页截图滑走绝迹; 用户点名)。
// 1.8.3 开局回跳 (用户点名「打开 app 自动回最后一个页面」): 没有旧深链
// 就读上次停的页; 没记过 (= 头一回) 回主页播放列表。
// 1.8.8 整栈回跳 (用户点名「返回逻辑要有效」): 档案记的是整条轨迹
// (根视图 + 各层依序), 开局逐层重放 —— 只回放栈顶的话, 那层直接盖在
// 没渲染过的根上, 收层返回露出的是「加载中」死页。首段不是主页 (旧
// 格式单键档案 / 旧深链) 就垫上主页再走, 返回一路有家可回。
const legacyHash = location.hash.replace(/^#\/?/, "");
const saved = legacyHash && parseRoute(legacyHash) ? legacyHash : readLastRoute();
let journey = saved.split(",").map((key) => key.trim())
  .filter((key) => parseRoute(key));
if (!journey.length || journey[0] !== "home") journey = ["home", ...journey];
history.replaceState(null, "", location.pathname + location.search);
journey.forEach(navigate);
