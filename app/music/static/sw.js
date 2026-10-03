// sw.js — My Music 的 Service Worker (scope /music):
//  - 曲目音频流: 1.8.59 起播放全程绕开 SW —— 流媒体请求带 ?direct 标记
//    (fetch 监听里放行直连), 已下载的由页面直读 Cache API 成 blob;
//    起因: iOS 锁屏会冻结 SW, 插在音频管线里的流会断粮自停 (开屏解冻
//    又自动续播)。serveTrack 只兜还没换到新壳的旧缓存页;
//  - 封面图: 缓存优先 —— 后端虽已发长缓存头, iOS 的 HTTP 缓存容易被系统
//    整体清掉, 50k 曲库一刷列表就是几百张图全回源; Cache API 里存一份,
//    系统清不动 (配合 storage.persist), 只在没缓存过时才走网络;
//  - 列表数据 (/music/api/ 的 GET, search 除外): 网络优先, 顺路存档 ——
//    断网时回上次拉到的 (1.8.4 用户点名「断网播放列表都打不开」:
//    壳和封面本来就缓存, 数据也缓一份, 联网打开过的页离线都能翻;
//    401/403 = 换人了, 整档清掉免得串账号);
//  - 应用壳 (页面 + 静态资源): 网络优先, 顺路存进缓存 —— 断网时页面也打得开,
//    已下载的歌照播 (已下载栏读的是本机索引, 不走接口);
//  - activate 时清掉旧版壳/数据缓存 + 接管已打开的页面 (clients.claim,
//    不用等重载)。
//  下载取流同样带 ?direct (拉网络的字节不经 SW, 落盘仍走页面 Cache API)。
//  注意: 只在安全上下文 (HTTPS / localhost) 能注册, 明文 HTTP 下不存在。
"use strict";

const DOWNLOAD_CACHE = "music-downloads-v1";
// 壳缓存 v121 (2026-10-01 1.8.130 补: 分享页接真音质行 —— 用户问「共享播放页面怎么没有音乐质量的内容」, 应用的 /api/tracks/{id}/quality 要登录会话, 访客没有: 后端新开 /share/{token}/quality/{id} 公开口 (同一条取数通道: 索引走库/老行现读回填, 只放行这份分享里有的), music-player-quality 抽出 qualityURL 全局 (v1→v2, stageCardSrc 同款覆盖法), 分享页三枚 art-quality 上屏跟卡飞 (css 直引 music-player-quality.css), share-viewer-stage 撤三钩子空转换 qualityURL 覆盖 (v1→v2), share-viewer-playback 换曲铺场 fillStageQuality (v8→v9)); // 壳缓存 v120 (2026-10-01 1.8.130 分享播放页对齐应用播放器, 用户点名「样式和普通播放页面一样, 3d切换封面, 按钮也保持一致」): 全屏播放页整块重造 —— 样式直接引应用的 music-player.css/music-queue.css (不再自己 fork 一份), 3D 封面舞台整用 music-player-art-stage (取址覆盖 stageCardSrc 走分享 token 公开路由, 音质条三钩子空转), 队列模型换应用的 player-queue.js (三态循环键 列表/单曲/随机 + 待播队列面板点行跳播 + 「回到当前句」浏览歌词); share html 换 #full-player 容器, share-viewer-data/-playback/-fullpage/-lyrics/-events 重写, 新拆 share-viewer-stage.js/share-viewer-queue.js, share-viewer-player.css 收成迷你条+分享侧补丁 (v10→v11); // 壳缓存 v119 (2026-09-30 1.8.129 音质条跟封面 3D 翻面进出 (用户点名「和封面一起 3D 滚动进入退出」)): 1.8.128 的单条静态居中改成每张卡一条 —— 上一首/当前/下一首三条, 各随各的封面槽位姿态飞进退出 (盒子与卡同宽同左缘+顶边钉卡底, poseCard 同参直落: 同宽保 translateX% 同距, rotateY 同轴 → 文字刚体跟飞不自转); 程序切歌的交班溶解也带上旧曲的字; 取数按曲缓存 (邻曲当邻居时就备好, 滑进来字早在); 新拆 music-player-quality.js / music-player-quality.css (player.css 顶到 200 行上限), 音质取数逻辑从 player-chrome 挪出 (art-stage v8→v9 挂姿态接线 / player-chrome v9→v10 / music-player.css v25→v26 撤旧单条规则); // 壳缓存 v118 (2026-09-30 1.8.128 音质行挪窝: 1.8.127 把 格式·采样率/位深·码率 那行塞在艺人名下面, 跟左对齐的曲名/艺人挤成一摞 —— 用户点名「放在封面下面, 居中」: 挪进封面舞台绝对定位, 贴封面正下方 10px 居中 (卡底恰在舞台 90% 高, 跟着封面走), 歌词/队列视图随舞台一起藏; music-player.css v24→v25); // 壳缓存 v117 (2026-09-30 1.8.127 播放页音质行: 封面下加一行当前歌曲的 格式·采样率/位深·码率 (如 FLAC · 44.1kHz / 16bit · 1049kbps); 索引加了采样率/位深/声道三列 (扫描顺手入库), 老库行没这些值 —— 增量重扫对没变的文件不读标签, 永远补不上, 所以新开 /api/tracks/{id}/quality 按需现读文件回填 (每首最多读一次, 之后走库); 码率 = 文件大小/时长 (有损无损都适用), 有损没有位深只显 kHz+kbps, 读不到整行藏; player-chrome v8→v9 / music-player.css v23→v24); // 壳缓存 v116 (2026-09-30 1.8.126 修「列表里点不动」(用户实报 Yashima 行点不动): ① 播放列表行触摸按住 200–500ms 的慢点按原本被拖拽预备吞掉尾随 click (「按住=想拖, 抬手不开播」—— 键鼠端没这道闸, 手机专属; 点得慢一点整列表就像死了一样) —— 现在只有真拖动过 (位移>8px/落定换序) 才吞, 按住没动抬手照旧开播; ② 长按 500ms 的吞点旗原在开菜单之前置, openTrackMenu 早退 (行禁用/曲目找不着) 时菜单没现身旗却挂着, 这一行所有点击被无声吞到点别处为止 —— 改成菜单真开了才置旗; playlist-drag / menu-gestures v6→v7); // 壳缓存 v115 (2026-09-30 1.8.125 修部署后播放不了: 1.8.124 部署窗口里编辑到一半的 audio-events.js?v=16 (还带着内联 const playOutbox) 被 live 服务发给手机进了不可变缓存, 部署后与新接线脚本的 const playOutbox 撞名 → audio-events 整个 SyntaxError 没执行, startAudio 全灭点歌无声; audio-events v16→v17 / play-outbox v1→v2 换新 URL 强制回源); // 壳缓存 v114 (2026-09-30 1.8.124 播放计数离线补报: 出声即上报原来是发后不管, 断网/服务重启/5xx 窗口里听过的歌就永久丢了 (排行缺账, 用户问「你的播放排行, 数据有丢失过吗」) —— 报不上先暂存 localStorage (play-outbox.js, node 直测), 开局/回网 (online)/回前台 (visibilitychange) 按真实播放时刻补报, 排行按时刻落区间不错档; 404 (曲目已删) 丢弃不重试, 队列封顶 500 丢最老; 服务端 /api/plays 收可选 played_at (越界落回当下, last_played_at 不被晚到的旧账拉回去), 5xx 也算失败进队列 —— 原先 fetch 不查状态码, 服务端报错被当成功); // 壳缓存 v113 (2026-09-29 1.8.123 播放列表改名陈货: 改了列表名收层回去, 列表页/主页还写着旧名 —— 底下的层收层回去不重铺 (1.8.80 老坑), 名字不就地换返回看到的就是旧名 (1.8.99 换封面修过同款); refreshPlaylistName 改名当场把底下那行/那张卡的名字换新); // 壳缓存 v112 (2026-09-29 1.8.122 缓存真查: 用户点名「Safari 会随机清空缓存, 哪些歌缓存了不能看下载记录, 要检查缓存里到底有没有」—— 播放入口 localBlobFor 撞到「索引说下载过、字节却读不出」当场 removeDownload 出账, 行图标跟着翻; 对账触发面从开局/回前台扩到 bfcache 恢复 (pageshow) + 路由重铺 (reconcileLocalAudioStoresSoon, 15s 节流) —— Safari 清仓不一定挑后台, 正翻着列表也能被清, 重铺即翻正); // 壳缓存 v111 (2026-09-29 1.8.121 循环两态同窗: 列表/单曲循环键的 loop 切换时整体平移 1.72px (1.8.118 起两态各开各的 viewBox 窗口, 同一枚环落在两扇窗里屏上位置就不同) —— 列表态弃用自己的居中窗, 与单曲态共用同一扇 (圆片出角要的那扇), 同枚环 d + 同窗 = 切换零平移, 点击感觉只是多了个「1」圆片; 代价是列表态的环在窗内偏左 95 单位 (24px 渲染 1.72px), 光心居中让位给两态重叠 —— 用户点名「loop 的形状要完全重叠」); // 壳缓存 v110 (2026-09-29 1.8.120 单曲徽章护城河: 圆片边缘外 1px 一圈原本有两处环墨贴脸 —— 顶杆右端撞进圆片左缘 + 右杆从圆片底缘冒出, 圆片看着跟循环 logo 长在一起; 两枚 −1 绕向守卫 (旗副本同款) 内沿收在圆片边缘弧、外沿 R+55.4 同心弧、侧沿与环自己的边反向重合, 带内环墨归零露底色 —— 用户点名「圆圈周围要有镂空, 不要跟循环图标连在一起」); v109 (2026-09-29 1.8.119 单曲徽章镂空净区: 「1」竖笔右侧骑在环右杆杆头上, 杆头墨从镂空里漏出来 —— 加 −1 绕向杆头副本 (旗副本同款) 抵消圆片盖住的杆头, 镂空里只剩底色, 圆片外的杆不动 —— 用户点名「透过镂空能看到下面的循环 logo」); v108 (2026-09-29 1.8.118 单曲循环徽章右移出角: 圆片整体右移 190 戳出环外顶到视框右上角 (右沿到视框宽 99.6%, 参照 100%), 「1」随圆片平移, 视框各开各的窗口边长不动 —— 用户点名「1 应该再往右边一点」, 参照 svg); v107 (2026-09-29 1.8.117 单曲循环徽章按用户参照 logo 重定尺寸: 圆片 Ø 放大 65% 到占图宽 47.8%, 顶/右沿与环极值齐平, 「1」高占圆片一半 —— 1.8.116 只放数字不放圆片, 用户点名「还是很小」); v106 (2026-09-29 1.8.116 徽章「1」放大: 右上角圆片里的「1」绕圆心再放大 19%, 高占圆片 ¾ —— 用户点名「有点小」); v105 (2026-09-29 1.8.115 单曲循环「1」徽章挪 logo 右上角: 圆片盖住折角箭头旗顶到视框顶, 顶杆流入圆片成 iOS 角标款); v104 (2026-09-29 1.8.114 长标题墨迹对齐: 收进顶栏的换行长标题按第一行字面左缘落位 —— 原先拿标题框对齐, 居中排版把第一行排在框中间, 框对了字没对 (用户三报「还是没改好」)); v103 (2026-09-29 1.8.113 并齐收紧: 上划收封面的头 22% 行程里标题/艺人名就左对齐 —— 宽的那行当锚走原路, 窄的那行追平 (只向左追不逆行), 修「感觉前面有空格」); v102 (2026-09-29 1.8.112 封面收缩两改: 标题/艺人名收缩途中一路左对齐 (副标题左缘跟主标题走, 居中错位 (1-p)^3 早收), 长标题不缩字号 (宽度退出缩放, 溢出右刀在条簇左缘裁+渐隐纱盖软)); v101 (2026-09-28 1.8.111 随机播放/循环键换实底新图标: 列表·单曲·随机三态+随机播放键同批换装, 单曲「1」徽章收环心, 切换循环环不跳位); v100 (2026-09-28 1.8.110 所有删除二次确认: 左滑红钮点下先问一句, 歌单/列表内曲目/下载/待播队列四口全上, 取消下载不问; 反悔行自动收起); v99 (2026-09-28 1.8.109 修 PC 菜单弹层飞远角: 开时现量菜单键 x, 弹层锚键正上方); v98 (2026-09-28 1.8.108 播放列表鼠标拖拽换序: 键鼠端即按即拖, 触摸端照旧按住 200ms; 行板亮抓手光标); v97 (2026-09-28 1.8.107 修来回切换页面画中画就没了: Chrome 手势规矩下回焦即关弹不回来, 小窗改长驻+亲手关过不再自动弹); v96 (1.8.106 键鼠端两改: 音量条缩到与进度条等长+两端小/大喇叭图标, 画中画改失焦自动开关撤入口键); v95 (1.8.105 画中画迷你播放窗: 播放页底排第四键, Chrome Document PiP 小窗遥控播放, 键鼠端专属); v94 (2026-09-28 1.8.104 键鼠端两改: 播放页音量条挪到标题下整行拉长 + 悬停删除钮改驻留半秒); v93 (2026-09-28 1.8.103 键鼠/触摸·大屏/小屏双轴拆分 + 船坞音量气泡: 触摸端一字节不动); v92 (2026-09-28 1.8.102 桌面键鼠补全: 音量条上桌+箭头快进退+点过的按钮不再吞键); v91 (2026-09-28 1.8.101 存储保卫: 系统悄悄清掉的缓存当场对账出清 + persist 申请 + 预算跟 quota 走); v90 (2026-09-27 1.8.100 后台连播提前接力: 趁上一曲还响着就切, 冻结整页的「无音频空窗」不出现); v89 (2026-09-27 1.8.99 播放列表封面陈货: 换/撤封面后底下列表页·主页的行就地换新图); v88 (2026-09-26 1.8.98 自动缓存换代清仓: 修过的歌手机不再压着旧坏字节); v87 (2026-09-25 1.8.97 播放页封面: 很短的滑行松手也完成切歌, pointercancel 弹回不切); v86 (2026-09-25 1.8.96 修邻曲卡静止露边+横滑只管切歌/首尾侧橡皮筋+出错不自动跳歌); v85 (2026-09-25 1.8.95 气泡滑切三卡横排: 拖动中预览邻曲+封面无缝); v84 (2026-09-25 1.8.94 播放气泡撤上下曲键改左右滑切歌); v83 (2026-09-25 1.8.93 气泡三键紧凑+上下曲裁单三角); v82 (2026-09-25 1.8.92 单曲 "1" 缩小 + 气泡挪封面标题接缝); v81 (2026-09-25 1.8.91 循环键图标并 path 去叠深+缩 24, 气泡上标题居中); v80 (2026-09-25 1.8.90 循环键图标粗描边重画); v79 (2026-09-25 1.8.89 播放页三态循环键+待播列表撤控制); v78 (2026-09-25 1.8.88 播放气泡加回上一首/下一首); v77 (2026-09-24 1.8.87 断网连播两刀: 换源带起播意图修缓存歌停在暂停+断网挂起回前台自动接着放); v76 (1.8.86 幽灵探针进起播入口+解冻自愈); v75 (1.8.85 幽灵播放判定); v74 (1.8.84 起播被拒兜底); v73 (1.8.83 撤自动续播+扫描全手动); v72 (1.8.82 封面 ?v= 跟内容走);
// v71–v67 (1.8.76–1.8.81 最近添加专辑倒排·音频源落定/自动缓存/打断续播/建列表防连点/删列表不留陈货); v66 (1.8.75 艺人页一键刷新元数据);
// v65 (1.8.74 拖进度条剩余时间 0 + 封面方回来); v64 (2026-09-21 1.8.59 锁屏自停根修: 音频流绕开 SW; 1.8.58 队列动条; 1.8.57 账号自助/歌词多厂商/普通账号收走管理员配置);
// v57: 1.8.47+1.8.48: 分享面板带封面 (封面抓成本地文件递 navigator.share); 按钮按下果冻 Q 弹;
// v56: 十改三轮: 层根滚动器外接点条 (惯性里点 播放/… 一下就灵);
// v55: 二轮: 补发上提 document·双通道; v54: 一轮按视觉位置认键补发; v53 补程只管页头收放;
// v52: 八改被吞点按补发; v51 停稳自动补程; v50 键衬底软边; v49 纱钉簇左缘);
// v48: 四改: 开 … 后五颗键等距 (首键让 8px); 飞行不掉帧 (GPU 层, 起飞立即显形);
// v47: 1.8.46 三改: 收拢的键错峰走弧线飞进 … (逐帧算过不叠), 遮罩罩满按钮区, 修了飞行期纱跑偏的根;
// v46: 1.8.46 二改: 收拢的键不再缩小, 全尺寸飞到 … 键上叠成一摞末段化进;
// v45: 1.8.46 收缩顶栏换岗改路径平移: 播放键平移进槽位, 其余四颗收拢进 …, 遮罩拉宽越靠左越透;
// v44: 1.8.45 收缩顶栏改单行: 播放 + … 两颗在封面同行右靠, … 点开四键顶替, 挤到的标题阴影渐隐;
// v43: 1.8.44 蓝牙车机封面实验 (锁屏封面先取成 blob 再设元数据); v42: 1.8.43 视口体检红框撤了, 打点改静默回传;
// v41: 1.8.42 收缩顶栏的标题/副标题左对齐;
// v40: 1.8.41 双指缩放全禁 + 分享页列表行序号换歌曲封面 / 1.8.40 收缩顶栏
// 两行布局·副标题并进上行·短列表补行程·横向晃动修复 / 1.8.39 桌面键鼠
// 适配 —— 换版本号让 activate 清旧账)
const SHELL_CACHE = "music-shell-v123";
const ARTWORK_CACHE = "music-artwork-v1";
// 列表数据档 (1.8.4): /music/api/ 的 GET 全缓存 (search 除外 —— 词组合
// 无限多, 缓存不值), 网络优先断网回档
const DATA_CACHE = "music-data-v1";
const TRACK_URL_PATTERN = /\/music\/media\/stream\/\d+$/;
// 封面族: 专辑/艺人/单曲封面 + 播放列表自定义封面
// (URL 全带 ?v= 版本号, 换图即换址 —— 缓存键跟着换, 不会读到旧图)
const ARTWORK_PATTERN
  = /^\/music\/media\/(?:albums|artists|tracks)\/\d+\/artwork$|^\/music\/media\/playlists\/\d+\/cover$/;
const DATA_PATTERN = /^\/music\/api\/(?!search\b)/;
const SHELL_PATHS = new Set(["/music", "/music/", "/music/login", "/music/changelog"]);

function isShellPath(path) {
  return SHELL_PATHS.has(path) || path.startsWith("/music/static/");
}

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  const path = url.pathname;
  if (TRACK_URL_PATTERN.test(path)) {
    // 1.8.59 锁屏自停根修: 带 ?direct 标记的流不接管 —— iOS 锁屏后系统
    // 冻结 SW, 插在音频管线里的流会断粮自停 (开屏解冻又自动续播)。
    // 不 respondWith, 浏览器媒体栈自己连网络, SW 冻不冻都碍不着。
    if (url.searchParams.has("direct")) return;
    event.respondWith(serveTrack(request));
  } else if (ARTWORK_PATTERN.test(path)) {
    event.respondWith(serveArtwork(request));
  } else if (DATA_PATTERN.test(path)) {
    event.respondWith(serveApiData(request));
  } else if (isShellPath(path)) {
    event.respondWith(serveShell(request));
  }
});

/** 壳资源: 在线用网络的 (顺手把成功的存缓存, 下次断网有得回), 断网回缓存。 */
async function serveShell(request) {
  const cache = await caches.open(SHELL_CACHE);
  try {
    const response = await fetch(request);
    if (response.ok) cache.put(request, response.clone());
    return response;
  } catch (_error) {
    const cached = await cache.match(request);
    if (cached) return cached;
    return new Response("离线且尚未缓存过此页面, 联网打开一次后可离线使用",
      { status: 503, headers: { "Content-Type": "text/plain; charset=utf-8" } });
  }
}

/** 缓存里有就回缓存 (Range 切 206, iOS Safari 拖进度条需要), 没有走
    网络。1.8.59 起页面播放已不经这里 —— 只兜还没换到新壳的旧缓存页。 */
async function serveTrack(request) {
  const cache = await caches.open(DOWNLOAD_CACHE);
  const cached = await cache.match(request.url);
  if (!cached) return fetch(request);
  const rangeHeader = request.headers.get("range");
  if (!rangeHeader) return cached;
  const slice = rangeSlice(await cached.blob(), rangeHeader);
  if (!slice) return cached;              // 解析不出范围: 给全量兜底
  return new Response(slice.body, {
    status: 206,
    headers: {
      "Content-Type": cached.headers.get("Content-Type")
        || "application/octet-stream",
      "Content-Range": `bytes ${slice.start}-${slice.end}/${slice.total}`,
      "Content-Length": String(slice.end - slice.start + 1),
    },
  });
}

/** "bytes=start-end" → 全量 blob 的切片 (end 缺省 = 到尾; 越界钳到尾)。 */
function rangeSlice(blob, rangeHeader) {
  const match = /^bytes=(\d+)-(\d*)$/.exec(rangeHeader.trim());
  if (!match) return null;
  const start = Number(match[1]);
  if (start >= blob.size) return null;
  const end = match[2] ? Math.min(Number(match[2]), blob.size - 1)
    : blob.size - 1;
  return { start, end, total: blob.size, body: blob.slice(start, end + 1) };
}

/** 封面: 缓存优先 (URL 自带 ?v= 版本, 缓存里的内容永不换), 没缓存过才走
    网络并顺手存下。条数封顶防无限膨胀: 超了丢最早一批 (Cache API 没有
    LRU, keys() 顺序近似先来后到, 够用)。 */
async function serveArtwork(request) {
  const cache = await caches.open(ARTWORK_CACHE);
  const cached = await cache.match(request);
  if (cached) return cached;
  const response = await fetch(request);
  if (response.ok) {
    await cache.put(request, response.clone());
    trimArtworkCache(cache);
  }
  return response;
}

async function trimArtworkCache(cache) {
  const keys = await cache.keys();
  if (keys.length <= 600) return;
  for (const key of keys.slice(0, keys.length - 400)) {
    await cache.delete(key);
  }
}

/** 列表数据: 网络优先 (在线永远拿新的), 断网回上次存档 —— 联网打开过的
    页 (播放列表/专辑/艺人/最近播放/统计…) 离线都能翻。401/403 = 登录态
    没了或换人了, 整档清掉免得串账号 (退出登录时页面也清一次)。 */
async function serveApiData(request) {
  const cache = await caches.open(DATA_CACHE);
  try {
    const response = await fetch(request);
    if (response.ok) {
      const type = response.headers.get("Content-Type") || "";
      if (type.includes("application/json")) {
        await cache.put(request, response.clone());
        trimDataCache(cache);
      }
    } else if (response.status === 401 || response.status === 403) {
      const keys = await cache.keys();
      for (const key of keys) await cache.delete(key);
    }
    return response;
  } catch (_error) {
    const cached = await cache.match(request);
    if (cached) return cached;
    return new Response(
      JSON.stringify({ detail: "离线中: 这个页面联网打开过一次就能离线看" }),
      { status: 503, headers: { "Content-Type": "application/json" } });
  }
}

/** 数据档条数封顶 (分页 URL 各占一条, 50k 曲库翻久了会攒出几十条):
    超了丢最早一批 (Cache API 没有 LRU, keys() 顺序近似先来后到)。 */
async function trimDataCache(cache) {
  const keys = await cache.keys();
  if (keys.length <= 120) return;
  for (const key of keys.slice(0, keys.length - 80)) {
    await cache.delete(key);
  }
}

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    // 壳/数据缓存换版本号时清旧账; 下载缓存 (DOWNLOAD_CACHE) 是用户数据, 不动
    const names = await caches.keys();
    for (const name of names) {
      if (name.startsWith("music-shell-") && name !== SHELL_CACHE) {
        await caches.delete(name);
      }
      if (name.startsWith("music-artwork-") && name !== ARTWORK_CACHE) {
        await caches.delete(name);
      }
      if (name.startsWith("music-data-") && name !== DATA_CACHE) {
        await caches.delete(name);
      }
    }
    await self.clients.claim();   // 不等刷新, 已开的页面立刻归我管
  })());
});
