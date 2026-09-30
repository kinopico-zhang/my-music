"""My Music 播放页音质行接线测试 (1.8.127 增; 1.8.128 封面正下方居中; 1.8.129
三条跟封面 3D 翻面进出): 每张卡一条 格式·采样率/位深·码率。

后端 /api/tracks/{id}/quality 的扫描入库/按需回填路径在
test_music_endpoints 与 test_music_tags; 这里只钉页面接线。"""
from tests.music_static_files import MUSIC_STATIC, music_page_shell


def test_music_quality_line_wiring():
    """音质行: 页面元素 + 取数接口 + 竞态守门 + 跟卡姿态 + 版本跟内容走。"""
    html = music_page_shell()
    # 三条住在封面舞台里 (各跟各的卡), .fp-now 只剩曲名/艺人
    assert ('<img id="fp-art" class="art-card" alt="">'
            '<small id="fp-quality-prev" class="art-quality" hidden></small>'
            '<small id="fp-quality-next" class="art-quality" hidden></small>'
            '<small id="fp-quality" class="art-quality" hidden></small>') in html
    assert ('<div class="fp-now"><b id="fp-title"></b>'
            '<small id="fp-artist"></small></div>') in html
    assert 'js/music-player-quality.js?v=1"' in html   # 1.8.129 拆独立模块
    assert 'css/music-player-quality.css?v=1"' in html
    assert 'css/music-player.css?v=26"' in html        # 1.8.129 撤旧单条规则
    assert 'js/music-player-chrome.js?v=10"' in html   # 1.8.129 挪出音质逻辑
    js = (MUSIC_STATIC / "js" / "music-player-quality.js").read_text(
        encoding="utf-8")
    for frag in ["function fillStageQuality", "function poseQualityStrips",
                 "function handoffQualityStrip", "function clearQualityHandoff",
                 "function fillStrip", "function qualityText",
                 "function formatQuality", "const qualityCache = new Map()",
                 "`/music/api/tracks/${track.track_id}/quality`",
                 "quality.sample_rate >= 1000000", "kbps", "单声道",
                 "line.classList.toggle(\"off\", !track)",
                 "if (seq !== qualityFetchSeq) return;"]:
        assert frag in js, f"音质模块缺 {frag}"
    # 铺场: 当前曲 + 两侧邻居各就各位 (renderPlayerChrome 一拍)
    chrome = (MUSIC_STATIC / "js" / "music-player-chrome.js").read_text(
        encoding="utf-8")
    assert "void fillStageQuality();" in chrome
    assert "renderTrackQuality" not in chrome   # 1.8.129 挪进独立模块
    # 舞台接线: 姿态同参直落 + 交班成对
    stage_js = (MUSIC_STATIC / "js" / "music-player-art-stage.js").read_text(
        encoding="utf-8")
    assert "poseQualityStrips(sway);" in stage_js
    assert "handoffQualityStrip(stageHandoff);" in stage_js
    assert "clearQualityHandoff();" in stage_js
    assert "/* exported initArtStage, stageNeighbors, poseCard */" in stage_js
    # 几何 (刚体跟飞): 盒子与卡同宽同左缘 + 顶边钉卡底, 侧条开局兜底同参
    css = (MUSIC_STATIC / "css" / "music-player-quality.css").read_text(
        encoding="utf-8")
    for frag in [".art-quality { position: absolute; top: 50%; margin-top: 40%;"
                 " left: 10%; width: 80%;",
                 "text-align: center", "will-change: transform, filter;",
                 "#fp-quality { z-index: 3; }",
                 "#fp-quality-prev { transform: translateX(-55%)"
                 " translateZ(-150px) rotateY(-40deg); }",
                 "#fp-quality-next { transform: translateX(55%)"
                 " translateZ(-150px) rotateY(40deg); }",
                 "#fp-art-wrap.dragging .art-quality { transition: none; }",
                 ".art-quality.off { visibility: hidden; }",
                 ".art-quality.handoff { z-index: 5; }",
                 ".art-quality[hidden] { display: none; }"]:
        assert frag in css, f"音质条样式缺 {frag}"
    # 旧文件撤干净: 单条规则的残留不许回来 (样式已拆家)
    player_css = (MUSIC_STATIC / "css" / "music-player.css").read_text(
        encoding="utf-8")
    assert "#fp-quality" not in player_css
    sw = (MUSIC_STATIC / "sw.js").read_text(encoding="utf-8")
    assert "music-shell-v119" in sw
