"""My Music 播放页音质行接线测试 (1.8.127): 封面下的 格式·采样率/位深·码率。

后端 /api/tracks/{id}/quality 的扫描入库/按需回填路径在
test_music_endpoints 与 test_music_tags; 这里只钉页面接线。"""
from tests.music_static_files import MUSIC_STATIC, music_page_shell


def test_music_quality_line_wiring():
    """音质行: 页面元素 + 取数接口 + 竞态守门 + 隐藏规则 + 版本跟内容走。"""
    html = music_page_shell()
    assert '<small id="fp-quality" hidden></small>' in html
    assert 'js/music-player-chrome.js?v=9"' in html    # 1.8.127 音质行改版
    assert 'css/music-player.css?v=24"' in html
    js = (MUSIC_STATIC / "js" / "music-player-chrome.js").read_text(
        encoding="utf-8")
    assert "async function renderTrackQuality" in js
    assert "void renderTrackQuality(track);" in js     # 换曲即取 (loadTrack 一拍)
    assert "`/music/api/tracks/${track.track_id}/quality`" in js
    assert "currentTrack !== track" in js              # 迟到应答不盖新歌
    assert "quality.sample_rate >= 1000000" in js      # DSD 显 MHz, CD 显 kHz
    assert "kbps" in js
    # .fp-now small 的 display:block 会盖掉 UA 的 [hidden] 样式 —— 必须显式藏,
    # 不然没数据时那行空占位
    css = (MUSIC_STATIC / "css" / "music-player.css").read_text(
        encoding="utf-8")
    assert "#fp-quality[hidden] { display: none; }" in css
    sw = (MUSIC_STATIC / "sw.js").read_text(encoding="utf-8")
    assert "music-shell-v117" in sw
