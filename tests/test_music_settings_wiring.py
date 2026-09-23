"""My Music 设置页接线测试 (1.8.17 改版): 四个左右滑的子页 + 蜂窝流量
撤净的回归守卫 + 1.8.57 账号自助块 —— 静态文本断言, 不碰数据库。拆自
test_music_page_wiring.py (文件超 200 行按域再拆)。"""

from tests.music_static_files import MUSIC_STATIC, music_browser_js, music_page_shell


def test_music_settings_view_wiring():
    """设置页接线 (1.8.17 改版, 用户点名): 拆成四个左右滑的子页 —— 通用 /
    歌词 / 统计 / 更新 (搜索页同款手感), 统计/更新复用各自视图函数嵌进
    子页; 1.8.57 (用户点名): 普通账号连歌词页签一起收走, 表单只在管理员
    位渲染, 只读锁与「仅管理员」提示随之撤了。"""
    html = music_page_shell()
    js = music_browser_js()
    assert 'data-pop-nav="settings"' in html             # 菜单直通设置页
    assert "music-settings.css?v=" in html               # 子页样式独立成件
    assert ".settings-block" in html and ".switch" in html
    assert ".month-row" not in html and "month-row" not in js   # 月账撤净
    assert '"search", "settings", "stats", "changelog"];' in js
    assert "async function renderSettingsView(" in js
    assert 'data-set-tab="general"' in js and 'data-set-tab="lyrics"' in js \
        and 'data-set-tab="stats"' in js \
        and 'data-set-tab="changelog"' in js             # 四滑页的页签
    assert 'data-set-page="general"' in js and 'data-set-page="lyrics"' in js
    assert "function bindSetTabs" in js                  # 页签 ↔ 滑动互切
    assert 'renderStatsView(page("stats"));' in js       # 统计/更新嵌为子页
    assert 'renderChangelogView(page("changelog"));' in js
    assert 'fetchJSON("/music/api/settings")' in js
    assert 'fetchJSON("/api/me")' in js and "editable" in js   # 按管理员分叉
    assert "music_directory" in js and "lyrics_api_enabled" in js \
        and "lyrics_api_base" in js
    assert "cellular" not in js and "cellular" not in html      # 蜂窝撤净
    # 1.8.57 普通账号 (用户点名「不需要看音乐库的设置」): 歌词页签和页整个
    # 移除 (页签/页同摘一套, 滑页下标才对得齐), 音乐库块不再渲染进通用页
    assert "target.querySelector('[data-set-tab=\"lyrics\"]').remove();" in js
    assert 'page("lyrics").remove();' in js
    assert 'page("general").innerHTML = editable ? `' in js
    view_js = (MUSIC_STATIC / "js" / "music-settings-view.js").read_text(
        encoding="utf-8")
    assert "const lock" not in view_js and "仅管理员可修改" not in view_js
    # 1.8.57 歌词厂商 (用户点名「多提供几个厂商」): 四枚药丸键, 空键 =
    # 自动依次试; LRCLIB 兼容地址行只在 LRCLIB 选中时亮出来
    assert '[["", "自动"], ["lrclib", "LRCLIB"],' in js
    assert '["netease", "网易云"], ["qq", "QQ 音乐"]];' in js
    assert 'data-prov="${key}"' in js
    assert "lyrics_api_provider" in js
    assert 'chip.dataset.prov !== "lrclib"' in js


def test_music_settings_account_wiring():
    """1.8.57 账号块 (用户点名「账号可以改名字和密码」): 自助改名/改密走
    账号自助接口 (旧密码验身; uuid 不动会话不掉线), 两枚行内编辑器互斥,
    退出登录整段从视图模块搬来; 模块先于视图加载 (视图渲染时调它)。"""
    html = music_page_shell()
    js = music_browser_js()
    account_js = (MUSIC_STATIC / "js" / "music-settings-account.js").read_text(
        encoding="utf-8")
    assert html.index("music-settings-account.js") \
        < html.index("music-settings-view.js")
    assert "function renderSettingsAccount" in account_js
    assert 'renderSettingsAccount(page("general"), me);' in js  # 插通用页最前
    for frag in ['"/api/account/name"', '"/api/account/password"',
                 "old_password: fields[0].value",
                 "new_password: fields[1].value",
                 'id="set-rename"', 'id="set-rename-box"',
                 'id="set-pass"', 'id="set-pass-box"',
                 "两次输入的新密码不一样",      # 新密码两遍不一致: 前端先拦
                 'id="set-user-name"',          # 改完当场换行上的名字
                 "boxes[1].hidden = true;",
                 'caches.delete("music-data-v1")']:
        assert frag in account_js, f"账号块缺 {frag}"
    # 退出登录整段搬来了账号块, 视图模块里不再有
    view_js = (MUSIC_STATIC / "js" / "music-settings-view.js").read_text(
        encoding="utf-8")
    assert 'id="set-logout"' not in view_js
    assert 'id="set-logout"' in account_js


def test_music_cellular_wiring():
    """蜂窝流量采集 1.8.17 整个撤了 (用户点名「设置里蜂窝网络数据相关内容
    去掉」): 前端模块/上报代码/后端接口全拆了 —— 回归守卫, 别再爬回来。"""
    html = music_page_shell()
    js = music_browser_js()
    assert "cellular-usage.js" not in html               # 模块不再加载
    assert not (MUSIC_STATIC / "js" / "cellular-usage.js").exists()
    assert "createCellularMonitor" not in js
    assert '"/music/api/cellular-usage"' not in js
    assert "connection.type" not in js    # 网型探针没了 (体检窗的 keepalive
    # 回传是另一回事, 不算蜂窝流量的残留)
