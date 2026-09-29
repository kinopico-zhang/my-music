"""My Music 封面收缩顶栏测试 (1.8.34, 用户点名; 1.8.45 改单行顶栏): 专辑/
播放列表/艺人详情页的页头 sticky 钉在层顶, 上划列表时封面一边缩小一边挪向
左上角, 标题文字跟着缩进 (封面右边) —— 收齐后钉成实底单行顶栏, 顶栏里
播放 + … 两颗键从操作行的键位沿路径平移进来接班 (1.8.46, 见
test_music_hero_bar), 列表继续上滑从顶栏底下滚过, 下划对称还原。
静态文本断言, 不碰数据库 (插值是纯几何, 手感真机眼验)。"""
from tests.music_static_files import music_browser_js, music_page_shell


def test_music_1834_hero_collapse_wiring():
    """三个详情页的页头都包进 .hero-head, 各自渲染尾挂 bindHeroCollapse
    (重铺换元素, WeakMap 记控制器, 监听只绑一次); 挂线模块排在视图模块
    之前加载。三个页头的文字统一包 .hero-txt (主标题 + 副标题行
    .hero-sub —— 艺人/年份/时长并一行, 收缩时跟封面一起进顶栏)。"""
    html = music_page_shell()
    js = music_browser_js()
    assert js.count('<div class="hero-head">') == 3   # 专辑 + 艺人 + 播放列表
    assert js.count("bindHeroCollapse(target);") == 3
    assert js.count('<div class="hero-txt">') == 3
    assert js.count('<div class="hero-sub">') == 3
    assert js.count('class="hero-meta"') == 3
    assert html.index("music-hero-collapse.js") < html.index("music-album-artist-views.js")
    for frag in ["function bindHeroCollapse(scroller)",
                 "const heroCtrls = new WeakMap();",
                 "requestAnimationFrame(() => {",      # 滚动事件按帧节流
                 "{ passive: true }"]:
        assert frag in js, f"hero-collapse 缺 {frag}"


def test_music_1834_hero_collapse_geometry():
    """细腻的根: 页头布局高度恒定, 收缩只写 transform/opacity (零重排),
    滚动位置线性直驱 (手指拖到哪跟到哪, 动量滚动天然续上); 收缩行程 =
    页头自然高 − 顶栏高, 页头太矮收不动就不挂 (行为照旧)。
    1.8.42 左对齐: 主标题/副标题各自搬、左缘都贴封面右边 —— 整块搬的话
    窄的那行在块里居着中, 收进顶栏就飘 (用户点名)。
    1.8.45 单行顶栏: 顶栏高 52 (封面 44 + 下沿 8, 按钮上到封面那行),
    操作行不再竖移成第二行 —— 1.8.46 起行键一进收缩就藏, 顶栏那套从
    行键位沿路径平移进来 (见 test_music_hero_bar)。
    1.8.55 换行标题只收第一行 (用户点名): 落位按第一行的行盒量, 第二行
    起随行程用 clip-path 裁掉; 1.8.56 二连 (用户点名「大小没必要缩小,
    按一行的样式来渲染」): 换行标题退出缩宽约束, 收拢态按原字号, 溢出
    条簇的一截右刀裁掉 (渐隐纱 .bar-sheen 正好罩住裁口)。
    1.8.112 两改 (用户点名): ① 收缩途中两行先并齐 —— 副标题左缘跟主标题
    走, 居中错位按 (1-p)^3 早收 ② 宽度彻底退出缩放 —— 长标题不再为塞
    进条簇缩字号 (只有两行摞超高才轻微收), 溢出右刀改单行也吃、后段
    (0.55 起) 与渐隐纱同一条坡进场, 终点切在条簇左缘。
    1.8.113 并齐收紧 (用户二报「感觉前面有空格」): (1-p)^3 铺满全程, 半
    程还错着几个 px —— 改成宽的那行 (居中起得靠左) 当锚走线性原路, 窄
    的那行头 22% 行程追平 (追向与自家飞向同向, 不逆行), 之后两行贴成一
    整块飞; 两处重复的摘样式循环顺手抽成 heroReset 共用。"""
    js = music_browser_js()
    assert "const HERO_MINI = 44;" in js and "const HERO_BAR = 52;" in js
    assert "dist: head.offsetHeight - padTop - HERO_BAR," in js
    assert "return ctrl.dist > 24 ? ctrl : null;" in js
    assert "Math.min(1, Math.max(0, scroller.scrollTop / ctrl.dist))" in js
    assert "if (p === ctrl.p) return;" in js           # 同值不重写
    # 两行的目标位 (1.8.42 左对齐, 用户点名): 左缘同贴封面右边 (textX),
    # 整摞在上行 44 里垂直居中; 副标题顶 = 摞顶 + 原缝缩放; 共用一尺 —
    # 高按整摞 (标题+副标题+中缝), 宽度 1.8.112 起彻底退出缩放 (见下)
    assert "const textX = contentLeft + HERO_MINI + 12;" in js
    assert "const titleTx = textX - (titleRect.left - headRect.left);" in js
    assert "const subTx = subRect ? textX - (subRect.left - headRect.left) : titleTx;" in js
    assert "const stackY = padTop + (HERO_MINI - stackH * textScale) / 2;" in js
    assert "titleTy: stackY - (titleRect.top - headRect.top)," in js
    assert "anchorTx, titleCorr, subCorr," in js
    assert "const textScale = Math.min(1, HERO_MINI / Math.max(1, stackH));" in js
    assert 'for (const el of movers) el.style.transformOrigin = "0 0";' in js
    # 1.8.113 并齐收紧 (用户二报「感觉前面有空格」): 宽的那行 (居中起得靠
    # 左) 当锚走线性原路, 窄的那行头 22% 行程追平 —— 追向与自家飞向同向
    # (不逆行), 之后两行贴成一整块飞; 1.8.112 的 (1-p)^3 铺满全程, 半程
    # 还错着几个 px。锚/横修在 heroCollect 一次算好, 每帧只做乘加
    assert "const anchorTx = !subRect || subRect.left < titleRect.left ? subTx : titleTx;" in js
    assert ("const titleCorr = subRect && subRect.left < titleRect.left"
            " ? subRect.left - titleRect.left : 0;") in js
    assert ("const subCorr = subRect && subRect.left >= titleRect.left"
            " ? titleRect.left - subRect.left : 0;") in js
    assert "const catchUp = 1 - Math.max(0, 1 - p / 0.22) ** 3;" in js
    assert ("textMove(ctrl.title, ctrl.anchorTx * p + ctrl.titleCorr"
            " * catchUp, ctrl.titleTy * p);") in js
    assert ("if (ctrl.sub) textMove(ctrl.sub, ctrl.anchorTx * p + ctrl.subCorr"
            " * catchUp, ctrl.subTy * p);") in js
    # 1.8.55 换行标题只收第一行: 量第一行的行盒 (Range), 第二行起随行程
    # clip-path 从底边裁掉 —— 裁口在本地坐标里, 缩放同步作用其上, 裁缝
    # 永远落在行缝; 单行标题 titleClip=0 照旧 (✎ 铅笔位不扰动)
    assert "const tRange = document.createRange();" in js
    assert "tRange.selectNodeContents(title);" in js
    assert "const tLines = tRange.getClientRects();" in js
    assert "const titleClip = tLines.length > 1" in js
    assert "? Math.max(0, titleRect.bottom - tLines[0].bottom) : 0;" in js
    assert ("const stackH = (subRect ? subRect.bottom - titleRect.top"
            " : titleRect.height)") in js
    assert "- titleClip;" in js
    assert "? stackY + (subRect.top - titleRect.top - titleClip) * textScale" in js
    assert "title, sub, titleClip, titleCutR," in js
    # 1.8.112 宽度退出缩放 (用户点名「字体不需要变小」): 字号不再为塞进
    # 条簇缩小 (缩放只剩「两行摞塞进 44」的轻收); 溢出右刀单行也吃, 后段
    # (0.55 起) 才走 —— 与渐隐纱同一条坡进场, 纱没上不硬切字, 终点正好
    # 切在条簇左缘 (availW 边界); 底刀 (1.8.55) 照旧乘 p 随缩放走
    assert "const titleCutR = Math.max(0, titleRect.width - availW);" in js
    assert "if (ctrl.titleClip || ctrl.titleCutR)" in js
    assert "const rCut = ctrl.titleCutR * Math.min(1, Math.max(0, (p - 0.55) * 2.5));" in js
    assert "`inset(0px ${rCut.toFixed(1)}px`" in js
    assert "+ ` ${(ctrl.titleClip * p).toFixed(1)}px 0px)`;" in js
    # 摘样式: 重测量前/回自然位共用一枚 heroReset (1.8.113 抽出, 原先两处
    # 逐行抄), clipPath 清空只出现一回
    assert "const heroReset = (els) => {" in js and js.count("heroReset([") == 2
    assert js.count('el.style.clipPath = "";') == 1
    # 顶栏动作条让位 (1.8.45): 右刀按收拢态的条宽算, 别钻到键底下;
    # 条宽/起飞位/槽位都由 heroBarMeasure 量 (见 test_music_hero_bar),
    # 开 … 多挤出来的宽压住文字由 .bar-sheen 阴影渐隐, 不重算
    assert "const barInfo = heroBarMeasure(head, rowButtons, headRect);" in js
    assert "const availW = contentW - HERO_MINI - 12 - barInfo.barRowW - 10;" in js
    assert "heroBarTravel(ctrl, p);" in js
    # 操作行的键一进收缩就藏 (1.8.46): 顶栏那套从它们的键位起飞接班
    # (起飞位逐像素重合, 两套不同屏), 藏着的键也不再截点
    assert ('for (const btn of ctrl.rowButtons) {\n    btn.style.opacity = "0";\n'
            '    btn.style.pointerEvents = "none";\n  }') in js
    # 淡出的只剩散块小字/换封面角标 (0.6 行程淡尽) + 上飘 + 淡尽不再挡点
    assert "const fades = [...hero.children].filter((el) => el !== cover && el !== text);" in js
    assert 'el.style.pointerEvents = p > 0.35 ? "none" : "";' in js
    # 转屏/改窗宽: 宽度哨兵触发懒重测; 元素断线 (重铺) 也重测
    assert "ctrl.width !== scroller.clientWidth" in js
    assert "!ctrl.head.isConnected" in js


def test_music_1840_short_list_and_sideways():
    """1.8.40 两件配套 (用户报的): 短列表补行程 —— 滚到底也够不着收缩
    行程的页, JS 量差值写 --hero-extra 垫高底部空隙 (CSS 加在船坞让位
    之上, 变量没写时缺省 0), 上划一路有得滑直到顶栏收齐、空间归位;
    横向晃动修复 —— 层内滚动器/主页滚动器只写 overflow-y 时横向按 auto
    算, iOS 给单向滚动器也配横向橡皮筋, 竖滑稍带偏整层左右荡 —— 横向
    显式掐掉 (右划返回走 JS 手势, 不受影响)。"""
    html = music_page_shell()
    js = music_browser_js()
    # 补行程: scrollHeight 被 clientHeight 钳住 (内容比视口矮时报视口高),
    # 一步量的差值没算进「没填满视口」那截 —— 先归零再「补一步、量一步」
    # 收敛 (两首歌的歌单上划卡在一半就是这个坑, 用户报的)
    assert 'scroller.style.setProperty("--hero-extra", "0px");' in js
    assert ("const shortfall = ctrl.dist - (scroller.scrollHeight"
            " - scroller.clientHeight);") in js
    assert "extra += shortfall;" in js
    assert 'scroller.style.setProperty("--hero-extra", `${Math.ceil(extra)}px`);' in js
    assert "padding-bottom: calc(var(--dock-clear) + var(--hero-extra, 0px));" in html
    pane_css = html[html.index(".push-pane .pane-scroll {"):html.index(".album-hero")]
    assert "overflow-x: hidden;" in pane_css
    main_css = html[html.index("main {"):html.index("#root-view {")]
    assert "overflow-x: hidden;" in main_css


def test_music_1834_hero_collapse_css():
    """顶栏的壳: 页头 sticky 钉层顶, ::before 实底罩到顶栏下沿 (其下
    透明 —— 收缩途中列表照常从底下穿过, 不是一整块死盖), ::after 血线按
    --hero-p 后段浮现; 头自身放行点按, 头里的可点元素逐个接回。
    钉顶控件不吃 env+14: 页头整体落在全局上边界 --top-clear 之下
    (1.8.19 立的规矩, 与搜索页头/播放页抓手同一条线 —— 收缩后的小顶栏
    和展开时 sticky 钉住的页头都不进系统磨砂带)。"""
    html = music_page_shell()
    hero_css = html[html.index(".hero-head {"):html.index(".hero-head .album-hero > img")]
    for frag in [".hero-head {", "position: sticky; top: 0; z-index: 5;",
                 "padding: var(--top-clear) 16px 0;",
                 '.push-pane[data-view="album"] .pane-scroll,']:
        assert frag in html, f"收缩顶栏样式缺 {frag}"
    assert "padding: var(--top-clear) 16px 0;" in hero_css   # 边界让位在头上
    # 顶栏下沿 = --top-clear + 52px (52 = 封面 44 + 下沿呼吸 8, 1.8.45 单行
    # 顶栏 —— 按钮上到封面那行, 第二行撤了), 与 JS 的 HERO_BAR 同源;
    # 52px 出现两回 (::before 一截 + ::after 血线一扣)
    assert html.count("calc(var(--top-clear) + 52px)") == 2
    assert "opacity: min(1, max(0, calc((var(--hero-p, 0) - 0.75) * 4)));" in html
    assert ".hero-head .action-row > button { pointer-events: auto; }" in html
    # 副标题行 (.hero-sub: 艺人/年份/时长并一行) 的样式 —— 缩进上行时
    # 跟主标题同块一起缩 (用户点名「缩小之后副标题也需要, 比如8首14分钟」)
    assert ".hero-sub { margin-top: 3px; display: flex; align-items: baseline;" in html
    assert ".hero-meta { color: var(--ink-3); font-size: 12px; }" in html
    # 1.8.42 左对齐的根: 两行各自收缩到内容宽 (JS 量的就是字面实宽, 左缘
    # 才贴得准封面右边); 展开态两行仍居中, 渲染与块级 + text-align 逐像素同款
    assert ".hero-txt { margin-top: 14px; max-width: 100%; display: flex;" in html
    # 三个详情层各自的滚器撤掉顶部留白 (顶栏从层顶就位)
    for view in ["album", "playlist", "artist"]:
        assert f'.push-pane[data-view="{view}"] .pane-scroll' in html
