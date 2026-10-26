"""My Music 画中画迷你播放窗测试 (1.8.105, 用户点名「pc 版本支持画中画
模式」; 1.8.106 改失焦自动开; 1.8.107 修用户实报「来回切换页面, 画中画
就没了」: Chrome 只许赶在最近用户手势 (~5 秒) 里 requestWindow, 回焦即关
的小窗再想弹开时手势早过期 —— 小窗改长驻; 1.8.141 方形跟唱重排: 上半屏
歌词跟唱滚动, 遥控横条沉窗底): Chrome 的 Document
Picture-in-Picture API 开一枚总在最前的小窗遥控主页播放器 —— 音频照旧
留在主页 #audio (PiP 窗只是遥控器), 控制键回连主页播放函数。探测不到 API
的浏览器整个模块歇着。静态文本断言, 不开真浏览器。"""
from tests.music_static_files import MUSIC_STATIC, music_page_shell


def test_music_pip_wiring():
    """模块/样式的接线: music-pip.js 挂在 boot 之前, 小窗样式自带
    music-pip.css (PiP 文档不吃主页样式 —— 独立 <link> 挂进 pip 文档,
    主页不挂)。入口键 1.8.106 撤了 (底排回三颗键), 全 html/CSS 不留痕。"""
    html = music_page_shell()
    pip_js = (MUSIC_STATIC / "js" / "music-pip.js").read_text(encoding="utf-8")
    player_css = (MUSIC_STATIC / "css" / "music-player.css").read_text(
        encoding="utf-8")
    desktop_css = (MUSIC_STATIC / "css" / "music-desktop.css").read_text(
        encoding="utf-8")
    # 模块在 boot 之前加载; 样式文件被 JS 挂进 pip 文档 (主页不挂)。
    # 1.8.141 拆分: 歌词机器单独成 music-pip-lyrics.js (301 行撞 200 行帽,
    # 顺播放页当年的拆法分家)。歌词模块必须排在窗体模块**前面** — 窗体
    # 模块顶层就跑 bindPip(), 挂监听时要解引用歌词函数, 反着排会在加载
    # 当场炸 ReferenceError, timeupdate 两条再也挂不上
    assert html.index("music-pip-lyrics.js?v=1") \
        < html.index("music-pip.js?v=4") \
        < html.index("music-app-boot.js")
    assert "/music/static/css/music-pip.css?v=" in pip_js
    assert "music-pip.css" not in html
    # 1.8.106 撤入口键: 播放页底排回到三颗, 基线藏/键鼠端放行那对规则一起撤
    assert "fp-pip-btn" not in html
    assert "fp-pip-btn" not in player_css and "fp-pip-btn" not in desktop_css
    # API 探测: 没这 API 的浏览器 (Firefox/Safari) 模块歇着, 不是报错
    assert '"documentPictureInPicture" in window' in pip_js
    assert "documentPictureInPicture.requestWindow(" in pip_js


def test_music_pip_auto_trigger():
    """失焦自动开 (1.8.106) → 小窗长驻 (1.8.107 修「来回切换页面, 画中画
    就没了」): Chrome 只许赶在最近用户手势 (~5 秒) 里开窗, 回焦即关的小窗
    再想弹开时手势早过期, 被 NotAllowedError 拦下 —— 收窗那条路整个撤了。
    现在的规矩: blur 后观望 300ms 还没回焦、还正在播、用户没亲手 ✕ 过、
    手上还没开着, 才开; 回焦只清观望计时不收窗; 亲手 ✕ (pagehide 不是我们
    代关的) 这一页会话不再自动弹; 主页收页不留孤儿窗。手势没赶上被浏览器
    拒时静默作罢不炸页面。"""
    pip_js = (MUSIC_STATIC / "js" / "music-pip.js").read_text(encoding="utf-8")
    # 失焦 → 观望 300ms → 还没回焦且正在播且没亲手关过才开
    assert 'window.addEventListener("blur"' in pip_js
    assert "pipOpenTimer = setTimeout(async () => {" in pip_js
    assert "if (document.hasFocus() || !playerIsPlaying() || pipDismissed) return;" \
        in pip_js
    assert "}, 300);" in pip_js
    # 手势没赶上被浏览器拒: 静默兜住 (try/catch), 页面不炸
    assert "await openPipWindow();" in pip_js
    assert "catch (_error) {" in pip_js
    # 回焦: 只清观望计时, 不再收窗 (1.8.107 —— 收了这小窗就再也弹不回来)
    focus_js = pip_js[pip_js.index('window.addEventListener("focus"'):
                      pip_js.index('window.addEventListener("pagehide"')]
    assert "clearTimeout(pipOpenTimer);" in focus_js
    assert "closePipWindow" not in focus_js
    # 亲手 ✕ 过的小窗这会话不再自动弹 (我们代关的不算嫌弃)
    assert "let pipDismissed = false;" in pip_js
    assert "if (!pipClosingByApp) pipDismissed = true;" in pip_js
    # 主页收页不留孤儿窗; 开着就不重开; 小窗自己的 pagehide 清引用+记账
    assert 'window.addEventListener("pagehide", closePipWindow);' in pip_js
    assert "if (pipWindow && !pipWindow.closed) return;" in pip_js
    assert 'pipWindow.addEventListener("pagehide"' in pip_js


def test_music_pip_window_contract():
    """小窗的行为契约: 音频留在主页 (小窗只是遥控器 —— 不挪 <audio>、不
    自己播), 控制键回连主页播放函数; playerNext 必须包一层箭头函数 ——
    裸挂 addEventListener 会把 click 事件对象当 forceAutoplay 传进去
    (队列会在没播的时候也自动续曲)。换曲/播停/进度全从主 #audio 的原生
    事件同步, 窗没开时早退。"""
    pip_js = (MUSIC_STATIC / "js" / "music-pip.js").read_text(encoding="utf-8")
    for frag in ['audio.addEventListener("play", updatePipChrome)',
                 'audio.addEventListener("pause", updatePipPlayButton)',
                 'audio.addEventListener("loadedmetadata", updatePipChrome)',
                 'audio.addEventListener("timeupdate", updatePipProgress)',
                 'const bar = pipWindow && pipWindow.document'
                 '.getElementById("pip-progress");']:
        assert frag in pip_js, f"画中画缺 {frag}"
    # 小窗里不建第二个音频源 (画中画 = 遥控器, 双声部是事故)
    assert "new Audio(" not in pip_js and "createElement(\"audio\")" not in pip_js
    # 三颗控制键回连主页播放函数; next 包箭头 (forceAutoplay 那个坑)
    assert 'getElementById("pip-prev").addEventListener("click", playerPrevious)' \
        in pip_js
    assert 'getElementById("pip-play").addEventListener("click", playerToggle)' \
        in pip_js
    assert 'getElementById("pip-next").addEventListener("click", () => playerNext())' \
        in pip_js


def test_music_pip_css_standalone():
    """小窗样式自带全套 (PiP 文档不吃主页样式): 调色板照抄 music-base.css
    一份硬写进文件 (纯黑底/白字/苹果红进度); 1.8.141 起窗是方形跟唱版 ——
    上歌词下遥控条, 文字行省略号截断, 不把三键挤出窗。"""
    pip_css = (MUSIC_STATIC / "css" / "music-pip.css").read_text(encoding="utf-8")
    for frag in ["background: #000;", "color: #f5f5f7;",
                 "background: #fa2d48;",        # 进度线 = 主题红
                 "text-overflow: ellipsis;",
                 "color-scheme: dark;",         # 原生滚动条/控件也走深色
                 "display: flex;", "object-fit: cover;"]:
        assert frag in pip_css, f"pip 样式缺 {frag}"
    # 封面 64 方 + 三键圆钮 36 (遥控器的密度, 不是播放页的仪式感)
    assert "width: 64px;" in pip_css and "height: 64px;" in pip_css
    assert "width: 36px;" in pip_css and "border-radius: 50%;" in pip_css


def test_music_pip_lyrics():
    """1.8.141 方形跟唱窗 (用户点名「当前界面沉在下面, 上面显示滚动歌词,
    整体是个方形的界面」): 窗 360 方, 上半屏歌词 + 底部原遥控横条。词走
    主页同一份缓存/解析/行定位/对齐微调 (没缓存现拉, 与播放页 loadLyrics
    同配方), 滚动动画走 pipWindow 自己的 requestAnimationFrame —— 主页
    切后台被浏览器限帧, 小窗自己可见照常跑帧, 词不卡; 手动滑词暂停跟唱、
    静置回跟 (窗口常数与播放页同一个 LYRICS_FOLLOW_RESUME_MS), 自己动画
    写的滚动不算手动。"""
    pip_js = (MUSIC_STATIC / "js" / "music-pip.js").read_text(encoding="utf-8")
    pip_lyr = (MUSIC_STATIC / "js" / "music-pip-lyrics.js").read_text(
        encoding="utf-8")
    pip_css = (MUSIC_STATIC / "css" / "music-pip.css").read_text(encoding="utf-8")
    # 方窗 + 上词下条的结构 (窗体/遥控在 music-pip.js, 词的机器在
    # music-pip-lyrics.js — 1.8.141 拆分, 301 行撞 200 行帽)
    assert "{ width: 360, height: 360 }" in pip_js
    assert 'id="pip-lyrics"' in pip_js and 'class="pip-bar"' in pip_js
    assert "bindPipLyrics(" in pip_js
    # 词 = 主页同源: 缓存/解析/行定位/对齐微调; 没词垫空态, 纯文本整页清晰
    for frag in ["lyricsCache", "parseLyrics(", "activeLyricIndex(",
                 "lyricsOffsets", "这首歌没有歌词", 'classList.toggle("static"']:
        assert frag in pip_lyr, f"画中画歌词缺 {frag}"
    # 帧走 pipWindow 自己的 rAF; 手动滑词静置回跟用播放页同一常数;
    # 滚动目标钳到可达区间 (头几行目标为负 / 短词不满一屏时目标超过
    # 最大可滚距离 — 两头不钳则缓动永不收敛); 步长地板 1px (scrollTop
    # 取整环境 <1px 步子原地踏步, 尾巴走不完)
    assert "pipWindow.requestAnimationFrame" in pip_lyr
    assert "LYRICS_FOLLOW_RESUME_MS" in pip_lyr
    assert "Math.max(0, Math.min(" in pip_lyr
    assert "container.scrollHeight - container.clientHeight" in pip_lyr
    assert "Math.abs(step) < 1 ? (step < 0 ? -1 : 1) : step" in pip_lyr
    # 手指按下那一刻先撤动画清宽限 (播放页同款): 不然动画追行中上手滑,
    # 头几拍 scroll 会被当成自己写的, 跟手指抢
    assert "container.addEventListener(\"pointerdown\", () => {" in pip_lyr
    assert "cancelPipLyricsScroll();\n    pipSelfScrollUntil = 0;" in pip_lyr
    # 换曲重铺: 高亮有防串门闩 (窗里铺的词必须对上当前曲才动)
    assert "pipLyricsTrackId !== currentTrack.track_id" in pip_lyr
    # 样式: 歌词行清晰度分工 + 上下渐隐 + 藏滚动条; 底条血线分隔
    for frag in [".lyrics-line", ".lyrics-line.active", ".lyrics-line.upnext",
                 ".lyrics-empty", "mask-image", "scrollbar-width: none",
                 ".pip-bar", "border-top: 1px solid"]:
        assert frag in pip_css, f"pip 样式缺 {frag}"
