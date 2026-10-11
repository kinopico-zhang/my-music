"""My Music MediaSession 接线测试: 锁屏/控制中心元数据 —— 静态文本
断言, 不碰数据库。拆自 test_music_wiring_library.py (1.8.44 批加测试
把那个文件顶过 200 行硬上限)。"""
from tests.music_static_files import MUSIC_STATIC


def test_music_1844_bluetooth_artwork():
    """1.8.44 蓝牙车机封面 (用户车上实报「锁屏有封面、车机没有」): 特斯拉
    v10 起认蓝牙封面, iOS 13 起会把 now-playing 里的图塞进蓝牙的 AVRCP
    通道 —— 但网页的远程 URL 封面 WebKit 是后台异步取的, 进没进
    now-playing 不保证。对策 = 封面取回本地再重设一次元数据 (本地现成
    数据), 慢一拍的回包按 track_id 闩住别盖新歌, 取图失败维持远程
    URL 那份 (锁屏不退步)。"""
    js = (MUSIC_STATIC / "js" / "music-player-media-session.js").read_text(
        encoding="utf-8")
    assert "function setMediaMetadata(artwork) {" in js
    assert "fetch(artwork).then((resp) => (resp.ok ? resp.blob() : null))" in js
    assert ("if (!blob || !currentTrack || artForTrack === currentTrack.track_id)"
            " return;" in js)
    assert 'setMediaMetadata([remoteEntry]);' in js   # 先远程址兜底


def test_music_18140_tesla_media_card_artwork():
    """1.8.140 车机媒体卡封面 (特斯拉浏览器实报「媒体控制界面只有浏览器
    图标, 没有歌的封面」): 1.8.44 的 blob: 址只有本进程认得, 车机把媒体
    信息递给系统侧的通道一出进程就取不动 blob:; 相对址拼不出请求。对策
    = 封面归一成 ≤512 方 JPEG 的 data URI 重设 (字节自带在址里), 远程
    绝对址 (location.origin 拼全) 垫在第二位当兜底; 大图先过 canvas 压
    身量, 位图路走不通原图字节直接 base64。"""
    js = (MUSIC_STATIC / "js" / "music-player-media-session.js").read_text(
        encoding="utf-8")
    assert ("const artwork = `${location.origin}/music/media/albums/"
            "${currentTrack.album_id}/artwork`;") in js
    assert "async function artworkEntry(blob) {" in js
    assert "await createImageBitmap(blob);" in js
    assert 'canvas.toBlob((out) => resolve(out || blob), "image/jpeg", 0.85)' in js
    assert "reader.readAsDataURL(source);" in js
    assert "setMediaMetadata([localEntry, remoteEntry]);" in js
    assert "URL.createObjectURL" not in js     # blob: 址退役 (出进程取不动)
