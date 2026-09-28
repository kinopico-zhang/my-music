"""My Music 收缩顶栏动作条测试 (1.8.45 单行条 + 1.8.46 路径换岗三改), 拆自
test_music_hero_collapse.py (文件超 200 行按域再拆): 顶栏右侧 播放 + … 的
生成/接线/样式, 与 1.8.46 的沿路径平移换岗 (错峰弧线途中不叠 + 遮罩罩满
整个按钮区域 + 四改: 五键等距/飞行上 GPU 层 + 五改: 渐隐纱钉在收拢簇左
缘 + 六改: 键衬底左缘 20px 半透明过渡 + 七改: 停稳补程 + 九改: 补程只管行程中间)。
被吞点按的补发 (十改二轮) 拆去 test_music_hero_tap.py。静态文本断言, 不碰数据库 (插值是纯几何, 轴距由 node 单测
tests/js/hero-bar-travel.test.mjs 逐帧验, 手感真机眼验)。"""
from tests.music_static_files import music_browser_js, music_page_shell


def test_music_1845_hero_bar_actions():
    """1.8.45 单行顶栏的动作条 (用户点名「五个按钮收缩成播放和 … 两个按钮,
    和封面放在一行右对齐; … 放在边上, 点击后 随机/下载/分享/删除 出来顶替
    它、把播放按钮往左边挤; 挤占了标题的空间就阴影过渡一下」): 独立的
    .hero-bar-actions 一套键接班, … 开合只动 width/opacity —— 收缩动画
    零重排的根不能破。1.8.46 起这套键沿路径从操作行平移进来 (下个测试),
    不再两套交叉淡入淡出。"""
    html = music_page_shell()
    js = music_browser_js()
    # 生成器: play 之外的键 ≥2 颗才收进 … (艺人页就一颗随机, 直接亮出来);
    # … 键带 data-bar-more, 额外键包 .bar-extras
    for frag in ["function heroBarHTML(acts) {",
                 '(Object.keys(acts).length >= 3',
                 'data-bar-more title="更多操作"',
                 '<span class="bar-extras">${extras}</span>',
                 '<div class="hero-bar-actions"><span class="bar-sheen"']:
        assert frag in js, f"动作条生成器缺 {frag}"
    # 接线: … 开合 + 动作键分派到视图闭包, 干完活自动收回; 监听只绑一次
    for frag in ["function wireHeroBarActions(scope, handlers) {",
                 'if (btn.dataset.barMore !== undefined) {',
                 "head.classList.toggle(\"bar-open\");",
                 "const run = handlers[btn.dataset.barAct];",
                 "head.classList.remove(\"bar-open\");      // 动作键: 干完活收回去"]:
        assert frag in js, f"动作条接线缺 {frag}"
    # 进度回话: 到位 (p≥0.8, 与飞行结束同一刻) 才开闸 —— 中途开 … 的话
    # 展开态槽位和飞行落点对不上会错位, 惯性里被吞的点按由补发接手 (下
    # 组); 上滑往回飞 (第三参) 过 0.9 才收 … 菜单 —— 下滑到位途中开着不收
    assert "function heroBarTick(head, p, back) {" in js
    assert 'head.classList.toggle("bar-live", p >= 0.8);' in js
    assert 'if (back && p < 0.9) head.classList.remove("bar-open");' in js
    assert "heroBarTick(ctrl.head, p, p < ctrl.p);" in js
    # 三个视图各渲染一条动作条、各接一回线 (播放列表多一颗删除)
    assert js.count("heroBarHTML({") == 3
    assert js.count("wireHeroBarActions(target, {") == 3
    assert "delete: deleteThisList," in js
    # 播放列表/专辑的禁用态与操作行同步 (无可播曲目时键也是灰的)
    assert "play: !!playable.length, shuffle: !!playable.length," in js
    # 条的样式: 键未开闸不可点、… 收宽、额外键的箱、遮罩后段浮现;
    # 五改起纱退出弹性流 —— 条靠 justify-content: flex-end 右贴
    for frag in [".hero-bar-actions {",
                 "align-items: center; justify-content: flex-end;",
                 "opacity: min(1, max(0, calc((var(--hero-p, 0) - 0.55) * 2.5)));",
                 ".hero-bar-actions button { pointer-events: none; }",
                 ".hero-head.bar-live .hero-bar-actions button { pointer-events: auto; }",
                 ".hero-head.bar-open .bar-btn.more "
                 "{ width: 0; margin-left: -8px; opacity: 0; }",
                 ".hero-head.bar-open .bar-extras { max-width: 260px; opacity: 1; }",
                 ".bar-sheen {",
                 "background: linear-gradient(to right, "
                 "transparent calc(100% - 150px), var(--bg));"]:
        assert frag in html, f"动作条样式缺 {frag}"
    # … 的图标 (三点横排) 进了公共图标件, 生成器拿它渲染
    assert "ICON_ACTION_MORE" in js
    # 桌面端同款手感: 悬停亮一档 + 图标钮悬停出文字提示
    assert 'html[data-input="keymouse"] .bar-btn:hover { background: var(--surface-3); }' in html
    assert 'html[data-input="keymouse"] .bar-btn:hover::after {' in html


def test_music_1846_bar_path_travel():
    """1.8.46 路径换岗 (用户点名「控制按钮平移不要闪现, 要通过路径丝滑
    平移过去」): 两套键交叉淡入淡出废了 —— 顶栏那套键沿路径从操作行的
    键位平移进槽位, 起飞位与行键逐像素重合所以换岗无闪; 行程前段走完,
    到位与 .bar-live 开闸同一刻行内样式全摘。三改 (用户点名「控件移动
    不一定非要走直线, 你计算一下, 要这几个控件移动的过程中不要有重叠
    的时刻」): 收拢键错峰走弧线 (近的先到, 到场前自淡落进 … 里), 途中
    两两不叠 —— 纯几何的排程/取位拆成 heroBarPlanLanes/heroBarPointAt,
    node 直测 (tests/js/hero-bar-travel.test.mjs 按真机几何逐帧验轴距);
    遮罩罩满整个按钮区域 (用户点名): 播放键整高衬底 + 额外键箱整高衬底。"""
    html = music_page_shell()
    js = music_browser_js()
    # 量位: 自然态里量 (先收 … 菜单、摘净行内样式), 行键与条键按序配对
    # (两套同源同序); 收拢键保住 0.4 底透明度 (禁用键飞着也不满亮)
    for frag in ["function heroBarMeasure(head, rowButtons, headRect) {",
                 'head.classList.remove("bar-open");       // 量宽前先收菜单, 展开态不算数',
                 "info.barRowW = play ? bar.clientWidth - play.offsetLeft : 0;",
                 "const s0 = lw ? fw / lw : 1;",
                 "s1: fade ? s0 : s1, fade, base: el.disabled ? 0.4 : 1,",
                 "arr: 1, bx: 0, by: 0 });",
                 "flyer(play, rowButtons[0], play, 1, false);",
                 "heroBarPlanLanes(info.flyers);"]:
        assert frag in js, f"路径量位缺 {frag}"
    # 收拢进 … vs 各飞各的槽 (艺人页没有 …, 随机键直接亮出来); 收拢的键
    # s1 = s0 —— 全程不缩, 全尺寸飞完, 不是缩没了
    assert "const sink = !!more;" in js
    assert "sink ? more : el," in js and "1, sink));" in js
    # 错峰排程 + 弧线 (纯几何, node 直测): 按到 … 的路程排序, 近的先到场;
    # 各自沿弦的法向 (右下) 弓出 sin(πe) 的弧, 两端归零 —— 起飞/落位
    # 仍是原位; 领头弓得最大、追兵越小 —— 途中两两不叠
    for frag in ["const HERO_BAR_STEP = 0.22;",
                 "const HERO_BAR_FADE = 0.32;",
                 "function heroBarPlanLanes(flyers) {",
                 "sink.sort((a, b) => a.len - b.len);",
                 "f.arr = 1 - (sink.length - 1 - r) * HERO_BAR_STEP;",
                 "const bow = Math.max(6, 24 - 6 * r);",
                 "function heroBarPointAt(f, k) {",
                 "const u = Math.min(1, k / f.arr);",
                 "const arc = Math.sin(Math.PI * e);"]:
        assert frag in js, f"错峰弧线缺 {frag}"
    # 平移: 飞行窗口 p 0.05→0.8 (到位与 .bar-live 开闸同一刻), smoothstep
    # 缓动; 中心插值 + 缩放, 只写 transform/opacity (零重排不破)
    for frag in ["function heroBarTravel(ctrl, p) {",
                 'ctrl.head.classList.toggle("bar-fly", p > 0 && p < 0.8);',
                 "const t = Math.min(1, Math.max(0, (p - 0.05) / 0.75));",
                 "const k = t * t * (3 - 2 * t);",
                 "const [x, y, u, e] = heroBarPointAt(f, k);",
                 "` scale(${(f.s0 + (f.s1 - f.s0) * e).toFixed(4)})`;",
                 "if (t >= 1) { rest(); return; }"]:
        assert frag in js, f"路径平移缺 {frag}"
    # 收拢键到场前自淡 (落进 … 那一刻正好淡尽 —— 追兵压到一键宽内时,
    # 先到的已淡尽, 谁也压不着谁); … 键在头一颗落位前后显形接场
    assert "const gone = Math.min(1, Math.max(0," in js
    assert "/ HERO_BAR_FADE));" in js
    assert "const mo = Math.min(1, Math.max(0, (k - 0.2) / 0.8));" in js
    # 样式: 条只在飞行 (bar-fly) 或到位 (bar-live) 显形 —— 没挂线/没滚过
    # 就不露脸; 飞行中额外键出裁剪箱走路径; min-width 0 钉死箱宽 ——
    # overflow 放行时弹性项的最小内容宽会把箱撑开, 纱被挤短、起飞位
    # 跟着漂 (三改修的根)
    for frag in [".hero-head.bar-fly .hero-bar-actions,",
                 ".hero-head.bar-live .hero-bar-actions { opacity: 1; }",
                 ".hero-head.bar-fly .bar-extras {",
                 "overflow: visible; opacity: 1;",
                 "min-width: 0; align-self: stretch; align-items: center;",
                 "overflow: hidden; opacity: 0; background: var(--bg);",
                 "transparent calc(100% - 150px), var(--bg));"]:
        assert frag in html, f"路径换岗样式缺 {frag}"
    # 四改 (用户报「5个图标展开后不等间距」+「动画还有点掉帧」): 首键让回
    # 8px —— 五颗键等距 (箱左缘贴死播放键是为了衬底, 缝在箱里让回来);
    # 飞行键各上 GPU 合成层治掉帧; 起飞那刻箱和 … 键的透明度过渡归零
    # (吃基态 250ms 淡入会先暗一下再亮, 行内每帧值也会吊在目标后面)
    assert ".bar-extras > button:first-child { margin-left: 8px; }" in html
    assert ".hero-head.bar-fly .hero-bar-actions button { will-change: transform, opacity; }" \
        in html
    assert "transition: opacity 0s, max-width .3s ease;" in html
    assert "transition: opacity 0s, width .3s ease, margin-left .3s ease;" in html
    # 遮罩罩满整个按钮区域 (用户点名): 条自成层叠上下文, 播放键 36 高在
    # 44 行里露的上下 4px 由 z:-1 整高衬底罩住 (飞行中键带 transform 会
    # 建 layer 上下文, z:-1 反压键面 —— 飞行中先别衬, … 收着键底下没字)
    assert "isolation: isolate;" in html
    assert ".bar-btn.primary::before {" in html
    # 六改 (你点的「按钮和被遮盖的文字之间加一点缓冲」): 衬底左缘加
    # 20px 半透明过渡 —— 被盖住的字贴着键边淡下去不硬切; 软边长在键上,
    # 键到哪跟到哪 (收拢/开 … 途中都在), 不与纱的钉位耦合
    assert "position: absolute; left: -20px; right: 0; top: -4px; bottom: -4px;" in html
    assert "background: linear-gradient(to right, transparent, var(--bg) 20px);" in html
    assert ".hero-head.bar-fly .bar-btn.primary::before { display: none; }" in html
    # 七改 (你报的「…要点第二下才行」): 收拢靠惯性滚完, iOS 把惯性中的
    # 头一下点按吞成「停滚」。停稳 (160ms 无滚动事件) 自动补程 —— 过半滑
    # 到底收齐、不到半弹回; 手指按着不补, … 开着照补 (顶栏钉死)
    for frag in ["const heroSnapTimers = new WeakMap();",
                 "const heroTouching = new WeakSet();",
                 'scroller.scrollTo({ top: target, behavior: "smooth" });',
                 "if (heroTouching.has(scroller) || !ctrl || !ctrl.head.isConnected) return;",
                 'scroller.addEventListener(ev, () => heroTouching[fn](scroller),']:
        assert frag in js, f"停稳补程缺 {frag}"
    # 九改 (你报的「深处翻列表, 每次滑动结束自动回到顶端」): 补程目标原
    # 先拿整个滚动范围当收缩行程 —— 深处任何一次停稳都被拽回列表顶。现
    # 在只管行程中间: 已收齐 (≥dist) = 人在翻列表, 不碰
    for frag in ["const t = scroller.scrollTop;",
                 "const target = t >= ctrl.dist - 2 ? t",
                 "if (Math.abs(t - target) > 2) {"]:
        assert frag in js, f"九改行程范围缺 {frag}"
    # 十改二轮起被吞点按的补发拆去 test_music_hero_tap.py (本文件超 200
    # 行按域再拆); 五改 (你报的「按钮旁边的遮挡问题」): 纱原先是弹性项, 开
    # … 时跟着播放键左缘一起左移 —— 渐隐整片扫过没被任何键压到的标题 (真机上量到
    # 副标题被抹到只剩一成亮)。现在纱改绝对定位钉在收拢簇左缘:
    # right = collapse.js 量来的收拢簇宽 (--bar-row-w), 开 … 簇往左长、
    # 纱不动 —— 没压到字就别渐隐; 绝对定位的纱会画在流内键之上, 学播放
    # 键衬底那招压 z:-1 (条已 isolation, 压得过页头文字、翻不到键面);
    # 渐隐段拉宽到 150 —— 开 … 时贴播放键左缘还留一小段过渡
    assert "position: absolute; left: 0; top: 0; height: 44px; z-index: -1;" in html
    assert "right: var(--bar-row-w, 80px);" in html
    # 十改三轮起簇宽写在层根 (接点条在层根按它对位; 无层兜底写回头上)
    assert '(head.closest(".push-pane") || head)' in js
    assert '.style.setProperty("--bar-row-w", `${Math.ceil(barInfo.barRowW)}px`);' in js
