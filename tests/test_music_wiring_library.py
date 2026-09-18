"""My Music 资料库接线测试: 分享链接, 左滑删除, 下载全部,
更新日志应用内化, 前端结构守恒 —— 静态文本断言, 不碰数据库。
拆自 test_music_wiring.py (结构化重构, 代码逐字节未动)。"""
import re
from pathlib import Path

from tests.music_static_files import (MUSIC_STATIC, music_browser_js,
                                      music_page_shell, share_page_js,
                                      share_page_shell)


def test_music_share_link_wiring():
    """分享改链接制 (1.7.0, 用户点名"单独生成一个 uuid 的 url, 有效期 1 天,
    不用鉴权"): 开 24 小时免登录链接, 系统分享面板优先、复制回落;
    公开页 share.html 自包含 (不引应用 JS —— 访客没有会话)。"""
    js = music_browser_js()
    share = share_page_shell()
    share_all = share + share_page_js()   # markup+css+脚本, 拆分前的整页口径
    for frag in ["async function shareByLink",
                 'fetchJSON("/music/api/shares"',
                 "async function sharePlaylist", 'id="playlist-share"',
                 "24 小时内有效"]:
        assert frag in js, f"music.js 分享缺 {frag}"
    # 公开页: 拿 uuid 换数据 → 流地址播放, 失效态/滑进度/iOS 兜底都在
    for frag in ["/music/share/${token}/api",
                 "/music/share/${token}/stream/${track.track_id}",
                 "链接不存在或已过期", "playsinline",
                 "fmtDateTime", "playQueue", "togglePlay"]:
        assert frag in share_all, f"share.html 缺 {frag}"
    assert "js/music-" not in share    # 自包含, 不引应用模块 (只带自己的 share 脚本)
    # 整页不画滚动条 (与应用同款: 星规则 + 伪元素)
    assert "scrollbar-width: none;" in share
    assert "::-webkit-scrollbar { display: none; }" in share
    # 全屏播放页 1.8.5 与 app 一致 (用户点名): 大封面 + 标题/作者·专辑行;
    # 1.8.17 播放区改版 (用户点的布局): 传输区两行 —— 细进度条 (无旋钮,
    # 填充走 --fill) 一行, 上一首/播放/下一首三键站进度条上一行;
    # 标题行旁边的键改成歌词键 (歌词只走它, 封面点开不再切歌词), 歌词
    # 视图罩住封面区 (app 同款距离模糊/当前句放大), 歌词解析借公开的
    # lyrics-parser.js
    for frag in ['id="fp"', 'id="fp-play"', 'id="fp-prev"', 'id="fp-next"',
                 'id="fp-lyrics"', 'id="fp-meta-lyrics"', 'id="fp-scrub"',
                 'id="fp-grab"', 'id="fp-bg"', "openFullPlayer",
                 "closeFullPlayer", "bindPullClose", "updateMediaSession",
                 "/music/share/${token}/lyrics/${track.track_id}",
                 'src="/music/static/js/lyrics-parser.js',
                 ".lyrics-line.upnext", ".lyrics-line.active"]:
        assert frag in share_all, f"share.html 缺 {frag}"
    # 1.8.17 结构: 进度行 (.fp-scrub-row) 在上, 三键行 (.fp-keys) 在下
    assert '<div class="fp-transport">' in share_all
    assert share_all.index('<div class="fp-scrub-row">') < share_all.index('<div class="fp-keys">')
    assert "fp-controls" not in share_all      # 旧键行 (键在进度条旁) 撤了
    # 作者行并专辑名 (「下面是标题和作者专辑名称」)
    assert '[track.artist, track.album_title].filter(Boolean).join(" | ")' in share_all
    # 歌词视图开关 (1.8.17 只走标题行的歌词键): 开着封面让位, 键点亮;
    # 视图关着时没词键灰掉; 开着保持可点好关回封面
    assert "lyricsViewOpen" in share_all
    assert "function toggleLyricsView" in share_all
    assert '$("#fp-art-wrap").hidden = open;' in share_all
    assert 'lyricsButton.disabled = !lyrics && !lyricsViewOpen;' in share_all
    assert 'lyricsButton.classList.toggle("on", open);' in share_all
    # 切歌后视图跟上一首保持一致 (1.8.17 用户点名): 开合只听用户的态,
    # 不随有没有词翻面 —— 没词不强关, 空态垫着 (还在取词时空白, 不闪
    # 「没有歌词」的错话)
    assert "const open = lyricsViewOpen;" in share_all
    assert "lyricsSettled" in share_all
    assert '<div class="lyrics-empty">这首歌没有歌词</div>' in share_all
    # 封面左右滑切歌 (左滑下一首, 右滑上一首): 横向显著位移才认
    # (竖向下拉归收起, 互不抢)
    assert "bindCoverSwipe" in share_all
    assert "if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy) * 1.5) {" in share_all
    # 队列两头切歌键灰掉点不动 (1.8.17 用户点名)
    assert '$("#fp-prev").disabled = queuePos <= 0;' in share_all
    assert '$("#fp-next").disabled = queuePos >= queue.length - 1;' in share_all
    assert ".fp-keys > button:disabled { opacity: .3; pointer-events: none; }" in share_all
    # 播放列表行歌名/艺人分两行 (1.8.18 用户点名): 行内 span 挤一行不吃省略号, block 化才各行其道
    assert ".row .t { display: block;" in share_all \
        and ".row .a { display: block;" in share_all
    assert "with-lyrics" not in share_all   # 常驻封面下面那套 (1.8.2) 撤了
    # 下拉收起扩到整页: 传输区/歌词键照常点, 词滚到中间先归滚词
    assert 'const sheet = $("#fp .fp-sheet");' in share_all
    assert 'if (event.target.closest("button, input")) return;' in share_all
    assert 'if (scroller && scroller.scrollTop > 0) return;' in share_all
    # 细进度条填充: 播/拖都更新 --fill
    assert "function setScrubFill" in share_all
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


def test_music_swipe_delete_wiring():
    """左滑删除 (用户点名两处: 列表内曲目移出 + 主页列表整列删): iOS 同款
    红色删除钮。与长按菜单共存 (阈值分家), 滚动让位 (touch-action pan-y +
    捕获 scroll 即收), 尾随 click 吞掉, 同一时间只开一行。"""
    html = music_page_shell()
    js = music_browser_js()
    for frag in [".swipe-wrap {", ".swipe-del {", "touch-action: pan-y;"]:
        assert frag in html, f"左滑样式缺 {frag}"
    assert "#e5484d" in html                          # 删除钮红底
    for frag in ["const SWIPE_REVEAL = 72;",
                 "function closeSwipeRow", "function bindSwipeDelete",
                 'document.addEventListener("scroll", closeSwipeRow, true)',
                 'data-swipe-track=', 'data-swipe-playlist=',
                 "swipeSuppressClick",
                 '`/music/api/playlists/${playlistId}/tracks/${trackId}`']:
        assert frag in js, f"music.js 缺 {frag}"
    # 两处挂载: 列表详情的曲目行 + 主页的列表行
    assert 'bindSwipeDelete(target.querySelector("#playlist-tracks")' in js
    assert 'bindSwipeDelete($("#home-playlists")' in js
    # 手势地盘分家 (1.7.0 后遗症修): 左滑只认左移 (右移归推入层返回手势,
    # 抢了会被 pointercancel 掐弹回); 左缘 24px 让给 iOS 系统边缘返回
    assert "swipeDrag.horizontal = dx < 0 && Math.abs(dx) > Math.abs(dy);" in js
    # 左缘返回的归属 (用户点名两轮 preventDefault 拦截, iPhone Safari 实测
    # 都掐不住系统手势, 终版撤净): 苹果把屏幕最边一条握在系统手里, 网页
    # 收不到那片触摸 (Navigation API 的 traverse 取消也未实现) —— 应用
    # 自己的右滑从页面任意位置起手; 别再往 document 挂 touchstart 拦截,
    # 那只剩左缘一小条不能起手滚动的副作用
    assert "standaloneLaunch" not in js
    assert "EDGE_STRIP_PX" not in js
    assert 'document.addEventListener("touchstart"' not in js
    assert 'document.addEventListener("touchend"' not in js
    # 拖动跟手: 行上挂 .swiping 撤掉 transform 过渡, 松手回位才交给过渡
    # (不撤的话每帧都在重定 250ms 补间, 手指拖着行像皮筋 —— 队列拖拽同款)
    assert 'swipeDrag.row.classList.add("swiping")' in js
    assert ".swipe-wrap > button:first-child.swiping { transition: none; }" in html
    # 删除钮的点击走捕获层 (}, true); 行自己的冒泡 click 处理器看不到它
    assert 'container.addEventListener("click", async (event) => {' in js
    assert "}, true);" in js


def test_music_download_all_wiring():
    """「下载全部」(用户点名: 播放列表/专辑详情页): 顺序一首首下
    (几十个 40MB 并发请求在手机上必炸), 已在库/正在下的跳过,
    下载管理「全部删除」把整批叫停。列表页操作行 1.7.0 起改纯图标
    (播放/随机/下载/分享/删除 五枚一般大, 一行装下不再换行)。"""
    html = music_page_shell()
    js = music_browser_js()
    assert 'id="album-download"' in js and "下载全部" in js
    assert 'id="playlist-download"' in js
    for frag in ["function downloadAllFromUI", "let downloadAllCancelled = false;",
                 "await downloads.downloadTrack(track)",   # 顺序 (await 在循环里)
                 "downloadAllCancelled = true;"]:
        assert frag in js, f"music.js 缺 {frag}"
    # 操作行纯图标: 五枚 .action.icon 齐全 (有 title 无文字), 单行居中
    for frag in ['class="action icon primary" id="playlist-play"',
                 'id="playlist-shuffle"', 'id="playlist-download"',
                 'id="playlist-share"', 'id="playlist-delete"']:
        assert frag in js, f"操作行缺 {frag}"
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
