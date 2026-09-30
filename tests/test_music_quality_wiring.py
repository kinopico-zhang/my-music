"""My Music 播放页音质行接线测试 (1.8.127 增, 1.8.128 挪封面正下方居中):
封面下的 格式·采样率/位深·码率。

后端 /api/tracks/{id}/quality 的扫描入库/按需回填路径在
test_music_endpoints 与 test_music_tags; 这里只钉页面接线。"""
from tests.music_static_files import MUSIC_STATIC, music_page_shell


def test_music_quality_line_wiring():
    """音质行: 页面元素 + 取数接口 + 竞态守门 + 隐藏规则 + 版本跟内容走。"""
    html = music_page_shell()
    # 1.8.128 挪进封面舞台 (用户点名「放在封面下面, 居中」), .fp-now 只剩曲名/艺人
    assert ('<img id="fp-art" class="art-card" alt="">'
            '<small id="fp-quality" hidden></small></div>') in html
    assert ('<div class="fp-now"><b id="fp-title"></b>'
            '<small id="fp-artist"></small></div>') in html
    assert 'js/music-player-chrome.js?v=9"' in html    # 1.8.127 音质行改版
    assert 'css/music-player.css?v=25"' in html        # 1.8.128 挪窝
    js = (MUSIC_STATIC / "js" / "music-player-chrome.js").read_text(
        encoding="utf-8")
    assert "async function renderTrackQuality" in js
    assert "void renderTrackQuality(track);" in js     # 换曲即取 (loadTrack 一拍)
    assert "`/music/api/tracks/${track.track_id}/quality`" in js
    assert "currentTrack !== track" in js              # 迟到应答不盖新歌
    assert "quality.sample_rate >= 1000000" in js      # DSD 显 MHz, CD 显 kHz
    assert "kbps" in js
    # 贴封面正下方居中: 卡底恰在舞台 90% 高, 绝对定位跟着封面走
    css = (MUSIC_STATIC / "css" / "music-player.css").read_text(
        encoding="utf-8")
    assert "#fp-quality { position: absolute; top: 90%; margin-top: 10px" in css
    assert "text-align: center" in css
    # 显式藏: 自己的 display 类规则一旦出现会盖掉 UA 的 [hidden], 1.8.127 撞过
    assert "#fp-quality[hidden] { display: none; }" in css
    sw = (MUSIC_STATIC / "sw.js").read_text(encoding="utf-8")
    assert "music-shell-v118" in sw
