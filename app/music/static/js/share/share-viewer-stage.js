// share-viewer-stage — 分享页 3D 封面舞台接线。
// 1.8.130 (用户点名「3d切换封面」) 整模块复用应用的 music-player-art-stage
// (摆姿/拖拽/交班溶解全在里头, 200 行零余量不动它), 这里只做两件覆盖:
//  - 封面取址改走分享 token 的公开路由 —— 原版 stageCardSrc 指要登录会话
//    的 /music/media/..., 访客没有会话。经典脚本的全局函数属性是可写的,
//    这里直接改写它, 舞台内部按名调用自然走新的 (应用侧哪天收编成模块,
//    这条覆盖会当场失效, 页面接线测试咬得住)。
//  - 音质取址同法 (应用的 /api/tracks/{id}/quality 要会话): 后端给
//    /share/{token}/quality/{id} 公开口, 音质行整用 music-player-quality
//    (三条跟卡飞、按曲缓存那套全白拿), 钩子不再空转。
"use strict";
/* global PLACEHOLDER_ARTWORK, artURL, qualityURL: writable, stageCardSrc: writable,
          token */
/* exported qualityURL, stageCardSrc */   // 两枚只写不读的覆盖 (读它们的在 art-stage/quality), exported 豁免

stageCardSrc = (img, track) => {
  img.onerror = () => { img.onerror = null; img.src = PLACEHOLDER_ARTWORK; };
  img.src = track ? artURL(track) : PLACEHOLDER_ARTWORK;
};

qualityURL = (track) => `/music/share/${token}/quality/${track.track_id}`;
