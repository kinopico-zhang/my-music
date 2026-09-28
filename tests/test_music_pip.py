"""My Music 画中画迷你播放窗测试 (1.8.105, 用户点名「pc 版本支持画中画
模式」): Chrome 的 Document Picture-in-Picture API 开一枚总在最前的
小窗遥控主页播放器 —— 音频照旧留在主页 #audio (PiP 窗只是遥控器), 控制
键回连主页播放函数。仅键鼠端亮入口 (操作轴), 触摸端基线一个字节不动;
探测不到 API 的浏览器 JS 整键收走。静态文本断言, 不开真浏览器。"""
from tests.music_static_files import MUSIC_STATIC, music_page_shell


def test_music_pip_wiring():
    """入口/模块/样式的接线: 播放页底排第四键 (基线藏, 键鼠端放行),
    music-pip.js 挂在 boot 之前, 小窗样式自带 music-pip.css (PiP 文档
    不吃主页样式 —— 独立 <link> 挂进 pip 文档, 主页不挂)。"""
    html = music_page_shell()
    pip_js = (MUSIC_STATIC / "js" / "music-pip.js").read_text(encoding="utf-8")
    player_css = (MUSIC_STATIC / "css" / "music-player.css").read_text(
        encoding="utf-8")
    desktop_css = (MUSIC_STATIC / "css" / "music-desktop.css").read_text(
        encoding="utf-8")
    # 入口键站底排第四位 (队列键之后), 与音量条同一套分轴规矩
    assert html.index('id="fp-queue-btn"') < html.index('id="fp-pip-btn"')
    assert 'id="fp-pip-btn" aria-label="画中画"' in html
    assert "#fp-pip-btn { display: none; }" in player_css   # 触摸端基线藏
    assert 'html[data-input="keymouse"] #fp-pip-btn { display: flex; }' \
        in desktop_css                                       # 键鼠端放行
    assert 'html[data-size="large"] #fp-pip-btn' not in html  # 不挂尺寸轴
    # 模块在 boot 之前加载; 样式文件被 JS 挂进 pip 文档 (主页不挂)
    assert html.index("music-pip.js") < html.index("music-app-boot.js")
    assert "/music/static/css/music-pip.css?v=" in pip_js
    assert "music-pip.css" not in html
    # API 探测: 没这 API 的浏览器 (Firefox/Safari) 整键收走, 不是报错
    assert '"documentPictureInPicture" in window' in pip_js
    assert "button.hidden = true;" in pip_js
    assert "documentPictureInPicture.requestWindow(" in pip_js


def test_music_pip_window_contract():
    """小窗的行为契约: 音频留在主页 (小窗只是遥控器 —— 不挪 <audio>、不
    自己播), 控制键回连主页播放函数; playerNext 必须包一层箭头函数 ——
    裸挂 addEventListener 会把 click 事件对象当 forceAutoplay 传进去
    (队列会在没播的时候也自动续曲)。窗关了收尾走 pagehide。"""
    pip_js = (MUSIC_STATIC / "js" / "music-pip.js").read_text(encoding="utf-8")
    # 换曲/播停/进度全从主页 #audio 的原生事件同步进小窗, 窗没开时早退
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
    # 窗已开着再点入口 = 聚焦, 不叠第二只; 关窗收尾走 pagehide
    assert "pipWindow.focus();" in pip_js
    assert 'pipWindow.addEventListener("pagehide"' in pip_js
    assert "pipWindow = null;" in pip_js


def test_music_pip_css_standalone():
    """小窗样式自带全套 (PiP 文档不吃主页样式): 调色板照抄 music-base.css
    一份硬写进文件 (纯黑底/白字/苹果红进度), 横条布局一行装下; 文字行
    省略号截断, 不把三键挤出窗。"""
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
