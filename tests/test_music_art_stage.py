"""My Music 播放页 3D 封面舞台接线测试 (1.8.60): 上一首/下一首斜插两侧,
左右拖跟手, 松手 3D 落定切歌。1.8.61 修「切歌很卡」: 姿态改 JS 直落
每张卡的行内 transform/filter + 原生过渡 (合成器线程插值)。
1.8.62 修「3D 穿模」: 平面叠放 + JS 显式排 z, 不靠引擎深度排序。
1.8.65 修「侧卡突兀跳到前卡上面」: 换曲那拍旧曲卡压顶 (z5) 溶出让位。
1.8.66 修「过场重叠穿模」: 中段扇形张开 (过卡那拍两侧分最开), 来卡过半
浮上旧卡沉底 —— 翻层藏进缝最大处。1.8.67 修「旧封面闪没再闪回」: 拖动
松手不交班溶解 (缝里层序天然接对), 交班只留程序切歌。"""


from tests.music_static_files import MUSIC_STATIC, music_page_shell


def test_music_art_stage_wiring():
    """1.8.60 (用户点名「封面两边显示上一首下一首, 立体视角, 左右划 3D
    切换」): 三张卡按槽位 (自身位 + 拖拽进度) 摆横移/纵深/转角/压暗。
    切歌落定: 松手余位 (1+d / d-1) 递给换曲回调接力, 不许跳位; 程序切歌
    (按钮/自然播完) 按队列走向猜来向从侧面滑入; 没换成 (队尾顶住/回本曲
    开头) 就地弹回。旧的平移滑出滑入 (swipeCoverTo) 退役。
    1.8.61 修「切歌很卡」: 姿态 JS 直落行内 transform/filter, 松手走原生
    过渡 (合成器线程); 队列视图没开着也不整页重铺 (翻开时会现铺)。
    1.8.62 修「3D 穿模」: 撤 preserve-3d 深度排序 (挂着 filter 的卡
    Safari 不参与排序, 对穿时图层乱序) —— 平面叠放显式排 z。
    1.8.65 修「侧卡突兀跳到前卡上面」(用户回评「换一种 3D 动画方式,
    更自然, 更顺滑」): 1.8.62 的拖过半翻 z (.rise-next/.rise-prev) 在
    40% 重叠带上硬跳层。改为换曲那一拍退去的旧曲卡 .handoff 压顶 (z5)
    溶出让位, 淡完落回侧卡层 (z1) 再淡回显形; 交班半路被接走
    (拖拽接手/又换曲) 就地平回。
    1.8.66 修「滚动时重叠和穿模」(用户点名「左右两个封面分得再开一点」):
    过场中段扇形张开 —— fanOf 槽位倍率在 |slot|=0.5 (两卡交会那拍) 峰值
    ×(1+STAGE_FAN), 静止/越台收回 1 (侧卡原地不挪); 张开后交会处两卡
    分开 ~44px, 拖过半的翻层 (.rise-next/.rise-prev, z4) 藏在缝最大处
    翻, 肉眼看不见 —— 松手那拍两卡分在缝两侧, 层序交换落在缝里本来就
    看不见, 不用交班; 只有程序切歌 (按钮/自然播完, 全叠) 才走 1.8.65 的
    交班溶解。1.8.67 修「旧封面闪没再闪回」(用户报「滑动封面的时候, 旧
    的封面会消失一下再出现」): 1.8.66 首版给 |d|<0.5 的松手也挂了溶解
    —— 可扇形把两卡分开了, 溶解不再是交叠处的互相显影, 旧卡在缝里
    孤零零淡出又淡回。撤掉拖动路径的交班, 溶解只留程序切歌; 半路抓
    落定中的封面, 横移≠sway (扇形展开过) 由定点迭代反解。
    1.8.97 修「滑一点点松手被取消」(用户点名「很短的滑行轨迹也要完成
    切歌」): 认领的横滑松手一律切歌, 方向按舞台倒向 (含半路抓取的
    swayBase), 只有倒向不足 4px 且没甩劲才放回; pointercancel 弹回不切。"""
    html = music_page_shell()
    css = (MUSIC_STATIC / "css" / "music-player.css").read_text(encoding="utf-8")
    stage_js = (MUSIC_STATIC / "js" / "music-player-art-stage.js").read_text(
        encoding="utf-8")
    events_js = (MUSIC_STATIC / "js" / "music-player-events.js").read_text(
        encoding="utf-8")
    fullpage_js = (MUSIC_STATIC / "js" / "music-player-fullpage.js").read_text(
        encoding="utf-8")
    queue_js = (MUSIC_STATIC / "js" / "music-player-queue.js").read_text(
        encoding="utf-8")
    # 三张卡: 上一首/下一首 + 当前曲 (DOM 在最后, 兜底画在最上)
    assert 'id="fp-art-prev"' in html and 'id="fp-art-next"' in html
    assert 'class="art-card"' in html
    # 姿态直落行内样式: 原生 transform/filter 过渡 (合成器线程), 拖动中
    # .dragging 掐过渡跟手; 静止姿态写在选择器上当开局兜底
    assert "@property" not in css and "--sway" not in css and "--k" not in css
    assert "transition: transform .36s cubic-bezier(.22,.61,.36,1)," in css
    assert "will-change: transform, filter;" in css
    assert "#fp-art-wrap.dragging .art-card { transition: none; }" in css
    # 平面叠放显式排 z (preserve-3d 深度排序撤了 —— Safari 对挂 filter
    # 的卡不排序, 对穿时图层乱序 = 穿模); 交班层压顶, opacity 同走过渡
    assert "transform-style: preserve-3d;" not in css
    assert "perspective: 920px;" in css
    assert "#fp-art { transform: translateZ(0); z-index: 3; }" in css
    assert ".art-card.handoff { z-index: 5; }" in css
    assert "opacity .3s cubic-bezier(.22,.61,.36,1);" in css
    for frag in ["#fp-art-prev { transform: translateX(-55%) translateZ(-150px)"
                 " rotateY(-40deg);",
                 "#fp-art-next { transform: translateX(55%) translateZ(-150px)"
                 " rotateY(40deg);",
                 ".art-card.off { visibility: hidden; }"]:
        assert frag in css, f"封面舞台样式缺 {frag}"
    # 邻居只读不动队列: 队首没上一首 (goBack 是回本曲开头), 队尾看循环模式
    for frag in ["function stageNeighbors", "playQueue.position > 0",
                 'playQueue.repeat === "all" && order.length > 1',
                 "function poseCard", "function poseStage", "function fanOf",
                 "function stageAnimatedSway", "function renderArtStage",
                 "function clearHandoff", "function commitStage",
                 "function bindArtStageDrag", "function initArtStage"]:
        assert frag in stage_js, f"art-stage 缺 {frag}"
    # 1.8.95 气泡横滑也来取邻居 (拖动中预览邻曲): 跨文件读, exported 挂上
    assert "/* exported initArtStage, stageNeighbors */" in stage_js
    # 落定: 掐过渡先摆起跳位 (一帧内完成不跳位), 再放过渡滑回中间
    assert "poseStage(from !== null ? from : 0);" in stage_js
    # 姿态公式: 横移按卡宽 (槽位×55%)×扇形倍率, 深度/压暗按槽位平方
    assert "const STAGE_SPACING = 0.55;" in stage_js
    assert "const STAGE_DEPTH = 150;" in stage_js
    assert "`translateX(${slot * STAGE_SPACING * fanOf(slot) * 100}%)`" in stage_js
    assert "` translateZ(${slot * slot * -STAGE_DEPTH}px)`" in stage_js
    # 1.8.66 扇形张开: |slot|=0.5 (交会那拍) 峰值 ×(1+STAGE_FAN), 两端收回 1
    assert "const STAGE_FAN = 1;" in stage_js
    assert "return 1 + STAGE_FAN * 4 * t * (1 - t);" in stage_js
    assert "const t = Math.min(1, Math.abs(slot));" in stage_js
    # 换曲回调接线 + 落定接力: 余位传给 renderArtStage, 没换成就地弹回
    assert "onTrackChange(stageTrackChanged);" in stage_js
    assert "swayFrom = direction === \"next\" ? 1 + d : d - 1;" in stage_js
    assert "playerNext();" in stage_js and "playerPrevious();" in stage_js
    assert "if (currentTrack !== before) return;" in stage_js
    # 半路抓住落定中的封面: 读当前卡实时横移 (过渡插值就在 computed 里);
    # 扇形展开后横移≠sway, 定点迭代反解 (真解∈[px/2, px])
    assert "new DOMMatrixReadOnly(matrix).m41" in stage_js
    assert "for (let i = 0; i < 3; i++) s = px / fanOf(s);" in stage_js
    # 1.8.97 松手一律切歌 (用户点名「很短的滑行轨迹也要完成切歌」): 方向按
    # 舞台倒向 (px 口径, 不再卡 28% 份额), 倒向不足 4px 且没甩劲才放回;
    # 系统掐掉 (pointercancel) 弹回不切; 竖向让给下拉收起
    assert "const dir = Math.abs(d) * width >= 4 ? Math.sign(d)" in stage_js \
        and ": (Math.abs(hVelocity) > 0.1 ? Math.sign(hVelocity) : 0);" in stage_js
    assert 'if (dir < 0) commitStage(d, "next");' in stage_js
    assert 'else if (dir > 0) commitStage(d, "prev");' in stage_js
    assert 'if (event.type === "pointercancel") { poseStage(0); return; }' in stage_js
    assert "dragging = false;        // 竖向: 归下拉收起" in stage_js
    # 1.8.66 遮盖交接: 过场扇形张开后交会处两卡分开, 拖过半翻层 (rise)
    # 藏在缝最大处翻 (z4, 肉眼看不见); 非拖动路径 (renderArtStage/弹回/
    # 交班) live 不传 → rise 撤干净, 层序由 z3/z1 天然接对
    assert "poseStage(sway, true);" in stage_js
    assert 'wrap.classList.toggle("rise-next", !!live && sway <= -0.5);' in stage_js
    assert 'wrap.classList.toggle("rise-prev", !!live && sway >= 0.5);' in stage_js
    assert "#fp-art-wrap.rise-next #fp-art-next," in css
    assert "#fp-art-wrap.rise-prev #fp-art-prev { z-index: 4; }" in css
    # 1.8.67 拖动松手不交班 (用户报「旧的封面会消失一下再出现」): 扇形
    # 张开后松手那拍两卡分在缝两侧, 层序交换落在缝里本来就看不见, 再叠
    # 1.8.65 的溶解反而让旧卡孤零零闪没又闪回; 交班只留程序切歌 (全叠)
    commit_block = stage_js[stage_js.index("function commitStage"):
                            stage_js.index("function initArtStage")]
    assert "stageHandoff" not in commit_block
    assert 'stageHandoff = from > 0 ? "prev" : "next";' in stage_js
    assert 'handoffCard = $(stageHandoff === "prev" ? "#fp-art-prev"' \
           ' : "#fp-art-next");' in stage_js
    assert 'handoffCard.classList.add("handoff");' in stage_js
    assert 'handoffCard.style.opacity = "0";' in stage_js
    assert "handoffTimer = setTimeout(clearHandoff, 420);" in stage_js
    assert "// 交班半路接手: 旧卡复位" in stage_js
    assert 'card.style.opacity = "1";' in stage_js   # 交班旧卡被接走时自愈
    # 事件接线: 封面的下拉收起照旧, 左右划交给舞台; 旧平移切歌退役
    assert 'bindDismissDrag($("#fp-art-wrap"));' in events_js
    assert "initArtStage();" in events_js
    assert "swipeCoverTo" not in fullpage_js and '"side"' not in fullpage_js
    assert "swipeCoverTo" not in events_js
    # 1.8.61 主线程减负: 队列视图没开着不整页重铺 (innerHTML 大重建)
    assert "if (queueViewOpen) renderQueueView();" in queue_js
    assert "if (queueViewOpen) renderQueueView();" in events_js


def test_music_art_cards_are_square():
    """1.8.74 封面恢复正方形 (用户实报「封面不是正方形的」): 1.8.60 3D 舞台
    把卡做成宽八成、高满铺 —— 4:5 竖长方, 方形封面被 object-fit:cover
    裁掉两侧。现在卡高从自身宽出 (aspect-ratio: 1), top:50% + margin-top
    -40% (百分数 margin 按容器宽取值) 垂直居中 —— 横屏 wrap 被 max-height
    压矮时卡照样是方的; 矮屏媒体查询里舞台改高度说了算, wrap 也见方。"""
    css = (MUSIC_STATIC / "css" / "music-player.css").read_text(encoding="utf-8")
    # 几何规则 (position: absolute 那条): 上面的 user-drag 联名规则
    # (#fp-art-wrap, .art-card) 也含 ".art-card {", 按内容定位
    card = css[css.index(".art-card { position: absolute"):]
    card = card[:card.index("}")]
    assert "aspect-ratio: 1;" in card                 # 方形: 高从自身宽出
    assert "top: 50%; margin-top: -40%;" in card      # 垂直居中 (margin 按容器宽)
    assert "width: 80%;" in card                      # 两侧留缝照旧
    assert "height: 100%" not in card                 # 高满铺 = 4:5 长方, 不许回来
    # 横屏 (矮屏): 舞台改高度说了算 (宽满铺会宽过高), 保 wrap 方形
    landscape = css[css.index("@media (max-height: 520px)"):]
    assert "#fp-art-wrap { width: auto; height: 100%; }" in landscape
