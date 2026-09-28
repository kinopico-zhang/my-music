"""1.8 系列的版本条目 · 活跃段 (1.8.86 起, 新的 1.8.x 补丁版加在文件顶上)。
更老的 1.8 线全部冻结分家 (1.8.76–1.8.85 / 1.8.67–1.8.75 / 1.8.59–1.8.66 /
1.8.40–1.8.58 / 1.8.33–1.8.39 / … / 1.8.0–1.8.4 十二个数据文件, 当年一整线
塞一个文件超 200 行硬上限, 分了十一次家)。条目规矩: 用户视角, 一条一句话
(test_music_changelog 有断言把着)。"""
from typing import Final

from ..schemas import ChangelogItem, ChangelogVersion

VERSIONS_1_8: Final[list[ChangelogVersion]] = [
    ChangelogVersion(version="1.8.111", date="2026-09-28", items=[
        ChangelogItem(kind="改进", text="随机播放和循环键换了实底新图标 —— "
                                       "列表循环/单曲循环/随机三态和随机播"
                                       "放键同一批换装, 单曲循环的「1」徽章"
                                       "收进环心, 切换循环模式时环纹丝不动"),
    ]),
    ChangelogVersion(version="1.8.110", date="2026-09-28", items=[
        ChangelogItem(kind="改进", text="所有删除都加了二次确认 —— 左滑"
                                       "的红色删除按钮点下去会先问一句 (删哪"
                                       "个列表/哪首歌都点名道姓), 确认了才"
                                       "真删, 反悔了按钮自己缩回去"),
    ]),
    ChangelogVersion(version="1.8.109", date="2026-09-28", items=[
        ChangelogItem(kind="修复", text="修了电脑大屏上菜单弹层离菜单键老"
                                       "远 —— 之前钉死在屏幕左下角, 现在从"
                                       "菜单键正上方长出来"),
    ]),
    ChangelogVersion(version="1.8.108", date="2026-09-28", items=[
        ChangelogItem(kind="改进", text="电脑上播放列表的曲目直接按住鼠标拖"
                                       "动就能换顺序 —— 不用再长按等待, 手机"
                                       "触屏上照旧按住一小会儿再拖"),
    ]),
    ChangelogVersion(version="1.8.107", date="2026-09-28", items=[
        ChangelogItem(kind="修复", text="修电脑上来回切换页面后画中画小窗不"
                                       "再出现 —— Chrome 只许刚点过页面时开"
                                       "窗, 收了就弹不回来; 小窗改长驻 (回到"
                                       "播放页不再自动收), 不想要就点它自己"
                                       "的 ✕, 关过这一页就不会再自动弹"),
    ]),
    ChangelogVersion(version="1.8.106", date="2026-09-28", items=[
        ChangelogItem(kind="改进", text="电脑上播放页的音量条两端加了小/大喇"
                                       "叭图标标明这是音量, 条子也缩短到和进"
                                       "度条一样长 (正好落在进度条正下方)"),
        ChangelogItem(kind="改进", text="电脑 Chrome 的画中画小窗改成自动的"
                                       " —— 播放中切去别的窗口小窗自己弹出"
                                       "来, 回到播放页自己收掉, 底排的画中"
                                       "画按钮撤了 (还是三颗键)"),
    ]),
    ChangelogVersion(version="1.8.105", date="2026-09-28", items=[
        ChangelogItem(kind="新增", text="电脑 Chrome 播放页多了画中画键 —— 点开"
                                       "弹一枚总在最前的小窗 (封面/歌名/进度/"
                                       "上下曲/播停), 最小化网页或切去干别的"
                                       "活也能遥控着听; 不支持的浏览器不显示"
                                       "这颗键, 手机触屏端照旧没有"),
    ]),
    ChangelogVersion(version="1.8.104", date="2026-09-28", items=[
        ChangelogItem(kind="改进", text="电脑上播放页的音量条挪到了歌名下方、"
                                       "播放按钮上方, 加长到和进度条一样长 —— "
                                       "原先挤在底部一排的角落里, 太短不好拖"),
        ChangelogItem(kind="改进", text="电脑上鼠标扫过播放列表不再每一行都弹"
                                       "出红色删除按钮了 —— 现在在歌曲上停住"
                                       "半秒才会出现, 一扫而过只亮行背景"),
    ]),
    ChangelogVersion(version="1.8.103", date="2026-09-28", items=[
        ChangelogItem(kind="新增", text="电脑上底部多了一颗音量键 —— 点开在键"
                                       "上方弹出小气泡, 拖滑杆直接调音量, 与播"
                                       "放页音量条和上下方向键三处同源, 手机上"
                                       "不出现 (音量归系统硬件键)"),
        ChangelogItem(kind="改进", text="电脑等大屏上内容不再挤在手机宽度里 —— "
                                       "版面随屏幕加宽, 专辑格更大更饱满"),
        ChangelogItem(kind="改进", text="页面改为按「屏幕大小」和「键鼠/触摸」"
                                       "两条线分开适配 —— 电脑上列表行距收紧一"
                                       "屏多放几行, 之后给电脑加的键鼠优化都不"
                                       "会再波及手机触屏体验"),
    ]),
    ChangelogVersion(version="1.8.102", date="2026-09-28", items=[
        ChangelogItem(kind="修复", text="电脑上打开补齐了键鼠手感 —— 之前点"
                                       "过一次按钮后空格和方向键就全没反应了, "
                                       "现在左右方向键直接快退快进 10 秒, "
                                       "上下调音量 (播放页也加了音量条), 切歌"
                                       "用 Shift 加左右方向键, 音量记住上次"
                                       "调好的"),
    ]),
    ChangelogVersion(version="1.8.101", date="2026-09-28", items=[
        ChangelogItem(kind="修复", text="手机系统悄悄清掉的缓存不再被当成还"
                                       "在 —— 之前索引记着「都缓存好了」, "
                                       "放到那首才发现字节没了、整首重新走"
                                       "流量, 现在回到应用就当场对账出清, "
                                       "并申请把存储固定住不被系统清理, 手"
                                       "机存储吃紧时缓存上限也跟着收紧"),
    ]),
    ChangelogVersion(version="1.8.100", date="2026-09-27", items=[
        ChangelogItem(kind="修复", text="后台连播第二首开始没声音、锁屏进度"
                                       "却还在走, 过一阵锁屏连播放卡片都没"
                                       "了的问题修了 —— 现在趁上一首还响着"
                                       "就把下一首接上, 手机系统冻不住页面"),
    ]),
    ChangelogVersion(version="1.8.99", date="2026-09-27", items=[
        ChangelogItem(kind="修复", text="换了播放列表封面后, 回到所有播放"
                                       "列表页和主页看到的还是旧图的问题修了"
                                       " —— 现在设完封面, 底下的列表当场"
                                       "换上新图, 撤掉封面也一样"),
    ]),
    ChangelogVersion(version="1.8.98", date="2026-09-26", items=[
        ChangelogItem(kind="修复", text="服务器修过的歌手机也认账了 —— 之前音频"
                                       "文件在服务器换新, 手机自动缓存里的旧字节"
                                       "还压着不放, 现在缓存换代自动清旧重新拉"),
    ]),
    ChangelogVersion(version="1.8.97", date="2026-09-25", items=[
        ChangelogItem(kind="改进", text="播放页封面轻轻一划也能切歌了 —— 之前"
                                       "要划过小半张封面或甩得够快才切, 滑得短"
                                       "了会被当成没划够放回原位"),
    ]),
    ChangelogVersion(version="1.8.96", date="2026-09-25", items=[
        ChangelogItem(kind="修复", text="修了播放气泡还没滑动就露出下一首封面"
                                       "窄条的问题"),
        ChangelogItem(kind="改进", text="气泡左右滑只管切歌了 —— 第一首往右划、"
                                       "最后一首往左划是拖不动的橡皮筋, 不会再把"
                                       "底下的页面划走退出去"),
        ChangelogItem(kind="改进", text="网络不好歌加载不出来时不再自动跳过这首"
                                       "了 —— 会自己试着把这首加载出来, 想跳过"
                                       "自己划或自己点"),
    ]),
    ChangelogVersion(version="1.8.95", date="2026-09-25", items=[
        ChangelogItem(kind="修复", text="修了滑动气泡切歌时封面不跟着换的问题 —— "
                                       "现在手指拖到哪, 相邻那首的封面歌名就跟着"
                                       "从两侧滑进来提前看到, 松手顺势滑满一整张"
                                       "换曲, 新封面无缝接上"),
    ]),
    ChangelogVersion(version="1.8.94", date="2026-09-25", items=[
        ChangelogItem(kind="改进", text="播放气泡的上一首/下一首键撤了, 换成左右"
                                       "滑动气泡切歌 —— 封面和歌名跟着手指走, "
                                       "松手顺势滑出、新歌从另一侧滑进来"),
    ]),
    ChangelogVersion(version="1.8.93", date="2026-09-25", items=[
        ChangelogItem(kind="改进", text="播放气泡的上一首/下一首图标裁成单个"
                                       "三角形, 三颗按键也收得更紧凑"),
    ]),
    ChangelogVersion(version="1.8.92", date="2026-09-25", items=[
        ChangelogItem(kind="改进", text="单曲循环图标里的 \"1\" 缩小了一号, "
                                       "环里留白回来不再发胀"),
        ChangelogItem(kind="改进", text="播放页的气泡提示挪到封面和标题之间, "
                                       "不再盖住歌名"),
    ]),
    ChangelogVersion(version="1.8.91", date="2026-09-25", items=[
        ChangelogItem(kind="改进", text="循环模式键的图标缩小一号跟旁边的按键"
                                       "看齐, 线条交叉处不再叠出深色斑点"),
        ChangelogItem(kind="改进", text="循环模式的气泡提示挪到标题行上, "
                                       "整屏居中, 不再压着底部的播放按键"),
    ]),
    ChangelogVersion(version="1.8.90", date="2026-09-25", items=[
        ChangelogItem(kind="改进", text="循环模式键的三态图标线条加粗 —— "
                                       "列表/单曲/随机都换成粗描边画法, "
                                       "和旁边按键看着一样有分量"),
    ]),
    ChangelogVersion(version="1.8.89", date="2026-09-25", items=[
        ChangelogItem(kind="改进", text="播放页底行的加列表键换成循环模式键 —— "
                                       "点一下在列表循环、单曲循环、随机循环间"
                                       "轮换并气泡报当前模式, 加列表还在 ⋯ 菜单"
                                       "里, 待播放列表头的两枚循环键撤了"),
    ]),
    ChangelogVersion(version="1.8.88", date="2026-09-25", items=[
        ChangelogItem(kind="改进", text="播放气泡加回上一首/下一首键 —— "
                                       "路上想切歌不用进全屏页, 点封面文字"
                                       "照旧进全屏页"),
    ]),
    ChangelogVersion(version="1.8.87", date="2026-09-24", items=[
        ChangelogItem(kind="修复", text="开车路上信号断续时连播不再停摆 —— "
                                       "断网挂起的歌就地等信号, 一回到应用"
                                       "就自动接着放, 不跳歌"),
        ChangelogItem(kind="修复", text="缓存到本地的歌也偶发卡在暂停态 —— "
                                       "换用本地缓存源的一瞬把正在起播的请"
                                       "求掐断了, 换完没人再把播放下达回来, "
                                       "现在换完源自己接着放"),
        ChangelogItem(kind="改进", text="连跳 3 首停住只对歌本身坏 (解码不"
                                       "了) 生效 —— 网络断的问题不再跳歌计数"),
    ]),
    ChangelogVersion(version="1.8.86", date="2026-09-24", items=[
        ChangelogItem(kind="修复", text="看长视频回来后, 播放器卡在「看着"
                                       "在播其实没声」的假播放状态 —— 现在"
                                       "一回到应用就会自动纠正, 点一下播放"
                                       "键就从原位置接着听"),
        ChangelogItem(kind="改进", text="看过长视频后控制中心的按钮可能叫"
                                       "不动播放器 —— 那时应用已被系统冻"
                                       "结 (网页应用的限制), 先回到应用点一"
                                       "下就好; 短暂打断不受影响"),
    ]),
]
