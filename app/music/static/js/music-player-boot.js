// music-player-boot — My Music 播放器开局接线: 绑事件 + 恢复上次现场 (须最后加载)。
// 拆自 music-player.js (结构化重构: 按逻辑再切一刀, 前半按钮事件留在 music-player-events)。
"use strict";
/* global bindPlayerEvents, playerRestore, playerStateServerBackfill */

bindPlayerEvents();
playerRestore();
playerStateServerBackfill();   // 1.8.142: 本地档没了从服务端捞 (异步, 不挡开局)
