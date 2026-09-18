"""My Music 设置页接线测试 (1.8.17 改版): 四个左右滑的子页 + 蜂窝流量
撤净的回归守卫 —— 静态文本断言, 不碰数据库。拆自 test_music_page_wiring.py
(文件超 200 行按域再拆)。"""

from tests.music_static_files import MUSIC_STATIC, music_browser_js, music_page_shell


def test_music_settings_view_wiring():
    """设置页接线 (1.8.17 改版, 用户点名): 拆成四个左右滑的子页 —— 通用 /
    歌词 / 统计 / 更新 (搜索页同款手感), 统计/更新复用各自视图函数嵌进
    子页; 表单 (曲库路径/歌词开关/API 地址) 只有管理员能改; 蜂窝流量月账
    整个撤了 (前端采集与后端接口一起拆)。"""
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
    assert 'const lock = editable ? "" : " disabled"' in js    # 只读锁
    assert "仅管理员可修改" in js                              # 非管理员的落地面


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
