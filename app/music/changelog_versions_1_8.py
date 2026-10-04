"""1.8 系列的版本条目 · 活跃段 (1.8.106 起, 新的 1.8.x 补丁版加在文件顶上)。
更老的 1.8 线全部冻结分家 (1.8.96–1.8.105 / 1.8.86–1.8.95 / 1.8.76–1.8.85 /
1.8.67–1.8.75 / 1.8.59–1.8.66 / 1.8.40–1.8.58 / … / 1.8.0–1.8.4 十四个数据文件,
当年一整线塞一个文件超 200 行硬上限, 分了十三次家)。条目规矩: 用户视角, 一条
一句话 (test_music_changelog 有断言把着)。"""
from typing import Final

from ..schemas import ChangelogItem, ChangelogVersion

VERSIONS_1_8: Final[list[ChangelogVersion]] = [
    ChangelogVersion(version="1.8.133", date="2026-10-04", items=[
    ChangelogItem(kind="新增", text="播放页的 ⋯ 菜单多了「调整歌词」—— 弹出"
                                   "的面板盖在歌词页上, 歌照常放着: 搜一下"
                                   "换个词 (网易云/QQ/LRCLIB 三家候选点一下"
                                   "就换上), 词快了慢了还能 ±0.5 秒微调, 点"
                                   "一下当场见效。"),
]),
    ChangelogVersion(version="1.8.132", date="2026-10-03", items=[
    ChangelogItem(kind="修复", text="手机上更新日志页的禁缩放其实没装上 ——"
                                   " 负责的共享脚本此前在服务器上缺席过"
                                   " (地址 404), 浏览器把「不存在」当成了"
                                   " 可长期缓存的结果, 补上文件也不再来取;"
                                   " 换了新版本号的地址后手机重新拿到, 恢复"
                                   " 正常。"),
    ChangelogItem(kind="改进", text="带版本号的页面资源一律许缓存一整年、不再"
                                   " 逐个回服务器核对 —— 手机走公网访问时翻页"
                                   " 快了 (线上服务 9 月底已先行, 这回钉进本仓"
                                   " 和测试, 应用单独跑也齐)。"),
    ChangelogItem(kind="改进", text="登录/注册/账号三张门厅页也补齐了禁缩放 ——"
                                   " 全应用 1.8.6 起就有的防放大唯独这三页"
                                   " 漏了网, 现在跟齐。"),
]),
    ChangelogVersion(version="1.8.131", date="2026-10-02", items=[
    ChangelogItem(kind="改进", text="更新日志页也禁了双击和两指捏合放大 ——"
                                   " 全应用 1.8.6 起就有的禁缩放唯独这页"
                                   " 漏了网, 现在补齐。"),
]),
    ChangelogVersion(version="1.8.130", date="2026-10-01", items=[
    ChangelogItem(kind="改进", text="分享出去的链接, 播放页和应用里的长一样了"
                                   " —— 封面左右滑 3D 切歌、传输键站进度条上"
                                   "方、底排 循环/歌词/队列 三键同款, 封面下"
                                   "的音质行也有, 还能翻开待播队列点歌跳播、"
                                   "滚词时点「回到当前句」。"),
]),
    ChangelogVersion(version="1.8.129", date="2026-09-30", items=[
    ChangelogItem(kind="改进", text="封面下的音质行跟着封面一起 3D 翻面进"
                                   "出 —— 左右滑切歌时三行小字各随各的封面"
                                   "飞, 邻曲的字提前备好, 滑到中间就有。"),
]),
    ChangelogVersion(version="1.8.128", date="2026-09-30", items=[
    ChangelogItem(kind="改进", text="音质参数行挪到封面正下方居中 —— 原先挤"
                                   "在艺人名下面跟左对齐文字混在一起, 现在贴"
                                   "着封面走, 歌词/队列视图里随封面一起退场。"),
]),
    ChangelogVersion(version="1.8.127", date="2026-09-30", items=[
    ChangelogItem(kind="新增", text="播放页封面下多了一行当前歌曲的音质"
                                   "参数 (格式 · 采样率/位深 · 码率, 比如"
                                   " FLAC · 44.1kHz / 16bit · 1049kbps),"
                                   " 音质好坏一眼可辨; 老歌第一次打开时现"
                                   "场读一次文件, 之后都走库存档。"),
]),
    ChangelogVersion(version="1.8.126", date="2026-09-30", items=[
    ChangelogItem(kind="修复", text="修了列表里点歌没反应 —— 手机上点得慢一"
                                   "点 (按住一小会儿再松手) 会被当成想拖动排"
                                   "序, 那一下点击就被吃掉不放歌; 现在只有真"
                                   "的拖动过才不算点歌, 点得再慢也照常开播。"),
    ChangelogItem(kind="修复", text="个别情况长按菜单没能弹出来时, 那一行的点"
                                   "击会一直没反应, 直到点一下别处才恢复 —— "
                                   "一并修了。"),
]),
    ChangelogVersion(version="1.8.125", date="2026-09-30", items=[
    ChangelogItem(kind="修复", text="修了刚更新后点歌没声音 —— 更新窗口里手机"
                                   "拿到了编到一半的旧脚本, 和新脚本撞了名, "
                                   "播放器整个没接上; 已换新地址重新发, 重新"
                                   "打开应用就恢复。"),
]),
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
]
