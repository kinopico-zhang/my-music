"""1.8 系列的版本条目 · 活跃段 (1.8.59 起, 新的 1.8.x 补丁版加在文件顶上)。
更老的 1.8 线全部冻结分家 (1.8.40–1.8.58 / 1.8.33–1.8.39 / … / 1.8.0–1.8.4
九个数据文件, 当年一整线塞一个文件超 200 行硬上限, 分了八次家)。条目规矩:
用户视角, 一条一句话 (test_music_changelog 有断言把着)。"""
from typing import Final

from ..schemas import ChangelogItem, ChangelogVersion

VERSIONS_1_8: Final[list[ChangelogVersion]] = [
    ChangelogVersion(version="1.8.82", date="2026-09-23", items=[
        ChangelogItem(kind="修复", text="部分新加的专辑不显示封面的问题修好"
                                       "了 —— 文件标签里的封面数据写歪时"
                                       "(图前头混着文件名), 现在能自动剥掉"
                                       "只留图, 剥不出图的按没有封面算"),
        ChangelogItem(kind="修复", text="换过音乐文件后手机上专辑封面一直是"
                                       "旧图的问题也修了 —— 封面地址的版本"
                                       "号改成跟文件内容走, 换完文件扫一遍"
                                       "库就能看到新封面"),
    ]),
    ChangelogVersion(version="1.8.81", date="2026-09-23", items=[
        ChangelogItem(kind="改进", text="主页「最近添加专辑」点查看全部进去, "
                                       "专辑按添加时间倒排 (最新在前), 不再按"
                                       "字母排; 菜单「所有专辑」进去照旧"),
    ]),
    ChangelogVersion(version="1.8.80", date="2026-09-23", items=[
        ChangelogItem(kind="修复", text="删除播放列表后回主页, 主页不再"
                                       "还留着它 (列表页左滑删和详情页删"
                                       "两条路都算)"),
    ]),
    ChangelogVersion(version="1.8.79", date="2026-09-23", items=[
        ChangelogItem(kind="修复", text="新建播放列表连点几下不再连环报"
                                       "「没建起来」—— 之前第一下其实已建成, "
                                       "后面几下全是撞名报错把成功的盖成失败"),
    ]),
    ChangelogVersion(version="1.8.78", date="2026-09-23", items=[
        ChangelogItem(kind="修复", text="来电或微信语音打断播放后, 音乐会在"
                                       "打断结束后自动接着播, 锁屏控制也跟着"
                                       "回来, 不用再打开应用点播放"),
    ]),
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
]
