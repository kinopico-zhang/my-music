"""My Music 页面静态接线测试: 统计页/下载面/长按菜单/
设置页的静态文件断言 (主页的拆去 test_music_home_sections.py)。"""
import re


from tests.music_static_files import MUSIC_STATIC, music_browser_js, music_page_shell


def test_music_stats_page_wiring():
    """统计页接线: 推入层路由 + 渲染函数 (E2E 再验真数据); 1.8.17 起也嵌进
    设置页的「统计」子页 (查找收在 target 里 —— 同场叠着的独立统计层
    #stats-body 撞名, 全局 $() 会写错层)。"""
    html = music_page_shell()
    assert "stat-grid" in html and "format-bar" in html   # 统计卡片 + 比例条
    js = music_browser_js()
    assert '"search", "settings", "stats", "changelog"];' in js
    assert "async function renderStatsView(" in js
    assert '"/music/api/stats"' in js
    assert 'data-set-tab="stats"' in js                   # 设置页四滑页之一
    assert 'renderStatsView(page("stats"));' in js        # 嵌进设置子页
    assert 'const body = target.querySelector("#stats-body");' in js  # 收层内


def test_music_downloads_wiring():
    """下载接线: 纯逻辑模块 (node 直测) + SW 拦流 + 已下载独立页 + 能力门控 + 下载管理。"""
    js = music_browser_js()
    assert "downloadsSupported" in js and "createDownloads" in js
    assert '"/music/sw.js"' in js                  # SW 注册
    assert "isSecureContext" in js                 # 明文 HTTP 整个功能收起
    assert "function renderDownloadsPane(" in js   # 已下载独立页 (1.8.0)
    assert "$(\"#dl-pane-body\")" in js            # 页容器独占 id, 进度刷新认得准
    assert "data-download-track" in js             # 曲目行下载标
    assert "storageUsage" in js and "formatBytes" in js    # 下载管理: 量大小并显示
    # 1.8.17 改版 (用户点名): 行尾删除键换成左滑出删除 (与列表内曲目同一颗
    # bindSwipeDelete), 「全部删除」撤掉只留右上角多选 —— 删除只动下载缓存,
    # 曲库只读, 碰不到库里一个字节
    assert "dl-clear-all" not in js and "removeAll" not in js
    assert "bindSwipeDelete(target, async (wrap) => {" in js   # 左滑删除挂下载行
    assert "await downloads.removeDownload(trackId);" in js    # 左滑/多选同一条删径
    assert "navigator.storage.estimate" in js      # 手机存储占用
    # 1.8.50 (用户点名「全部下载按钮变成取消按钮」): 批量在跑 → 操作行和
    # 收缩顶栏的「下载全部」键都换成 ✕/「取消下载」, 点了整批叫停 (连
    # 在下的那首一起掐断); 已下载页删掉在下那首也整批叫停; 单曲下载标
    # 照旧进度环, 不掺和取消 (1.8.50 头版做错的单曲取消已全数回退)
    assert "let downloadAllJob = null;" in js
    assert "async function cancelDownloadAll" in js
    assert "function syncDownloadAllButtons" in js
    assert "if (downloadAllJob) { await cancelDownloadAll(); return; }" in js
    assert '[data-bar-act="download"], [data-dl-all]' in js
    assert "downloadRingHTML(state.progress, 17)" in js
    assert 'id="album-download" data-dl-all' in js
    assert 'id="playlist-download" data-dl-all' in js
    assert "if (busy) cancelDownloadAll();" in js
    # 1.8.2: 下载中的进度从百分比文字换成圆环 (r=8.5 周长切 dashoffset,
    # 正上方顺时针画满; 已下载照旧是勾)
    assert "function downloadRingHTML" in js
    assert "stroke-dasharray" in js and "stroke-dashoffset" in js
    # 1.8.5 修「下载中已下载页封面闪烁」: 进度回调不再整页重铺 —— 行级
    # 就地补 (同一行只换圆环, 状态翻转才换行), 全清了才补统计行
    assert "function refreshDownloadsBody" in js
    assert "function downloadRowHTML" in js
    assert 'body.querySelectorAll("[data-dl-wrap]")' in js   # 行集合对照在 wrap 一级
    assert "ring.outerHTML = downloadRingHTML" in js
    # 已下载行也带封面: 曲目封面接口 + 裂图退音符 (和播放列表行同款)
    assert 'src="/music/media/tracks/${entry.track_id}/artwork"' in js
    downloads_js = (MUSIC_STATIC / "js" / "downloads.js").read_text(encoding="utf-8")
    assert "/music/media/stream/" in downloads_js  # 缓存键 = 音频流地址
    assert "AbortController" in downloads_js       # 下载中的删除 = 取消下载
    html = music_page_shell()
    assert ".dl-stats" in html and ".dl-clear" in html    # 统计行样式
    scripts = re.findall(r'<script src="([^"]+)"', html)
    # 结构化重构后独立脚本 (1.8.1: +recent-pane; 1.8.3: +search-pages;
    # 1.8.5: +bubble-swipe; 1.8.6: +downloads-select; 1.8.14:
    # -viewport-heal; 1.8.17: -cellular-usage, +playlist-drag;
    # 1.8.23: +root-rubber; 1.8.31: +top-pane 播放排行页; 1.8.34:
    # +hero-collapse; 1.8.35: +client; 1.8.39: +desktop-keys; 1.8.45:
    # +hero-bar-actions 收缩顶栏动作条; 1.8.46: +hero-bar-tap 被吞点按
    # 补发; 1.8.47: +share-links; 1.8.57: +settings-account; 1.8.59:
    # +player-prefetch 预取拆分; 1.8.60: +player-art-stage 3D 封面舞台;
    # 1.8.76: +player-sources 源解析/失败兜底拆分, +player-slider 滑杆
    # 拆分, +downloads-pane 已下载面板拆分; 1.8.77: +autocache 自动缓存
    # 状态机, +autocache-integration 接线; 1.8.100: +handoff 后台连播
    # 提前接力裁决; 1.8.103: +dock-volume 船坞音量气泡 (键鼠端专属),
    # 引用一律带版本参数 (改哪个 bump 哪个)
    assert len(scripts) == 66 and all("?v=" in src for src in scripts)
    assert "js/downloads.js?v=" in html and "js/music-app-boot.js?v=" in html
    assert "js/autocache.js?v=" in html                  # 1.8.77 自动缓存状态机
    assert "js/music-autocache-integration.js?v=" in html  # 1.8.77 自动缓存接线
    assert "js/music-player-sources.js?v=" in html       # 1.8.76 源解析/失败兜底
    assert "js/music-player-slider.js?v=" in html        # 1.8.76 滑杆命中区拆分
    assert "js/music-downloads-pane.js?v=" in html       # 1.8.76 已下载面板拆分
    assert "js/music-player-prefetch.js?v=" in html   # 1.8.59 下一曲预取拆分
    assert "js/music-player-art-stage.js?v=" in html  # 1.8.60 3D 封面舞台
    assert "js/music-downloads-select.js?v=" in html   # 1.8.6 已下载多选删除
    assert "js/music-root-rubber.js?v=" in html        # 1.8.23 根层橡皮筋
    assert "js/music-hero-collapse.js?v=" in html      # 1.8.34 封面收缩顶栏
    assert "js/music-hero-bar-actions.js?v=" in html   # 1.8.45 顶栏动作条
    assert "js/music-hero-bar-tap.js?v=" in html       # 1.8.46 被吞点按补发
    assert "js/music-share-links.js?v=" in html       # 1.8.47 分享链接拆分
    assert "js/music-client.js?v=" in html             # 1.8.35 客户端识别
    assert "js/music-desktop-keys.js?v=" in html \
        and "js/music-dock-volume.js?v=" in html   # 1.8.39 键盘层; 1.8.103 音量气泡
    assert "js/music-settings-account.js?v=" in html   # 1.8.57 账号自助块
    assert "css/music-hero-bar.css?v=" in html \
        and "css/music-large.css?v=" in html  # 1.8.45 动作条; 1.8.103 大屏布局轴
    sw = (MUSIC_STATIC / "sw.js").read_text(encoding="utf-8")
    assert "TRACK_URL_PATTERN" in sw               # 曲目流: 缓存回源 + Range 切片
    assert "caches.open" in sw and "206" in sw
    assert "music-shell-v93" in sw                  # 应用壳也进缓存 (断网打得开)
    assert 'url.searchParams.has("direct")' in sw   # 1.8.59 流媒体直连放行
    assert "clients.claim" in sw                   # 装完立刻接管已开的页面


def test_music_track_context_menu_wiring():
    """长按菜单接线: 检测 (500ms/右键/移动作废)、菜单四项、选择单、
    分享回落都在页面上; 行样式禁掉 iOS 长按气泡。"""
    html = music_page_shell()
    js = music_browser_js()
    for frag in ['id="track-menu"', 'id="track-menu-mask"',
                 'data-track-action="play"', 'data-track-action="artist"',
                 'data-track-action="playlist"', 'data-track-action="share"',
                 'data-track-action="download" id="track-menu-download"',
                 'id="track-menu-artist"', 'id="picker-sheet"',
                 'id="picker-list"', 'id="picker-create"', 'id="picker-name"',
                 'id="picker-mask"',
                 "-webkit-touch-callout: none"]:
        assert frag in html, f"播放页缺少 {frag}"
    # 1.8.6: 播放页 ⋯ 菜单加「下载」—— 已下过的/下载不可用时藏掉,
    # 派发走 downloadTrackFromUI (与曲目行长按菜单同一颗)
    assert 'hideDownloadMenuItem(track)' in js
    assert '$("#track-menu-download").hidden' in js
    assert 'downloadTrackFromUI(track);' in js
    # 1.8.50 头版的菜单图标/文字换装已回退: 菜单项回归单图标「下载」
    assert 'id="track-menu-dl-cancel-icon"' not in html
    assert "track-menu-dl-label" not in html and "track-menu-dl-label" not in js
    assert "downloadMarkAria" not in js          # 单曲取消那套撤干净了
    for frag in ["function openTrackMenu", "function cancelTrackPress",
                 "function trackFromRow", "function shareTrack",
                 "function openPlaylistPicker", "trackListBindings",
                 "trackPressTimer = setTimeout",            # 500ms 长按计时
                 'document.addEventListener("contextmenu"',
                 "navigator.share", "execCommand",          # 分享 + 复制回落
                 # 1.8.47 拆出的分享链接域 (music-share-links.js): 封面抓成
                 # 本地文件递给系统分享面板 —— 面板只认 files 里的图
                 "function shareCoverFile",
                 "navigator.canShare({ files: [file] })",
                 "await navigator.share(cover ? { files: [cover], title, text, url }",
                 "suppressTrailingTarget",                 # 长按尾随点击按元素吞
                 # 1.8.2: 艺人/专辑两项并一路跳转 —— 先收全屏播放页
                 # (z90 盖着 z44 的推入层, 不收 = 看着没反应), 再按项分目标
                 # (1.8.63 收法 = 水滴收回, 层滑入与收拢同场)
                 'if (playerOpen) closeFullPlayer("morph");',
                 '? `artist/${track.artist_id}` : `album/${track.album_id}`);',
                 'fetchJSON("/music/api/playlists"',
                 '`/music/api/playlists/${playlistId}/tracks`',
                 "error.status === 409",            # 已在列表里: 直说原因不算失败
                 '`/music/api/playlists/${playlistId}`, { method: "DELETE" }',
                 'id="playlist-delete"',           # 列表删除在详情页 (选择单只加歌)
        ]:
        assert frag in js, f"music.js 缺少 {frag}"
    # 新版图标/脚本地址随行; Plex 同步全撤了
    assert "js/music-app-boot.js?v=" in html   # 浏览页模块链以 boot 收尾
    # 长歌名不许把菜单撑超宽 (用户报"菜单非常宽, 建议截断"): 固定定位菜单
    # 收缩到内容, 不封顶会一路撑到视口; 320px 封顶后 nowrap 截断才接管
    assert "max-width: min(320px, calc(100vw - 24px))" in html
    # fetchJSON 把 HTTP 状态码挂上错误对象 (加歌 409 分叉靠它)
    common = (MUSIC_STATIC / "js" / "music-common.js").read_text(encoding="utf-8")
    assert "status: response.status" in common
    assert "picker-sync" not in html and "picker-sync" not in js
    assert "picker-del" not in html and "picker-del" not in js
    assert "sync-playlists" not in html and "/playlists/sync" not in js
    # 1.8.17: 选择单顶部的「添加到播放列表 完成」栏撤掉 (关闭只剩点遮罩);
    # 列表按最后编辑时间排, 最近动过的在最前 (用户点名)
    assert 'id="picker-close"' not in html
    picker_js = (MUSIC_STATIC / "js" / "music-playlist-picker.js").read_text(
        encoding="utf-8")
    assert 'id="picker-close"' not in picker_js
    assert "playlists.sort((a, b) => b.updated_at - a.updated_at);" in picker_js
    # 1.8.18: 顶栏换成正在加的那首歌 —— 封面 + 歌名 + 艺人·专辑 (专辑名
    # 1.8.20 补上, 用户点名), 「选一个列表…」提示撤了
    assert 'id="picker-track-art"' in html and 'id="picker-track-artist"' in html
    assert "$(\"#picker-track-art\").innerHTML = trackArtHTML(track);" in picker_js
    assert "textContent = [track.artist, track.album_title]" in picker_js
    assert "选一个列表" not in html and "选一个列表" not in picker_js
    # 1.8.19: 行间分割线撤了 (用户点名) —— 规则收尾在 text-align, 没挂 border-bottom
    assert "padding: 11px 6px; text-align: left;\n}" in html


def test_album_artwork_url_versioning():
    """专辑封面 URL 的 ?v= 跟文件内容走 (1.8.82, EVA 四张换完文件手机
    一直占位块的根): artwork_version 优先, added_at 只作旧数据兜底 ——
    手机端长缓存/SW 封面档都按 URL 存, 版本号不变旧图永远换不掉。"""
    common = (MUSIC_STATIC / "js" / "music-common.js").read_text(encoding="utf-8")
    assert "album.artwork_version || album.added_at" in common
    assert "v=${version}" in common
