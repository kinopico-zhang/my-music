// music-player-quality — 播放页封面下的音质行 (1.8.127 增; 1.8.129 拆独立
// 模块并改成每张卡一条, 跟着封面 3D 翻面进出 —— 用户点名「和封面一起 3D
// 滚动进入退出」)。文案 = 格式 · 采样率/位深 · 码率 (有损没位深只显
// kHz+kbps, 单声道注明, DSD 显 MHz); 取数走 /api/tracks/{id}/quality
// (索引里有走库, 老库行后端现读文件回填 —— 每首最多读一次), 会话内按曲
// 缓存: 邻曲在当邻居时就取好, 滑进来那拍字早在。姿态由 art-stage 的
// poseCard 同参直落 (几何见 music-player-quality.css 头注)。
"use strict";
/* global $, currentTrack, fetchJSON, poseCard, stageNeighbors */
/* exported fillStageQuality, poseQualityStrips, handoffQualityStrip,
            clearQualityHandoff */

let qualityFetchSeq = 0;          // 每次铺场 +1: 迟到的应答不碰新场
const qualityCache = new Map();   // track_id → 格式化好的文案 (只存取成功的)

/** 音质对象 → 一行文案: FLAC · 44.1kHz / 16bit · 1049kbps。 */
function formatQuality(quality) {
  const hz = quality.sample_rate >= 1000000
    ? `${(quality.sample_rate / 1000000).toFixed(1)}MHz`
    : `${quality.sample_rate % 1000
         ? (quality.sample_rate / 1000).toFixed(1)
         : quality.sample_rate / 1000}kHz`;
  const parts = [];
  if (quality.file_format) parts.push(quality.file_format.toUpperCase());
  if (quality.sample_rate) {
    parts.push(quality.bit_depth ? `${hz} / ${quality.bit_depth}bit` : hz);
  }
  if (quality.bitrate) parts.push(`${quality.bitrate}kbps`);
  if (quality.channels === 1) parts.push("单声道");
  return parts.join(" · ");
}

/** 取数地址: 应用侧默认走会话接口; 分享页 (share-viewer-stage) 改写走
 *  token 公开路由 (stageCardSrc 同款覆盖法, 只写不读全靠运行时按名调用)。 */
function qualityURL(track) {
  return `/music/api/tracks/${track.track_id}/quality`;
}

/** 取一首的文案: 取成功才进缓存, 失败回空串不缓存 (下次铺场再试, 不弹错)。 */
async function qualityText(track) {
  try {
    const text = formatQuality(await fetchJSON(qualityURL(track)));
    qualityCache.set(track.track_id, text);
    return text;
  } catch (_error) {
    return "";
  }
}

/** 一条音质行落到槽上: 没曲藏; 没底子先清场 (别顶着他曲的旧字飞), 取回来再显。 */
async function fillStrip(line, track, seq) {
  line.classList.toggle("off", !track);   // 没邻居的侧条跟卡一样藏
  if (!track) { line.hidden = true; return; }
  let text = qualityCache.get(track.track_id);
  if (text === undefined) {
    line.hidden = true;
    text = await qualityText(track);
    if (seq !== qualityFetchSeq) return;  // 迟到: 场已换新, 不碰 (缓存已记上)
  }
  line.textContent = text;
  line.hidden = !text;
}

/** 铺场 (renderPlayerChrome 一拍): 当前曲 + 两侧邻居各就各位。 */
function fillStageQuality() {
  const seq = qualityFetchSeq += 1;
  const neighbors = stageNeighbors();
  void fillStrip($("#fp-quality"), currentTrack, seq);
  void fillStrip($("#fp-quality-prev"), neighbors.prev, seq);
  void fillStrip($("#fp-quality-next"), neighbors.next, seq);
}

/** 三条跟三张卡同参摆 (poseStage 每拍带呼, 拖动中跟手)。 */
function poseQualityStrips(sway) {
  poseCard($("#fp-quality"), sway);
  poseCard($("#fp-quality-prev"), sway - 1);
  poseCard($("#fp-quality-next"), sway + 1);
}

// 交班 (程序切歌): 旧曲的字跟旧曲卡一样压顶 (z5) 溶出让位 (与 clearHandoff 成对)。
let handoffStrip = null;
function handoffQualityStrip(side) {
  handoffStrip = $(side === "prev" ? "#fp-quality-prev" : "#fp-quality-next");
  handoffStrip.classList.add("handoff");
  handoffStrip.style.opacity = "0";
}

/** 撤交班: 淡出没走完就被下一场接走也在这里平回。 */
function clearQualityHandoff() {
  if (!handoffStrip) return;
  handoffStrip.classList.remove("handoff");
  handoffStrip.style.opacity = "1"; handoffStrip = null;
}
