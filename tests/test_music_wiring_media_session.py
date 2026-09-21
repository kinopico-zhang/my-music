"""My Music MediaSession 接线测试: 锁屏/控制中心元数据 —— 静态文本
断言, 不碰数据库。拆自 test_music_wiring_library.py (1.8.44 批加测试
把那个文件顶过 200 行硬上限)。"""
from tests.music_static_files import MUSIC_STATIC


def test_music_1844_bluetooth_artwork():
    """1.8.44 蓝牙车机封面 (用户车上实报「锁屏有封面、车机没有」): 特斯拉
    v10 起认蓝牙封面, iOS 13 起会把 now-playing 里的图塞进蓝牙的 AVRCP
    通道 —— 但网页的远程 URL 封面 WebKit 是后台异步取的, 进没进
    now-playing 不保证。对策 = 封面 fetch 成 blob 再重设一次元数据 (本地
    现成数据), 慢一拍的回包按 track_id 闩住别盖新歌, 取图失败维持远程
    URL 那份 (锁屏不退步)。"""
    js = (MUSIC_STATIC / "js" / "music-player-media-session.js").read_text(
        encoding="utf-8")
    assert "function setMediaMetadata(artSrc, artType) {" in js
    assert 'artwork: [{ src: artSrc, sizes: "512x512",' in js
    assert "fetch(artwork).then((resp) => (resp.ok ? resp.blob() : null))" in js
    assert "URL.createObjectURL(blob);" in js
    assert "URL.revokeObjectURL(artBlobURL);" in js
    assert ("if (!blob || !currentTrack || artForTrack === currentTrack.track_id)"
            " return;" in js)
    assert "setMediaMetadata(artBlobURL, blob.type);" in js
    assert 'setMediaMetadata(artwork);' in js      # 先远程 URL 兜底, 再 blob 补
