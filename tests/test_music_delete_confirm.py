"""My Music 删除二次确认测试 (1.8.110 用户点名「删除歌单应该给二次确认,
所有的删除都要二次确认」): 全应用每一条删除执行口都得先过一道
window.confirm (与改名 prompt 同款原生对话) —— 左滑红色删除钮不再点按
即删; 确认文案点名道姓 (删哪个列表/哪首歌)。反悔/失败时左滑行自动收起
(swipe 模块统一收尾, 消费方不用各家记)。静态文本断言, 不开真浏览器。"""
from tests.music_static_files import MUSIC_STATIC


def _js(name):
    """读一个静态 js 模块的原文。"""
    return (MUSIC_STATIC / "js" / name).read_text(encoding="utf-8")


def test_every_delete_path_confirms():
    """删除路径全盘点 (1.8.110 补上四处裸删; 原有三处保持, 别回退): 歌单
    列表左滑删列表 (用户主诉) / 列表详情页删列表钮 + 顶栏动作条 (同一闭包)
    / 列表内左滑移除曲目 / 已下载左滑删下载 / 已下载多选删 / 待播队列左滑
    移除 / 播放列表封面移除。下载中那颗是「取消」不是删除, 不确认。"""
    for name, frag in [
        # 1.8.110 新上四道 (原先点按即删)
        ("music-playlists-pane.js",
         "window.confirm(`删除播放列表「${name}」?`)"),
        ("music-playlist-view.js",
         "window.confirm(`从「${playlist.name}」移除「${title}」?`)"),
        ("music-downloads-pane.js", "window.confirm(`删除「${title}」的下载?`)"),
        ("music-player-queue-view.js",
         "window.confirm(`从待播列表移除「${title}」?`)"),
        # 原有三道 (盘点时已在): 保持住
        ("music-playlist-view.js",
         "window.confirm(`删除播放列表「${playlist.name}」?`)"),
        ("music-downloads-select.js", "删除选中的 ${dlSelected.size} 首?"),
        ("music-menu-gestures.js",
         "window.confirm(`移除「${coverMenuPlaylistName}」的自定义封面?`)"),
    ]:
        assert frag in _js(name), f"{name} 删除确认缺 {frag}"
    # 名字从行上现取 (列表页行内 .a-main b / 队列行 .q-title), 查不到兜底
    assert 'wrap.querySelector(".a-main b")' in _js("music-playlists-pane.js")
    assert 'wrap.querySelector(".q-title")' in _js("music-player-queue-view.js")


def test_swipe_delete_cancel_settles_row():
    """反悔/失败的行自动收起 (1.8.110, swipe 模块统一收尾): onDelete 没把
    行抽走 (isConnected 还在) 就地收起删除钮 —— 各消费方 confirm 里 return
    即可, 收尾不用各家自己记; 删成了的行早被抽走, 收尾是空操作。"""
    assert "if (wrap.isConnected) setSwipeTransform(wrap, 0);" \
        in _js("music-swipe-delete.js")
