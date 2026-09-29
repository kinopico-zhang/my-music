/* play-outbox.js 的 node --test 单元测试 (1.8.124 播放计数补报队列):
   成功当场出账, 网络错/5xx/401 留队等补, 404 丢弃不挡后面的, 按序发送,
   在途不重入, 队列封顶丢最老, 补报带真实播放时刻 (now 前进了也不改口)。 */
import test from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const dir = path.join(path.dirname(fileURLToPath(import.meta.url)),
                      "../../app/music/static/js");
const { createPlayOutbox, PLAY_OUTBOX_CAP } = require(path.join(dir, "play-outbox.js"));

/** 桩适配器: 队列在内存 (initial 预存旧账), postPlay 默认全成功
    (attempts 记下每次尝试)。 */
function stubOutbox(overrides = {}, initial = []) {
  let stored = initial.slice();
  const attempts = [];
  const adapters = {
    readQueue: () => stored,
    writeQueue: (entries) => { stored = entries.slice(); },
    postPlay: async (entry) => {
      attempts.push(entry);
      return { status: 200 };
    },
    now: () => 1000,
    ...overrides,
  };
  return { adapters, stored: () => stored, attempts };
}

test("报得上当场出账: report 即试发, 队列清空", async () => {
  const { adapters, stored, attempts } = stubOutbox();
  const outbox = createPlayOutbox(adapters);
  await outbox.report(7);
  assert.deepEqual(attempts, [{ track_id: 7, played_at: 1000 }]);
  assert.deepEqual(stored(), []);
});

test("网络错留队: 下个时机 (flush) 换成成功就补上", async () => {
  const { adapters, stored, attempts } = stubOutbox({
    postPlay: async () => { throw new Error("断网"); },
  });
  const outbox = createPlayOutbox(adapters);
  await outbox.report(5);                     // 断网: 留着
  assert.deepEqual(stored(), [{ track_id: 5, played_at: 1000 }]);
  adapters.postPlay = async (entry) => {      // 回网了
    attempts.push(entry);
    return { status: 200 };
  };
  await outbox.flush();
  assert.deepEqual(attempts, [{ track_id: 5, played_at: 1000 }]);
  assert.deepEqual(stored(), []);
});

test("5xx / 401 也留队 (服务端报错不再被当成功)", async () => {
  for (const status of [503, 500, 401]) {
    const { adapters, stored, attempts } = stubOutbox({
      postPlay: async (entry) => { attempts.push(entry); return { status }; },
    });
    const outbox = createPlayOutbox(adapters);
    await outbox.report(3);
    assert.deepEqual(stored(), [{ track_id: 3, played_at: 1000 }]);  // 留着
  }
});

test("404 (曲目已删) 丢弃, 不挡后面待补的", async () => {
  const { adapters, stored, attempts } = stubOutbox(
    { postPlay: async (entry) => {
        attempts.push(entry);
        return { status: entry.track_id === 1 ? 404 : 200 };
      } },
    [{ track_id: 1, played_at: 900 }, { track_id: 2, played_at: 950 }]);
  const outbox = createPlayOutbox(adapters);
  await outbox.flush();
  assert.equal(attempts.length, 2);           // 两笔都试过 (404 不短路)
  assert.deepEqual(stored(), []);              // 404 那笔丢弃出队
});

test("按序补报: 队列里的旧账一笔一笔按先后发", async () => {
  const { adapters, stored, attempts } = stubOutbox({
    postPlay: async () => { throw new Error("断网"); },
  });
  const outbox = createPlayOutbox(adapters);
  await outbox.report(1);
  await outbox.report(2);
  await outbox.report(3);
  adapters.postPlay = async (entry) => {
    attempts.push(entry);
    return { status: 200 };
  };
  await outbox.flush();
  assert.deepEqual(attempts.map((e) => e.track_id), [1, 2, 3]);
  assert.deepEqual(stored(), []);
});

test("在途不重入: 两次 flush 同场只跑一遍", async () => {
  let release;
  const gate = new Promise((resolve) => { release = resolve; });
  const { adapters, attempts } = stubOutbox(
    { postPlay: async (entry) => { attempts.push(entry); await gate; return { status: 200 }; } },
    [{ track_id: 1, played_at: 900 }]);
  const outbox = createPlayOutbox(adapters);
  const first = outbox.flush();               // 在途 (卡在第一笔)
  const second = outbox.flush();              // 同场第二触发: 直接让位
  release();
  await Promise.all([first, second]);
  assert.equal(attempts.length, 1);           // 没有第二遍
});

test("在途追加不丢: flush 发第一笔期间 report 进来的新账也照发", async () => {
  let release;
  const gate = new Promise((resolve) => { release = resolve; });
  const { adapters, stored, attempts } = stubOutbox({
    postPlay: async (entry) => { attempts.push(entry); await gate; return { status: 200 }; },
  });
  const outbox = createPlayOutbox(adapters);
  const flushing = outbox.report(1);          // 第一笔在途 (卡住)
  await new Promise((resolve) => setTimeout(resolve, 0));   // postPlay 已开局
  outbox.report(2);                           // 在途期间追加的新账
  release();
  await flushing;
  assert.deepEqual(attempts.map((e) => e.track_id), [1, 2]);  // 两笔都发了
  assert.deepEqual(stored(), []);
});

test("队列封顶: 满了丢最老 (本机存储守个底)", async () => {
  const { adapters, stored } = stubOutbox({
    postPlay: async () => { throw new Error("断网"); },
  });
  const outbox = createPlayOutbox(adapters);
  assert.equal(PLAY_OUTBOX_CAP, 500);
  for (let i = 0; i < PLAY_OUTBOX_CAP + 2; i += 1) {
    await outbox.report(i);
  }
  assert.equal(stored().length, PLAY_OUTBOX_CAP);
  assert.equal(stored()[0].track_id, 2);      // 最老的两笔让位
  assert.equal(stored()[PLAY_OUTBOX_CAP - 1].track_id, PLAY_OUTBOX_CAP + 1);
});

test("补报带真实播放时刻: 入队那一刻定死, now 前进了也不改口", async () => {
  let clock = 1000;
  const { adapters, stored, attempts } = stubOutbox({
    now: () => clock,
    postPlay: async () => { throw new Error("断网"); },
  });
  const outbox = createPlayOutbox(adapters);
  await outbox.report(9);                     // 昨天离线听的时候
  clock = 999999;                             // 今天回网补报
  adapters.postPlay = async (entry) => {
    attempts.push(entry);
    return { status: 200 };
  };
  await outbox.flush();
  assert.deepEqual(attempts, [{ track_id: 9, played_at: 1000 }]);
  assert.deepEqual(stored(), []);
});

test("开局补报: 新实例读得动上回存下的队列", async () => {
  const { adapters, stored, attempts } = stubOutbox({
    postPlay: async () => { throw new Error("断网"); },
  });
  const offline = createPlayOutbox(adapters);
  await offline.report(4);                    // 上回离线听的那笔
  adapters.postPlay = async (entry) => {      // 这次打开网络是好的
    attempts.push(entry);
    return { status: 200 };
  };
  const rebooted = createPlayOutbox(adapters);
  await rebooted.flush();                     // 开局先补一轮
  assert.deepEqual(attempts, [{ track_id: 4, played_at: 1000 }]);
  assert.deepEqual(stored(), []);
});
