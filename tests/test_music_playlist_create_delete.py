"""My Music 播放列表建/删两颗用户实报钉子: 1.8.79 建列表防连点 (服务日志
实锤: 一次 200 + 四次 409 + 两次 503, 建成的被连环失败盖成「没建起来」)
+ 1.8.80 删列表后回主页陈货 (底下的层收层回去不重铺)。
拆自 test_music_playlist_rename_reorder.py (文件超 200 行按域再拆)。"""

from tests.music_static_files import MUSIC_STATIC


def test_playlist_create_inflight_guard():
    """1.8.79 修「新建播放列表失败」(用户实报): 建列表请求一来一回不短
    (NAS + 外网中转), 按钮没在途闸, 手快点出连环 POST —— 第一击其实建成了,
    后几击撞名 409 (服务器内存盘满时还 503), 一串「没建起来」把成功的也盖
    成失败 (服务日志实锤: 一次 200 + 四次 409 + 两次 503, 列表 19 早就建好
    且歌已加进去)。接线: 在途不重复发; 撞名 (409) 直说「已经有了」,
    不再说"没建起来"。"""
    picker_js = (MUSIC_STATIC / "js" / "music-playlist-picker.js"
                 ).read_text(encoding="utf-8")
    assert "let creatingPlaylist = false;" in picker_js
    assert "if (!pickerTrack || creatingPlaylist) return;" in picker_js
    assert "creatingPlaylist = true;" in picker_js
    assert "creatingPlaylist = false;" in picker_js     # finally 里放行
    assert 'if (error.status === 409) toast("已经有叫这个名字的列表了, 点它加歌");' \
        in picker_js
    assert "没建起来" in picker_js            # 其余错误照旧直报原因


def test_playlist_delete_unstales_home():
    """1.8.80 修「删播放列表后回主页, 被删的还在」(用户实报): 主页层底下
    一直躺着, 收层回去只解锁滚动不重铺 —— 删掉的不抽走就等下次整页重铺
    才消失。两条删路都修: 列表页左滑删 → removeHomePlaylistCard 就地抽
    主页那张卡; 详情页删 → 原来先 navigate("home") 再补 renderRootView,
    但 navigate 已把层栈收干净, if (pushStack.length) 永不成立 = 死闸,
    换成趁层还盖着先铺再收层。"""
    home_js = (MUSIC_STATIC / "js" / "music-home-view.js").read_text(
        encoding="utf-8")
    pane_js = (MUSIC_STATIC / "js" / "music-playlists-pane.js").read_text(
        encoding="utf-8")
    view_js = (MUSIC_STATIC / "js" / "music-playlist-view.js").read_text(
        encoding="utf-8")
    # 就地抽卡: 主页段里按 id 抽, 抽空了换空态占位 (grid 不留白)
    assert "function removeHomePlaylistCard" in home_js
    assert 'element.querySelector(`[data-playlist-id="${playlistId}"]`)' \
        in home_js
    assert 'if (!element.querySelector("[data-playlist-id]"))' in home_js
    # 列表页左滑删: 抽完本层行, 主页那张卡一起抽
    assert "removeHomePlaylistCard(playlistId);" in pane_js
    # 详情页删: 趁层还盖着先整页重铺再收层 (次序不能反 —— navigate 收完
    # 层栈, 死闸那个写法永远不铺)
    assert 'renderRootView("home");\n      navigate("home");' in view_js
    assert 'navigate("home");\n      if (pushStack.length)' not in view_js
