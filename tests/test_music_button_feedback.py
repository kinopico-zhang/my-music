"""My Music 按钮果冻反馈测试 (1.8.48, 用户点名「按钮点击都加上果冻 q 弹
的效果, 给用户反馈他已经点到按钮了」; 1.8.49 修「播放键点一下闪一下」:
改走 Web Animations 合成器动画 —— 头一版挂类+强制回流在磨砂底上闪白)。
按下那刻全局监听给键播压扁回弹, 只动 transform 不碰布局; 按住拖走当场
收回 (那是手势不是点按); 接点条/补发补出来的合成 click 没有按下那一
下, 那两处各自补调 jellyButton —— 惯性里点 播放/… 也有反馈。
静态文本断言, 不碰数据库。"""


from tests.music_static_files import music_browser_js, music_page_shell


def test_music_1848_button_jelly():
    """按下即弹: 全局 pointerdown 播合成器动画 (连点上一下让位); 拖走/
    取消收回不给假反馈; 合成 click (接点条/补发) 也补弹。"""
    js = music_browser_js()
    html = music_page_shell()
    # JS: 合成器动画 (1.8.49 起) —— 不挂类不强制回流, 键自占一层不闪磨砂
    for frag in ["function jellyButton(btn) {",
                 'matchMedia("(prefers-reduced-motion: reduce)")',
                 "if (jellyReducedMotion.matches) return;",
                 'if (anim.id === "jelly") anim.cancel();',
                 'target.animate([{ transform: "scale(1)" },',
                 '{ transform: "scale(.92, .84)", offset: .25 },',
                 '{ transform: "scale(1.06, 1.04)", offset: .55 },',
                 '{ transform: "scale(.98, .99)", offset: .8 },',
                 'const btn = event.target.closest("button");',
                 "if (!btn || btn.disabled) return;",
                 "const press = new AbortController();",
                 "if (Math.hypot(ev.clientX - x, ev.clientY - y) > 10) cancel();",
                 "press.abort();"]:
        assert frag in js, f"果冻反馈缺 {frag}"
    # 1.8.51: 带蒙底衬底的键 (收拢顶栏播放键挂 .jelly-glyph, 衬底蒙着底下
    # 被挤的标题) 只弹键心里的图标 —— 整键缩放会把衬底一起压扁, 字从边上
    # 漏出来闪一下; 拖走收回也认 jellyTarget
    for frag in ["function jellyTarget(btn) {",
                 'btn.classList.contains("jelly-glyph")',
                 'btn.querySelector("svg") || btn',
                 "const target = jellyTarget(btn);",
                 "jellyTarget(btn).getAnimations()",
                 'primary jelly-glyph']:
        assert frag in js, f"只弹图标缺 {frag}"
    # 挂类那套 (1.8.48 头版) 真撤干净了 —— 它在磨砂底上闪白
    assert "jelly-press" not in js and "jelly-press" not in html
    assert "void btn.offsetWidth" not in js
    # 接点条/补发的合成 click 也补果冻 (惯性里的点按有反馈)
    assert "if (btn) { jellyButton(btn); btn.click(); }" in js
    assert "jellyButton(btn);                  // 合成点按也给果冻反馈" in js
    # 1.8.52 用户收窄: 只有列表页操作排 (.action) 和顶栏键 (.bar-btn) 弹,
    # 列表行/封面 (本来就是 <button>) 不弹 —— 闸门在 jellyButton 里,
    # 按下/接点条/惯性补发三条路一并管住
    for frag in ['!btn.classList.contains("action")',
                 '!btn.classList.contains("bar-btn")) return;']:
        assert frag in js, f"果冻收窄缺 {frag}"
