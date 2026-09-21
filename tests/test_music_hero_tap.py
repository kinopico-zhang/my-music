"""My Music 收缩顶栏被吞点按修法测试 (1.8.46 十改三轮), 拆自
test_music_hero_bar.py (文件超 200 行按域再拆): iOS 把惯性滚动中的点按
整个吞给滚动器 —— touchstart 都不派给滚动器内容 (SO 49468413: 惯性期间
约 500ms), 挂在页头上/提到 document 的监听都收不到, touch-action 也拦
不住; 船坞键没这毛病因为在滚动器外面 —— 照方抓药在层根 (滚动器外) 铺
接点条罩住收拢簇。静态文本断言, 不碰数据库。"""
from tests.music_static_files import music_browser_js, music_page_shell


def test_music_1846_eaten_tap_catcher():
    """十改三轮 (你报的「惯性里点 播放/… 只是把列表停住, 重开还是不行」+
    「感觉下面的列表把点击按钮事件劫持了」—— 感觉是对的): 层根 (滚动器
    外) 铺 .hero-bar-catch 接点条, heroBarTick 在 p≥0.8 给层挂 .bar-catch
    开闸 (与 .bar-live 同一刻) —— 接点区罩住收拢簇, 点按按矩形认出底下
    的真键补一发 click (冒泡到 wireHeroBarActions 照常分派); 惯性里 iOS
    不吞滚动器外的点按, 所以一下就灵。"""
    js = music_browser_js()
    html = music_page_shell()
    for frag in ["function heroTapRectBtn(bar, x, y) {",
                 "function wireHeroBarTapRecovery(scope) {",
                 'scope.closest(".push-pane");',
                 'pane.querySelector(".hero-bar-catch")',
                 '"<div><span></span></div>"',
                 "heroTapRectBtn(bar, e.clientX, e.clientY);",
                 "pane.appendChild(strip);"]:
        assert frag in js, f"接点条缺 {frag}"
    # 开闸同步挂层根 (接点条这时才接点), 簇宽写在层根 (接点条对位用;
    # 无层兜底时写回头上 —— 纱在头里也按它钉位)
    for frag in ['const pane = head.closest(".push-pane");',
                 'pane.classList.toggle("bar-catch", p >= 0.8);',
                 '(head.closest(".push-pane") || head)']:
        assert frag in js, f"接点条开闸缺 {frag}"
    # 样式: 条铺层根 z6 压过页头 z5; 列壳与 .pane-scroll 同款 860px 列
    # (宽屏对齐); 接点区罩收拢簇 (簇宽/顶隙同源), 点按不当滚动手势
    # (touch-action: none, click 必来); 桌面端摘接点权 (悬停归真键)
    for frag in [".hero-bar-catch {",
                 "position: absolute; inset: 0; z-index: 6;",
                 ".hero-bar-catch > div { width: 100%; max-width: 860px;",
                 "width: var(--bar-row-w, 80px); height: 52px;",
                 "pointer-events: none; touch-action: none;",
                 ".push-pane.bar-catch .hero-bar-catch span { pointer-events: auto; }",
                 'html[data-client="desktop"] .hero-bar-catch span '
                 "{ pointer-events: none; }"]:
        assert frag in html, f"接点条样式缺 {frag}"


def test_music_1846_eaten_tap_fallback():
    """document 级兜底补发留着 (接点条没罩住的场合: 操作行的键/开 … 后的
    额外键/还在飞的键): pointer+touch 双通道都听 (iOS 惯性里有时只走
    pointer 通道; 同一下只记一回), 认键按落点现场查 elementsFromPoint ——
    只认视觉最上层那个层的页头 (被推入层/遮罩盖住的不抢; 接点条罩着的
    键 pe:none 穿透, 退回条里按矩形认, rect 跟着飞行变换走、淡尽的键不
    抢)。真点按 20ms 内必到 (来了撤记不重发 —— 接点条的补发 click 也算
    真点按, 两条路不会双发); 没来把这一下记下: 条键等开闸到位再补 (12×
    90ms 等收齐, 滑回首了键没了就不补), 操作行的键本来就在原位直接补。"""
    js = music_browser_js()
    for frag in ["function heroTapBtnAt(x, y) {",
                 "const top = document.elementsFromPoint(x, y)[0];",
                 'top.closest(".push-pane")',
                 "if (direct && head.contains(direct)) return direct;",
                 'for (const ev of ["pointerdown", "touchstart"]) {',
                 'for (const ev of ["pointerup", "pointercancel", "touchend", "touchcancel"]) {',
                 'const inBar = !!btn.closest(".hero-bar-actions");',
                 "if (tries++ < 12) setTimeout(fire, 90);",
                 'document.addEventListener("click", () => { eaten = null; }, true);',
                 "wireHeroBarTapRecovery(scope);"]:
        assert frag in js, f"被吞点按的兜底缺 {frag}"
