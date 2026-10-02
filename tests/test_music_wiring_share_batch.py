"""My Music 分享页 1.8.6 批接线测试: 点句定位 + 禁双击/两指缩放 +
红键自动掀全屏页 + 全屏页封面; 1.8.41 列表行序号换歌曲封面 ——
静态文本断言, 不碰数据库。"""

from tests.music_static_files import share_page_js, share_page_shell


def test_music_186_share_batch():
    """1.8.6 分享页批 (用户点名): 歌词点一句跳到那句的进度 (app 同款
    data-time); 页面双击/两指捏不再放大 (viewport 收口 + body pan-y 双
    保险); 点大红播放键顺势掀开整页播放页; 整页播放页看不到封面修好
    (此前 setArt 错用在 <img> 上 —— 往 img 里塞子 img 永不渲染)。"""
    share = share_page_shell()               # markup + css
    share_all = share + share_page_js()      # 再拼脚本, 拆分前整页口径
    # 禁缩放: viewport meta 双保险 + 页面级 touch-action (app 同款收口)
    assert 'content="width=device-width, initial-scale=1, maximum-scale=1,' \
           ' user-scalable=no, viewport-fit=cover"' in share
    assert "touch-action: pan-y;" in share
    # 滑杆是手势区, 自带 touch-action 不被 body 的 pan-y 抢走
    assert 'input[type="range"] { touch-action: none; }' in share
    # 点句定位: 行带 data-time (解析器的时间轴, 纯文本词恒 -1), 点击跳
    # 进度并退出"暂停跟唱", 紧跟的 timeupdate 把新当前句滚回中央
    assert 'data-time="${line.timeSeconds}"' in share_all
    assert 'const line = event.target.closest(".lyrics-line");' in share_all
    assert "if (time >= 0) audio.currentTime = time;" in share_all
    assert "lyricsFollowPaused = false;" in share_all
    # 红键一按掀全屏页 (迷你条的播键不掀)
    assert '$("#hero-play").addEventListener("click", () => {' in share_all
    assert "togglePlay();\n  openFullPlayer();" in share_all
    # 封面修复: #fp-art 本尊是 <img>, 直接挂 src (app 同款), 不再走
    # 给容器 div 用的 setArt; 1.8.130 起裂图退应用的占位图, 邻卡归舞台
    assert 'const art = $("#fp-art");' in share_all
    assert "art.src = artURL(track);" in share_all
    # 1.8.19 切歌封面方向滑入 → 1.8.130 退役 (用户点名「3d切换封面」):
    # 切歌动画整块归 3D 舞台 (起跳位/交班溶解在 music-player-art-stage),
    # 平面 keyframes 那套撤净
    assert "art-in-next" not in share_all
    assert "art-in-prev" not in share_all
    assert "@keyframes fp-art-next" not in share
    assert "@keyframes fp-art-prev" not in share
    # 1.8.20 改回原样 (用户点名「歌词页不要封面缩略图」, app 同款): 歌词
    # 页罩满封面区, 封面整块藏掉 (缩略图那套 #fp.lyrics CSS 撤净)
    assert '$("#fp-art-wrap").hidden = open;' in share_all
    assert "#fp.lyrics .fp-body {" not in share


def test_music_1841_share_track_covers():
    """1.8.41 (用户点名「分享页面, 播放列表, 不需要显示序号, 改成显示歌曲
    封面吧」): 列表行去序号, 行首换 44px 歌曲封面 (app 歌单同款, 裂图退
    ♪ 占位); 正播的行封面留着, 跳条蒙在封面上 (半透黑纱 + 白条, app 播放
    队列 1.8.38 同款) —— 不再抹掉行首回填序号。"""
    share = share_page_shell()
    share_all = share + share_page_js()
    # 行首: 封面图 (曲目自己的 → 专辑的, artURL 兜底), 序号标记整个撤了
    assert '<span class="lead"><img alt="" loading="lazy" decoding="async"' in share_all
    assert "artURL(t)}\"" in share_all
    assert "classList.add('ph')" in share_all
    assert 'class="num"' not in share_all
    assert 'Array.prototype.indexOf.call(row.parentNode.children, row);' not in share_all
    # 44px 封面格: 圆角裁切 + 相对定位 (跳条的蒙纱挂在里面), 裂图占位 ♪
    assert ".row .lead { width: 44px; height: 44px; flex-shrink: 0;" in share
    assert ".row .lead img { width: 100%; height: 100%; object-fit: cover;" in share
    assert '.row .lead.ph::after { content: "♪"; }' in share
    # 播放行: 跳条蒙在封面上 (插入, 不抹内容), 换歌时摘掉 —— 封面永在
    assert "lead.insertAdjacentHTML(\"beforeend\", BARS_SVG);" in share_all
    assert "if (!on && bars) bars.remove();" in share_all
    assert ".row.on .bars { position: absolute; inset: 0;" in share
    assert "background: rgba(0,0,0,.45);" in share
