"""1.8 系列的版本条目 · 活跃段 (1.8.40 起, 新的 1.8.x 补丁版加在文件顶上)。
更老的 1.8 线全部冻结分家 (1.8.33–1.8.39 / … / 1.8.0–1.8.4 八个数据文件,
当年一整线塞一个文件超 200 行硬上限, 分了七次家)。条目规矩: 用户视角,
一条一句话 (test_music_changelog 有断言把着)。"""
from typing import Final

from ..schemas import ChangelogItem, ChangelogVersion

VERSIONS_1_8: Final[list[ChangelogVersion]] = [
    ChangelogVersion(version="1.8.77", date="2026-09-23", items=[
        ChangelogItem(kind="新增", text="播放时自动把下一曲缓存到手机 "
                                       "(上限 2GB, 满了自动清最久没听的), "
                                       "切歌几乎不等加载"),
        ChangelogItem(kind="改进", text="已下载页统计行能看到自动缓存占用"
                                       "了多少, 和手动下载分栏算"),
    ]),
    ChangelogVersion(version="1.8.76", date="2026-09-23", items=[
        ChangelogItem(kind="修复", text="锁屏和后台连播更稳: 切歌不再多等"
                                       "一步读缓存, 音频源当场落定"),
        ChangelogItem(kind="修复", text="歌单里夹着手机播不了的格式 "
                                       "(如 tak/dsf/ape) 时自动跳过接着播, "
                                       "不再连播到那就停住"),
        ChangelogItem(kind="修复", text="在线流播挂了不再停在半路: 先试本地"
                                       "缓存救回原位置接着放, 不行自动续下"
                                       "一首, 连挂三首才停"),
    ]),
    ChangelogVersion(version="1.8.75", date="2026-09-23", items=[
        ChangelogItem(kind="新增", text="艺人主页加了「刷新元数据」按钮, "
                                       "点一下按盘上现在的标签和海报重读这位"
                                       "艺人的全部信息 —— 换过的头像点完就能"
                                       "看到新图, 不用再等整库重扫"),
    ]),
    ChangelogVersion(version="1.8.74", date="2026-09-22", items=[
        ChangelogItem(kind="修复", text="播放页拖完进度条, 剩余时间和进度条"
                                       "不再提前归零, 会一直跟到歌真正播完"),
        ChangelogItem(kind="修复", text="播放页封面恢复正方形, 不再是被裁"
                                       "掉两边的竖长条"),
    ]),
    ChangelogVersion(version="1.8.73", date="2026-09-22", items=[
        ChangelogItem(kind="修复", text="在线歌曲放不出来或响几秒就断的问题"
                                       "修好了, 下载过的歌不受影响"),
    ]),
    ChangelogVersion(version="1.8.72", date="2026-09-22", items=[
        ChangelogItem(kind="改进", text="播放页封面下面那行作词署名撤掉了, "
                                       "看着更清爽"),
    ]),
    ChangelogVersion(version="1.8.71", date="2026-09-22", items=[
        ChangelogItem(kind="修复", text="被来电或别的应用声音打断后, 锁屏点"
                                       "播放键能接着播了"),
    ]),
    ChangelogVersion(version="1.8.70", date="2026-09-22", items=[
        ChangelogItem(kind="修复", text="重启应用后直接点气泡播放, 锁屏上"
                                       "也有上一首/下一首了"),
    ]),
    ChangelogVersion(version="1.8.69", date="2026-09-22", items=[
        ChangelogItem(kind="修复", text="iOS 锁屏按键换成上一首/下一首和暂停, "
                                       "不再是 10 秒快退快进"),
    ]),
    ChangelogVersion(version="1.8.68", date="2026-09-22", items=[
        ChangelogItem(kind="修复", text="点播放不再误弹「被浏览器拦了」,"
                                       "歌还在缓冲时连点播放键也不会互相掐断"),
    ]),
    ChangelogVersion(version="1.8.67", date="2026-09-22", items=[
        ChangelogItem(kind="修复", text="滑动封面切歌时旧封面不再闪一下"
                                       "消失再出现"),
    ]),
    ChangelogVersion(version="1.8.66", date="2026-09-22", items=[
        ChangelogItem(kind="修复", text="切歌不再改变播放状态, 本来暂停的"
                                       "保持暂停, 自然播完的连播照旧"),
        ChangelogItem(kind="改进", text="左右划封面时两侧封面过场张得更开, "
                                       "滚动中不再叠在一起"),
    ]),
    ChangelogVersion(version="1.8.65", date="2026-09-22", items=[
        ChangelogItem(kind="修复", text="左右划封面时后侧封面不再突然跳到前面"
                                       "盖过当前封面, 遮盖交接改成平滑的溶解过渡"),
    ]),
    ChangelogVersion(version="1.8.64", date="2026-09-22", items=[
        ChangelogItem(kind="改进", text="播放气泡展开成播放页的水滴动画放慢"
                                       "了, 封面和控件分层一排排浮现"),
    ]),
    ChangelogVersion(version="1.8.63", date="2026-09-22", items=[
        ChangelogItem(kind="改进", text="点播放气泡打开播放页, 面板像水滴"
                                       "一样从气泡原位平滑延展成整页, 不再"
                                       "生硬弹窗"),
    ]),
    ChangelogVersion(version="1.8.62", date="2026-09-22", items=[
        ChangelogItem(kind="修复", text="封面 3D 切歌时两张封面互相穿过去"
                                       "的问题修好了"),
    ]),
    ChangelogVersion(version="1.8.61", date="2026-09-22", items=[
        ChangelogItem(kind="修复", text="封面 3D 切歌的卡顿修好了, 换曲"
                                       "落定改走系统合成, 主线程再忙也不掉帧"),
    ]),
    ChangelogVersion(version="1.8.60", date="2026-09-21", items=[
        ChangelogItem(kind="新增", text="播放页封面换成 3D 舞台, 上一首下一首"
                                       "斜插在两侧, 左右划跟手转面切歌"),
    ]),
    ChangelogVersion(version="1.8.59", date="2026-09-21", items=[
        ChangelogItem(kind="修复", text="锁屏听歌播着播着自己停的问题修好了"),
    ]),
    ChangelogVersion(version="1.8.58", date="2026-09-21", items=[
        ChangelogItem(kind="修复", text="继续播放列表里正在播的那首, 封面"
                                       "上的跳动动画终于亮出来了"),
    ]),
    ChangelogVersion(version="1.8.57", date="2026-09-21", items=[
        ChangelogItem(kind="新增", text="设置里能改自己的账号名和密码了"),
        ChangelogItem(kind="改进", text="联网补歌词能挑厂商了, 自动会按网"
                                       "易云、QQ、LRCLIB 依次试"),
        ChangelogItem(kind="改进", text="普通账号的设置页不再显示曲库和歌词"
                                       "那些管理员配置"),
    ]),
    ChangelogVersion(version="1.8.56", date="2026-09-21", items=[
        ChangelogItem(kind="改进", text="收进顶栏的换行标题不再缩成小字, 放"
                                       "不下的尾字自动淡出"),
    ]),
    ChangelogVersion(version="1.8.55", date="2026-09-21", items=[
        ChangelogItem(kind="改进", text="标题太长换行的专辑/播放列表, 收进顶"
                                       "栏后只留第一行"),
    ]),
    ChangelogVersion(version="1.8.54", date="2026-09-21", items=[
        ChangelogItem(kind="改进", text="排行榜每行左边带上歌曲封面了"),
    ]),
    ChangelogVersion(version="1.8.53", date="2026-09-21", items=[
        ChangelogItem(kind="修复", text="打开播放页偶尔在封面页上见到「回到当"
                                       "前句」的问题修好了"),
    ]),
    ChangelogVersion(version="1.8.52", date="2026-09-21", items=[
        ChangelogItem(kind="改进", text="按压的 Q 弹只留列表页的操作键和收起后"
                                       "的顶栏键"),
    ]),
    ChangelogVersion(version="1.8.51", date="2026-09-21", items=[
        ChangelogItem(kind="修复", text="收拢顶栏的播放键按下时不再闪一下了"),
    ]),
    ChangelogVersion(version="1.8.50", date="2026-09-21", items=[
        ChangelogItem(kind="改进", text="「下载全部」进行中会变成取消键, 点一"
                                       "下整批停止, 已下好的保留"),
    ]),
    ChangelogVersion(version="1.8.49", date="2026-09-21", items=[
        ChangelogItem(kind="修复", text="按播放键时毛玻璃界面不再跟着闪一下了"),
    ]),
    ChangelogVersion(version="1.8.48", date="2026-09-21", items=[
        ChangelogItem(kind="改进", text="按钮按下有了轻轻压扁再弹回的 Q 弹反馈"),
    ]),
    ChangelogVersion(version="1.8.47", date="2026-09-21", items=[
        ChangelogItem(kind="修复", text="分享到微信等系统分享面板时, 顶上能看"
                                       "到封面了"),
    ]),
    ChangelogVersion(version="1.8.46", date="2026-09-21", items=[
        ChangelogItem(kind="修复", text="收进顶栏的按钮飞行时不再两两叠在一起"),
        ChangelogItem(kind="改进", text="点开 … 出来的那排键间距排匀了"),
        ChangelogItem(kind="改进", text="按钮飞进顶栏的动画顺滑不再掉帧"),
        ChangelogItem(kind="改进", text="点开 … 时没被按钮压到的标题不再被误"
                                       "淡化"),
        ChangelogItem(kind="修复", text="列表滑动的余势里点收拢顶栏的 播放/… "
                                       "立即有响应了"),
    ]),
    ChangelogVersion(version="1.8.45", date="2026-09-20", items=[
        ChangelogItem(kind="改进", text="收缩顶栏改成单行, 播放和 … 两颗键上到"
                                       "封面同一行"),
    ]),
    ChangelogVersion(version="1.8.44", date="2026-09-20", items=[
        ChangelogItem(kind="改进", text="试着修蓝牙车机上不显示封面 (效果要上"
                                       "车才知道)"),
    ]),
    ChangelogVersion(version="1.8.43", date="2026-09-20", items=[
        ChangelogItem(kind="改进", text="出问题时不再弹红框提示, 修复照旧自动"
                                       "完成"),
    ]),
    ChangelogVersion(version="1.8.42", date="2026-09-20", items=[
        ChangelogItem(kind="改进", text="顶栏收缩后标题和副标题改成左对齐"),
    ]),
    ChangelogVersion(version="1.8.41", date="2026-09-20", items=[
        ChangelogItem(kind="修复", text="双指捏合再也不能放大整个应用了"),
        ChangelogItem(kind="改进", text="分享页的歌单列表行换上歌曲封面, 和应"
                                       "用里同款"),
    ]),
    ChangelogVersion(version="1.8.40", date="2026-09-20", items=[
        ChangelogItem(kind="修复", text="往上划页面时整层不再左右晃"),
        ChangelogItem(kind="改进", text="收缩顶栏改成两行, 文字和按键分上下排"
                                       "开"),
        ChangelogItem(kind="修复", text="列表特别短的页, 上划的收拢动画不再中"
                                       "途停住"),
    ]),
]
