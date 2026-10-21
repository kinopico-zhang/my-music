# shots/ — README 全页截图复刻管线

把 README 的 8 张 iPhone 17 Pro 设备截图 (docs/screenshot-*.png) 从零复刻出来:
真实数据实例 → 无头射手 → 官方边框合成, 三步。全部中间产物落在 `$SHOTLAB`
(默认 `~/shotlab`, 可再生, 不进仓; 挪出 /tmp 后快照库与中间产物跨重启存活);
本目录只进脚本与自制资产。

`pylint`/`mypy` 只扫 `app`/`tests`, 本目录不参与静态检查。

与 my-tesla 的种子管线不同, 本仓截图口径是**真实数据** (用户确认不涉隐私):
曲库、收听史、歌单都来自生产库的快照 —— 不是假数据, 所以最近播放/排行
榜里是真实的听歌记录, 封面墙是真实的专辑封面。

## 一次性准备

1. **边框** (Apple 官方资产, 不可再分发, 不进仓): 从
   [design resources](https://developer.apple.com/design/resources/) 下载
   `Bezel-iPhone-17.dmg` 解出 `010_1350x2760.png` 放到
   `$SHOTLAB/bezel-png/` (解法见 my-tesla 仓 `shots/undmg.py`, 纯 python
   解 UDIF; 跑过 my-tesla 管线的机器资产已在, 跳过)。
2. **字体** (截图里的中文要与 macOS 观感一致): 苹方三字重
   `PingFangSC-Regular/Medium/Semibold.otf` 装到 `~/.fonts/pingfang/` 后
   `fc-cache -f`。页面 CSS 字体栈点名 `"PingFang SC"`。
3. **无头浏览器环境** (本机 WSL 的 chromium 缺系统库):
   `LD_LIBRARY_PATH=/home/admin/pwlibs/extracted/usr/lib/x86_64-linux-gnu`,
   Python 环境带 `playwright` + `Pillow` (合成用)。
4. **数据源** (真实口径的三件, 只读):
   `SHOT_SOURCE_DB` 曲库索引 / `SHOT_SOURCE_USERS` 账号库 /
   `SHOT_SOURCE_SECRET` 会话密钥。

## 三步流程

```bash
# 1. 真实数据实例: 快照生产曲库库 (sqlite backup API 一致性快照) + 账号库
#    与密钥的副本, 全落 $SHOTLAB/music-real/ —— 生产文件全程只读零写入。
#    打印 READY (含艺人/专辑/曲目计数) 后保持存活。
#    曲库库已在即整库复用 (重拍快照: SHOT_RESEED=1)。
SHOT_SOURCE_DB=<生产 music.db> \
SHOT_SOURCE_USERS=<生产 users.db> \
SHOT_SOURCE_SECRET=<生产 .session_secret> \
.venv/bin/python shots/real_server.py 8906

# 2. 射手: 8 个视图各一张 (推入动画一律等收尾; 播放器是点开真播放 +
#    seek 定格副歌高亮行的特例流程)。
#    原图 → $SHOTLAB/pages/music-<视图>.png。可带过滤词只拍一张, 如 `player`。
LD_LIBRARY_PATH=... /tmp/pw-verify/bin/python shots/shoot.py

# 3. 合成: 官方 bezel + 状态栏/时间/电池/home bar → $SHOTLAB/final/
#    (与 my-tesla 的 composite.py 同配方, 只换了 glob)。
LD_LIBRARY_PATH=... /tmp/pw-verify/bin/python shots/composite.py

# 4. 收尾: cp $SHOTLAB/final/music-*.png docs/screenshot-<视图>.png,
#    README 截图墙对齐, 提交 (纯图片提交不用等 CI)。
```

## 文件

| 文件 | 职责 |
|---|---|
| `real_server.py` | 真实数据实例: 快照生产曲库库 + 复制账号库/密钥到 `$SHOTLAB/music-real/` (工作目录内只读使用, 封面缓存天然落快照侧不污染生产); 组合仓布局的默认路径探不到时用 `SHOT_SOURCE_*` 显式给 |
| `shoot.py` | 8 视图射手: 每视图独立 context 清 `music.lastRoute` (开局回跳会抢导航), 等数据锚点 + 动画收尾; 收听史/排行按账号记, 用真实账号的 uuid 自签会话 cookie (`/api/login` 同配方); 播放器特例: 专辑页点曲 → 迷你条 → 全屏 → 开歌词 → seek 到副歌, 高亮行直接锚定「我也知道 天空多美妙」那句 |
| `composite.py` | 官方 bezel 合成: 预乘缩放 (透明留白 RGB 不渗边) + 洞形蒙版 (方角内容出不了圆角开窗) + 底部 34px 安全区拉伸补齐 (与 my-tesla 同源) |
| `assets/icons/` | 状态栏电池/信号与 home bar 图标 (自制, 随仓) |

## 真实数据口径

- 曲库快照 = 生产库 sqlite backup 一致性拷贝; 账号库与会话密钥**复制**到
  `$SHOTLAB/music-real/` 再用, 生产文件全程只读。
- 最近播放 / 播放排行按账号 uuid 记, 所以射手要用真实账号身份: 读账号
  副本取 uuid, 与 `/api/login` 同配方自签 7 天会话 cookie —— 榜上是
  真实的听歌史, 不是射手账号的空榜。
- 音乐文件直读生产曲库目录 (sshfs 只读挂载), 封面缓存自动落在快照库
  同目录的 `music-art/`, 生产侧零写入。
