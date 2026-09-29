"""1.8 系列的版本条目 · 活跃段 (1.8.96 起, 新的 1.8.x 补丁版加在文件顶上)。
更老的 1.8 线全部冻结分家 (1.8.86–1.8.95 / 1.8.76–1.8.85 / 1.8.67–1.8.75 /
1.8.59–1.8.66 / 1.8.40–1.8.58 / … / 1.8.0–1.8.4 十三个数据文件, 当年一整线
塞一个文件超 200 行硬上限, 分了十二次家)。条目规矩: 用户视角, 一条一句话
(test_music_changelog 有断言把着)。"""
from typing import Final

from ..schemas import ChangelogItem, ChangelogVersion

VERSIONS_1_8: Final[list[ChangelogVersion]] = [
    ChangelogVersion(version="1.8.124", date="2026-09-30", items=[
    ChangelogItem(kind="新增", text="播放计数离线补报: 断网、服务重启或报错"
                                   "窗口里听过的歌不再丢账 —— 先暂存本机, 回网"
                                   "或下次打开按真实播放时刻自动补记, 排行榜从"
                                   "此离线也不缺账。"),
    ChangelogItem(kind="改进", text="听歌上报开始认得出失败了: 以前服务器报错"
                                   "也被当成记成功, 现在这样的也进补报队列"
                                   "回头补记。"),
    ]),
    ChangelogVersion(version="1.8.123", date="2026-09-29", items=[
    ChangelogItem(kind="修复", text="改了播放列表的名字, 收层回到列表页和主"
                                   "页看到的还是旧名字的问题修了 —— 现在改名"
                                   "当场把底下那行和那张卡的名字一起换新, 返"
                                   "回去看到的就是新名。"),
]),
    ChangelogVersion(version="1.8.122", date="2026-09-29", items=[
    ChangelogItem(kind="修复", text="修了已下载标记撒谎 —— 手机浏览器会随"
                                   "机清掉缓存, 清掉的手机上还显示已下载, "
                                   "放的时候才发现要重新走流量; 现在回到应"
                                   "用、翻列表、播放时都实际查一遍缓存里"
                                   "到底有没有, 没有当场摘掉已下载标记。"),
]),
    ChangelogVersion(version="1.8.121", date="2026-09-29", items=[
    ChangelogItem(kind="改进", text="循环键在列表循环和单曲循环之间切换时, "
                                   "循环圈不再挪位了 —— 两态的圈完全重叠, "
                                   "点下去感觉只是多出/少了个「1」的圆片。"),
]),
ChangelogVersion(version="1.8.120", date="2026-09-29", items=[
    ChangelogItem(kind="改进", text="单曲循环的圆片徽章跟循环图标分家"
                                   "了 —— 圆圈周围留出 1px 镂空, 原先"
                                   "顶杆和右杆都贴着圆片长, 看着粘在一"
                                   "起。"),
]),
ChangelogVersion(version="1.8.119", date="2026-09-29", items=[
    ChangelogItem(kind="改进", text="单曲循环「1」的镂空擦干净了 —— 「1」"
                                   "右侧笔画正骑在循环 logo 的杆头上, 透过"
                                   "镂空看得见它, 现在镂空里只剩干净的底"
                                   "色。"),
]),
ChangelogVersion(version="1.8.118", date="2026-09-29", items=[
    ChangelogItem(kind="改进", text="单曲循环徽章挪出环角 —— 圆片往右顶"
                                   "到图标右上角 (照参照 logo 的位), 「1」跟着"
                                   "圆片走。"),
]),
ChangelogVersion(version="1.8.117", date="2026-09-29", items=[
    ChangelogItem(kind="改进", text="单曲循环徽章按用户参照 logo 重定尺寸 —— "
                                   "右上角圆片放大到占图宽近半, 「1」高占圆片"
                                   "一半。"),
]),
ChangelogVersion(version="1.8.116", date="2026-09-29", items=[
    ChangelogItem(kind="改进", text="单曲循环徽章里的「1」放大 (高占圆片四分"
                                   "之三)。"),
]),
ChangelogVersion(version="1.8.115", date="2026-09-29", items=[
    ChangelogItem(kind="改进", text="单曲循环键的「1」徽章从环心挪到 logo 右"
                                   "上角 (圆片盖住折角箭头, 顶杆顺势流入, iOS"
                                   " 角标款)。"),
]),
ChangelogVersion(version="1.8.114", date="2026-09-29", items=[
    ChangelogItem(kind="修复", text="上划收起封面后长专辑名的头一行与艺人名"
                                   "左对齐 (换行的长标题字居中排在标题框"
                                   "里, 原先对的是框不是字, 开头看着空着一"
                                   "小截)。"),
]),
ChangelogVersion(version="1.8.113", date="2026-09-29", items=[
    ChangelogItem(kind="修复", text="上划收起封面时标题和艺人名一开头就左"
                                   "对齐 (原先整个收缩过程两行都还错着一"
                                   "点, 标题看着像前面空了一格)。"),
]),
ChangelogVersion(version="1.8.112", date="2026-09-29", items=[
    ChangelogItem(kind="修复", text="上划收起封面的过程中标题和艺人名一路左"
                                   "对齐 (原先收缩途中两行一直错着, 到顶才"
                                   "对齐)。"),
    ChangelogItem(kind="改进", text="长标题收进顶栏不再缩成小字, 放不下的部"
                                   "分在按钮旁边淡掉。"),
]),
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
]
