"""My Music 全页截图射手: 8 个视图各一张, iPhone 视口 (内容区 393x764) dsf=2。

用法: /tmp/pw-verify/bin/python shots/shoot.py [名字过滤词]
依赖: 真实数据实例已起 (shots/real_server.py, 默认 127.0.0.1:8906)。
环境: SHOT_BASE 服务地址 (默认 http://127.0.0.1:8906)
      SHOT_PAGES 原图输出目录 (默认 ~/shotlab/pages)
      SHOTLAB 工作目录 (默认 ~/shotlab; 账号副本在 $SHOTLAB/music-real/)
      SHOT_ALBUM_ID 专辑页/播放器用的专辑 (默认 250 = 孙燕姿《风筝》,
      封面 + 全碟逐行歌词; 播放器放它的同名曲第 2 首)
口径与 my-tesla shots/shoot.py 同源: 视口 764 (底部 34px iOS 安全区由
合成补齐); 开场/推入动画等收完 (settle 等动画清零, 循环动画超时放行);
每视图独立 context, localStorage 清掉 music.lastRoute (开局回跳会跟
射手抢导航)。
会话: 最近播放/播放排行按账号记, 用真实账号的 uuid 签 cookie
(与 /api/login 同配方: exp.uuid.HMAC, 密钥 = 账号副本那份
.session_secret 的 sha256) —— 收听史是真实数据, 不是射手账号的空榜。
导航走页面自己的 navigate() 全局函数 (应用内路由, 地址栏全程不动),
不点菜单按钮 —— 与真实用户路径等价但不依赖弹层几何。
"""
import asyncio
import hashlib
import hmac
import os
import pathlib
import sqlite3
import sys
import time

os.environ.setdefault(
    "LD_LIBRARY_PATH", "/home/admin/pwlibs/extracted/usr/lib/x86_64-linux-gnu")
from playwright.async_api import async_playwright  # noqa: E402

BASE = os.environ.get("SHOT_BASE", "http://127.0.0.1:8906")
OUT = os.environ.get("SHOT_PAGES",
                     os.path.expanduser("~/shotlab/pages"))
ALBUM_ID = os.environ.get("SHOT_ALBUM_ID", "250")
os.makedirs(OUT, exist_ok=True)

VIEWPORT = {"width": 393, "height": 764}   # 852-54 状态栏-34 底部安全区
UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) "
      "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 "
      "Safari/604.1")

# 播放器放的歌: 专辑第 2 首《风筝》(4399), 副歌一句「我也知道 天空多美妙」
# 从 01:40 (100.11s) 唱起 —— 高亮行钉在这句: 它是全曲记忆点, 也呼应专辑名。
# seek 101 留出余量, wait 直接等这句亮起 (时序漂移不会滑到下一句去)。
PLAYER_TRACK_ID = "4399"
PLAYER_SEEK_SECONDS = 101
PLAYER_LINE = "天空多美妙"

# 专辑页曲目就绪锚点 (album 与 player 两处共用)
ALBUM_READY = ("document.querySelectorAll('.push-pane[data-view=album] "
               "#album-tracks .track-row').length >= 10"
               " && document.querySelector('.push-pane[data-view=album] "
               ".hero-txt h2') !== null")


LAB = pathlib.Path(os.environ.get("SHOTLAB",
                     os.path.expanduser("~/shotlab")))
WORK = LAB / "music-real"


def real_user_token() -> str:
    """真实管理员的会话 cookie 值 (app/authentication.make_token 同配方)。"""
    secret = hashlib.sha256(
        (WORK / "secret").read_bytes().strip()).digest()
    db = sqlite3.connect(WORK / "users.db")
    user_uuid = db.execute(
        "SELECT uuid FROM users WHERE is_admin LIMIT 1").fetchone()[0]
    db.close()
    exp = str(int(time.time()) + 7 * 86400)
    payload = f"{exp}.{user_uuid}"
    sig = hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


TOKEN = real_user_token()


async def ctx_new(browser):
    """独立 context; lastRoute 清档, 开局固定落主页 (不回跳上次的页)。"""
    ctx = await browser.new_context(
        viewport=VIEWPORT, device_scale_factor=2, is_mobile=True,
        has_touch=True, user_agent=UA, locale="zh-CN",
        timezone_id="Asia/Shanghai")
    await ctx.add_init_script(
        "try{localStorage.removeItem('music.lastRoute')}catch(e){}")
    await ctx.add_cookies([{"name": "auth", "value": TOKEN, "url": BASE}])
    return ctx


async def settle(page, ms=1200):
    """开场/推入动画收尾: 等动画清零 (一次性 transition 完成即自摘),
    循环动画 (转圈/呼吸/流体形变) 等不到就 4s 超时放行, 再加固定缓冲。"""
    try:
        await page.wait_for_function(
            "() => document.getAnimations().length === 0", timeout=4000)
    except Exception:                                  # noqa: BLE001
        pass                                           # 循环动画常驻, 尽力而为
    await page.wait_for_timeout(ms)


async def images_settled(page):
    """视口内的图片都真实解码完 (lazy 的未进视口不算数)。"""
    try:
        await page.wait_for_function("""() => {
          const vw = window.innerWidth, vh = window.innerHeight;
          return [...document.images].every(img => {
            const r = img.getBoundingClientRect();
            if (r.bottom < 0 || r.top > vh || r.right < 0 || r.left > vw)
              return true;                 // 不在视口, 管不着
            return img.complete && img.naturalWidth > 0;
          });
        }""", timeout=10000)
    except Exception:                                  # noqa: BLE001
        pass                                           # 个别封面拉不动不拦截图


async def open_app(browser):
    """带真实账号会话冷启 → 等主页三段都铺上真实数据 (不是骨架)。"""
    page = await (await ctx_new(browser)).new_page()
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    await page.goto(BASE + "/music", wait_until="domcontentloaded")
    await page.wait_for_function("""() =>
      document.querySelectorAll('#home-playlists [data-playlist-id]').length > 0
      && document.querySelectorAll('#home-recent [data-track-row]').length > 0
      && document.querySelectorAll('#home-albums [data-album-id]').length > 0""",
        timeout=30000)
    return page, errors


async def shoot_pane(browser, name, route, ready_js, last_ms=1200):
    """通用推入层射手: 冷启主页 → navigate() 推层 → 等数据锚点 → settle。"""
    page, errors = await open_app(browser)
    await page.evaluate(f"navigate('{route}')")
    await page.wait_for_function(ready_js, timeout=30000)
    await settle(page, last_ms)
    await images_settled(page)
    await page.screenshot(path=f"{OUT}/music-{name}.png")
    if errors:
        print(f"  [{name}] console errors: {errors[:5]}", flush=True)
    print(f"  music-{name} done", flush=True)


# 各视图数据就绪锚点 (等真实数据渲染完, 不是骨架出现):
#   home       主页三段 (最近播放列表 / 最近播放音乐 / 最近添加专辑) 都有卡
#   albums     所有专辑首批卡落 DOM
#   artists    所有艺人首批行落 DOM
#   album      专辑页 hero 标题就位 + 全碟曲目行
#   playlists  播放列表首批行落 DOM
#   top        排行三档页签 + 首档曲目行 (真实播放计数)
#   stats      统计四卡有值 + 格式行落 DOM
READY = {
    "albums": ("document.querySelectorAll("
               "'.push-pane[data-view=albums] .album-card').length > 0"),
    "artists": ("document.querySelectorAll("
                "'.push-pane[data-view=artists] .artist-row').length > 0"),
    "playlists": ("document.querySelectorAll('.push-pane[data-view=playlists]"
                  " [data-playlist-id]').length > 0"),
    "top": ("document.querySelectorAll('#top-tabs button').length === 3"
            " && document.querySelectorAll("
            "'.push-pane[data-view=top] .track-row').length > 0"),
    "stats": ("document.querySelectorAll("
              "'.push-pane[data-view=stats] .stat-card b').length === 4"
              " && document.querySelectorAll("
              "'.push-pane[data-view=stats] .format-row').length > 0"),
}


async def music_home(browser):
    page, errors = await open_app(browser)
    await settle(page, 1200)
    await images_settled(page)
    await page.screenshot(path=f"{OUT}/music-home.png")
    if errors:
        print(f"  [home] console errors: {errors[:5]}", flush=True)
    print("  music-home done", flush=True)


async def music_album(browser):
    """专辑页 (默认孙燕姿《风筝》): hero 封面 + 全碟曲目。"""
    page, errors = await open_app(browser)
    await page.evaluate(f"navigate('album/{ALBUM_ID}')")
    await page.wait_for_function(ALBUM_READY, timeout=30000)
    await settle(page, 1500)
    await images_settled(page)
    await page.screenshot(path=f"{OUT}/music-album.png")
    if errors:
        print(f"  [album] console errors: {errors[:5]}", flush=True)
    print("  music-album done", flush=True)


async def music_player(browser):
    """播放器 + 歌词: 专辑页点同名曲 → 迷你条 → 拉开全屏 → 开歌词,
    跳到副歌一句等高亮落定 —— 逐行跟唱是这一页的卖点, 高亮行必须真亮。"""
    page, errors = await open_app(browser)
    await page.evaluate(f"navigate('album/{ALBUM_ID}')")
    await page.wait_for_function(ALBUM_READY, timeout=30000)
    await settle(page, 800)
    print("    [player] tracks ready", flush=True)
    await page.click(f".push-pane[data-view=album] "
                     f"[data-track-id='{PLAYER_TRACK_ID}']")
    await page.wait_for_selector("#mini-player:not([hidden])", timeout=15000)
    print("    [player] mini visible", flush=True)
    await page.click("#mini-open")
    await page.wait_for_selector("#full-player.open", timeout=15000)
    await page.wait_for_selector("#fp-lyrics-btn:not([disabled])",
                                 timeout=15000)
    print("    [player] full open", flush=True)
    # 封面/标题就位再动进度 (加载中 seek 会被换源吞掉); audioElement 是
    # 取元素的函数 (全局), 真元素上 seek
    await page.wait_for_function(
        "document.querySelector('#fp-title').textContent.trim() !== ''",
        timeout=15000)
    await page.evaluate(
        f"audioElement().currentTime = {PLAYER_SEEK_SECONDS}")
    await page.click("#fp-lyrics-btn")
    await page.wait_for_selector(".lyrics-line", timeout=15000)
    await page.wait_for_function(
        """() => { const act = document.querySelector('.lyrics-line.active');
          return act && act.textContent.includes('""" + PLAYER_LINE + """'); }""",
        timeout=15000)
    await settle(page, 2000)      # 歌词滚动落位 + 高亮行停稳
    await images_settled(page)
    await page.screenshot(path=f"{OUT}/music-player.png")
    cur = await page.locator("#fp-time-cur").text_content()
    act = await page.locator(".lyrics-line.active").text_content()
    print(f"  music-player done (pos={cur!r} active={act!r})", flush=True)
    if errors:
        print(f"  [player] console errors: {errors[:5]}", flush=True)


async def main():
    only = sys.argv[1] if len(sys.argv) > 1 else ""
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            args=["--autoplay-policy=no-user-gesture-required"])
        for name, fn in (("home", music_home), ("album", music_album),
                         ("player", music_player)):
            if only and only not in name:
                continue
            print(f"shooting music-{name}...", flush=True)
            try:
                await fn(browser)
            except Exception as exc:                   # noqa: BLE001
                import traceback
                print(f"  !! music-{name} FAILED: {exc}", flush=True)
                traceback.print_exc()
        for name, ready_js in READY.items():
            if only and only not in name:
                continue
            print(f"shooting music-{name}...", flush=True)
            try:
                await shoot_pane(browser, name, name, ready_js)
            except Exception as exc:                   # noqa: BLE001
                print(f"  !! music-{name} FAILED: {exc}", flush=True)
        await browser.close()
    print("ALL DONE", flush=True)


asyncio.run(main())
