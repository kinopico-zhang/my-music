"""My Music 资料库接线测试: 分享链接, 下载全部, 更新日志应用内化,
前端结构守恒 —— 静态文本断言, 不碰数据库。拆自 test_music_wiring.py
(结构化重构); 左滑删除 1.8.23 批拆去 test_music_swipe_delete.py。"""
import re
from pathlib import Path

from tests.music_static_files import (MUSIC_STATIC, music_browser_js,
                                      music_page_shell, page_script_paths,
                                      share_page_js, share_page_shell)


def test_music_share_link_wiring():
    """分享改链接制 (1.7.0, 用户点名"单独生成一个 uuid 的 url, 有效期 1 天,
    不用鉴权"): 开 24 小时免登录链接, 系统分享面板优先、复制回落;
    公开页 share.html 半自包含 —— 页面逻辑全在自己的 js/share/ 里, 只借
    应用的纯逻辑件 (无会话依赖): 1.8.130 (用户点名「样式和普通播放界面
    保持一致」) 起播放器样式与舞台直接复用应用那份, 不再 fork;
    播放器接线细节在 test_music_share_player_wiring。"""
    js = music_browser_js()
    share = share_page_shell()
    share_all = share + share_page_js()   # markup+css+脚本, 拆分前的整页口径
    for frag in ["async function shareByLink",
                 'fetchJSON("/music/api/shares"',
                 "async function sharePlaylist", 'id="playlist-share"',
                 "24 小时内有效"]:
        assert frag in js, f"music.js 分享缺 {frag}"
    # 1.8.25 分享图标换 iconfont「分享」搜索第 8 个 (用户点名): 三节点互连
    # 的共享网络画法 (id 809967, fill 填充)。图标定义在公共件里, 直接读
    # 文件 (browser_js 口径不含 music-common)
    common = (MUSIC_STATIC / "js" / "music-common.js").read_text(encoding="utf-8")
    assert "M769.714 589.547c-51.754 0-97.702 24.851-126.571 63.269" in common
    # 1.8.23 的 iOS 共享样式与更早的上传画法都退役
    assert "M12 9.5v-6M8.5 7 12 3.5 15.5 7" not in common
    assert "M12 3.5v11M" not in common
    # 曲目菜单那颗分享 (music.html 内联 18px) 换成同款, 不再各画各的
    html = music_page_shell()
    assert html.count("M769.714 589.547c-51.754 0-97.702 24.851-126.571 63.269") == 1
    assert "M12 3.5v11M" not in html
    # 公开页: 拿 uuid 换数据 → 流地址播放, 失效态/iOS 兜底都在
    for frag in ["/music/share/${token}/api",
                 "/music/share/${token}/stream/${track.track_id}",
                 "链接不存在或已过期", "playsinline",
                 "fmtDateTime", "togglePlay"]:
        assert frag in share_all, f"share.html 缺 {frag}"
    # 半自包含: 借的应用脚本只有这六枚纯逻辑件 (会话无关, 页面无副作用),
    # 其余全在自己的 js/share/ 里 —— 新借一枚要在这里挂上号
    allowed = {"lyrics-parser.js", "player-queue.js", "music-common.js",
               "music-player-art-stage.js", "music-player-quality.js",
               "music-player-slider.js"}
    for path in page_script_paths("share.html"):
        assert path.parent.name == "share" or path.name in allowed, \
            f"share 引了未批准的应用模块 {path.name}"
    # 整页不画滚动条 (与应用同款: 星规则 + 伪元素)
    assert "scrollbar-width: none;" in share
    assert "::-webkit-scrollbar { display: none; }" in share
    # 播放列表行歌名/艺人分两行 (1.8.18 用户点名): 行内 span 挤一行不吃省略号, block 化才各行其道
    assert ".row .t { display: block;" in share_all \
        and ".row .a { display: block;" in share_all
    assert "with-lyrics" not in share_all   # 常驻封面下面那套 (1.8.2) 撤了
    # 微信卡片: <head> 留 og 占位注释, 服务端换掉 (占位符漏替换卡片就漏空)
    assert "<!--og-->" in share
    share_routes = (Path(__file__).parent.parent / "app" / "music"
                    / "webapp" / "share_routes.py").read_text(encoding="utf-8")
    assert '_OG_MARK = "<!--og-->"' in share_routes
    assert '"/share/{token}/lyrics/{track_id}"' in share_routes
    # 分享页对整站是公开前缀 (中间件只认这个面, 过期由路由自己验);
    # 结构化重构后中间件拆去了 app/home/middleware.py
    middleware = (Path(__file__).parent.parent / "app" / "home"
                  / "middleware.py").read_text(encoding="utf-8")
    assert '_PUBLIC_PREFIXES = ("/music/share/",)' in middleware


def test_music_download_all_wiring():
    """「下载全部」(用户点名: 播放列表/专辑详情页): 顺序一首首下
    (几十个 40MB 并发请求在手机上必炸), 已在库/正在下的跳过,
    下载管理「全部删除」把整批叫停。列表页操作行 1.7.0 起改纯图标
    (播放/随机/下载/分享/删除 五枚一般大, 一行装下不再换行);
    专辑/艺人页 1.8.33 同款改齐 (用户点名「跟播放列表的风格差不多」)。"""
    html = music_page_shell()
    js = music_browser_js()
    assert 'id="album-download"' in js and "下载全部" in js
    assert 'id="playlist-download"' in js
    for frag in ["function downloadAllFromUI", "let downloadAllJob = null;",
                 "await downloads.downloadTrack(track)",   # 顺序 (await 在循环里)
                 "job.cancelled = true;"]:
        assert frag in js, f"music.js 缺 {frag}"
    # 操作行纯图标: 五枚 .action.icon 齐全 (有 title 无文字), 单行居中
    for frag in ['class="action icon primary" id="playlist-play"',
                 'id="playlist-shuffle"', 'id="playlist-download"',
                 'id="playlist-share"', 'id="playlist-delete"']:
        assert frag in js, f"操作行缺 {frag}"
    # 1.8.33 专辑/艺人页操作行同款纯图标 (用户点名「跟播放列表的风格
    # 差不多」): 专辑 播放/随机/下载/分享 + 艺人 播放/随机, 文字收进
    # title/aria-label
    for frag in ['class="action icon primary" id="album-play"',
                 'id="album-shuffle"', 'id="album-download"',
                 'id="album-share"', 'class="action icon primary" id="artist-play"',
                 'id="artist-shuffle"']:
        assert frag in js, f"专辑/艺人操作行缺 {frag}"
    # 专辑分享 (1.8.33 用户点名): shareAlbum 开 24h 免登录链接, 专辑页挂线
    assert 'async function shareAlbum' in js
    assert 'shareByLink("album", album.album_id' in js
    assert "shareAlbum(album);" in js
    assert ".action.icon {" in html and ".action.icon svg {" in html


def test_music_changelog_in_app_wiring():
    """更新日志改应用内视图 (用户点名"看日志别断歌"): 原来是整页跳转
    /music/changelog, 卸载 SPA 音频就停; 改应用内推入层铺开,
    播放气泡常驻。入口在设置页「更新」子页 (1.8.17 起设置拆四个
    左右滑的子页, 更新日志是其一)。
    独立日志页保留 (直达链接仍可用)。"""
    html = music_page_shell()
    js = music_browser_js()
    assert 'data-set-tab="changelog"' in js         # 设置页「更新」子页的入口
    assert 'href="/music/changelog"' not in html    # 不再整页跳走
    # 1.8.0: 更新日志是推入层之一 (PANE_VIEWS 名单里), 与主页/专辑同款滑入
    assert '"search", "settings", "stats", "changelog"];' in js
    assert "async function renderChangelogView(" in js
    assert 'fetchJSON("/music/changelog/api/entries")' in js
    assert 'id="changelog-entries"' in js and ".v-badge" in html  # 版本卡片样式
    assert 'renderChangelogView(page("changelog"));' in js   # 更新子页入口


def test_music_frontend_structure():
    """结构化重构 (2026-09-17 用户令): 前端源文件超限按逻辑拆分互相引用;
    html/css/js 分家 —— 页面不再内联 <style> 与脚本正文; js/css 引用一律
    带版本参数 (改动必 bump, 否则手机缓存不刷新)。
    行数上限 (2026-09-18 用户令): js/css 200 行, html 放宽到 500 ——
    markup 天生长 (一页一文件), 不像代码那样需要按域拆。"""
    for page in ("music.html", "share.html", "changelog.html"):
        html = (MUSIC_STATIC / page).read_text(encoding="utf-8")
        assert "<style" not in html, f"{page} 还有内联样式"
        inline = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>", html)
        assert not inline, f"{page} 还有无 src 的内联脚本: {inline}"
        for path, query in re.findall(
                r'(?:src|href)="(/music/static/(?:js|css)/[^"?]+)(\?[^"]*)?"',
                html):
            assert query, f"{page} 引用 {path} 没带版本参数"
    oversize = []
    for path in MUSIC_STATIC.rglob("*"):
        if path.suffix not in (".js", ".css", ".html") or not path.is_file():
            continue
        cap = 500 if path.suffix == ".html" else 200
        count = len(path.read_text(encoding="utf-8").splitlines())
        if count > cap:
            oversize.append(f"{path.relative_to(MUSIC_STATIC)} ({count} 行)")
    assert not oversize, f"超行数上限 (html 500 / js·css 200) 的前端文件: {oversize}"
