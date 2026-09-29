// play-outbox — 播放计数补报队列 (1.8.124)。
// 出声即上报原来是发后不管: 断网听歌 / 服务重启 / 5xx 窗口里听过的那几笔
// 就永久丢了 (排行缺账, 用户问过「你的播放排行, 数据有丢失过吗」—— 查库
// 无零日, 但离线窗口无据可查)。现在报不上先暂存本机 (localStorage),
// 回网 / 回前台 / 下次打开时按序补报; 补报带真实播放时刻, 排行按时刻落
// 区间不错档。404 (曲目已删) 丢弃不重试; 队列封顶 500, 满了先丢最老的。
// 适配器注入 (node --test 直测); 浏览器接线在消费方
// music-player-audio-events.js (「playing」出声走 report, 三个补报时机)。
/**
 * 队列里待补的一笔。
 * @typedef {Object} PlayOutboxEntry
 * @property {number} track_id
 * @property {number} played_at    epoch 秒 (真实播放时刻, 排行落区间用它)
 */

/**
 * 适配器 (浏览器实现在接线文件, 测试用桩)。
 * @typedef {Object} PlayOutboxAdapters
 * @property {Function} readQueue   () => Array<PlayOutboxEntry>   坏数据容错返 []
 * @property {Function} writeQueue  (entries: Array<PlayOutboxEntry>) => void
 * @property {Function} postPlay    (entry) => Promise<{status: number}>
 *                                 应答带 HTTP 状态码; 网络错以 reject 出场
 * @property {Function} now         () => number   epoch 秒 (测试可注入)
 */

const PLAY_OUTBOX_CAP = 500;   // 封顶: 满了丢最老 (本机存储守个底)

function createPlayOutbox(adapters) {
  let flushing = false;   // 在途不重入 (online 与 visibilitychange 同场双触发)

  const load = () => {
    const entries = adapters.readQueue();
    return Array.isArray(entries) ? entries : [];
  };

  /** 一笔一笔按序发: 成功 / 404 出队落盘 (发一笔落一笔, 中途崩不重发
      已成的); 网络错 / 5xx / 401 停手留着, 回网 / 回前台 / 下次打开再试。
      永不 reject —— 失败只是留着, 补报从不挡听歌。 */
  async function flush() {
    if (flushing) return;
    flushing = true;
    try {
      let queue = load();
      while (queue.length) {
        let response;
        try {
          response = await adapters.postPlay(queue[0]);
        } catch {
          return;   // 网络错: 整队留着
        }
        // 200 记上了; 404 = 曲目已删, 丢弃不算失败 (后面的照发);
        // 其余 (5xx / 401 会话过期) 留队等下个时机
        if (response.status !== 200 && response.status !== 404) return;
        // 出队要重读盘上现状再删队头: 发送期间 report 还能追加新账
        // (在途闸只挡 flush 不挡 report), 认死开局那份旧数组会把追加
        // 进来的新账一并抹掉
        queue = load();
        queue.shift();
        adapters.writeQueue(queue);
      }
    } finally {
      flushing = false;
    }
  }

  /** 记一笔播放: 入队 (带真实时刻) 落盘, 顺手立即试发 —— 发得出去当场
      出账, 发不出去排队等补; 返回 flush 的 Promise (永不 reject, 调用方
      可不接)。 */
  function report(trackId) {
    const entries = load();
    entries.push({ track_id: trackId, played_at: adapters.now() });
    while (entries.length > PLAY_OUTBOX_CAP) entries.shift();   // 满了丢最老
    adapters.writeQueue(entries);
    return flush();
  }

  return { report, flush };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { createPlayOutbox, PLAY_OUTBOX_CAP };
}
