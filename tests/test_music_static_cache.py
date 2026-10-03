"""静态缓存头与门厅页禁缩放测试: 带 ?v= 的一年 immutable (?v= 家规配套) +
登录/注册/账号三张门厅页的 no-zoom 接线 (1.8.132 补齐)。"""
from pathlib import Path

_HOME = Path(__file__).parent.parent / "app" / "home" / "static"
_IMMUTABLE = "public, max-age=31536000, immutable"


def test_versioned_static_immutable(client):
    """带 ?v= 的静态资源回一年 immutable (?v= 家规: 内容一变必换号 —
    2026-10-03 手机公网导航提速的主修, 翻页不再逐个重验资产); 不带的
    (manifest/图标这类没法换 URL 的) 照旧 ETag 协商, 改了能及时生效。"""
    for url in ("/music/static/css/changelog-page.css?v=2",
                "/static/no-zoom.js?v=2"):
        versioned = client.get(url)
        assert versioned.status_code == 200, url
        assert versioned.headers["cache-control"] == _IMMUTABLE, url
    for url in ("/music/static/css/changelog-page.css", "/static/no-zoom.js"):
        plain = client.get(url)
        assert plain.status_code == 200, url
        assert "immutable" not in plain.headers.get("cache-control", ""), url


def test_foyer_pages_no_zoom():
    """门厅三页 (登录/注册/账号) 1.8.132 起也掐死放大缩小: meta 掐双击/
    聚焦放大, no-zoom.js 是 body 后第一条脚本 (拦 iOS 捏合的非标准
    gesture 事件), 页 css 的 body 收口 pan-y (Chrome/Android 捏合)。"""
    for name in ("login", "register", "accounts"):
        html = (_HOME / f"{name}.html").read_text(encoding="utf-8")
        assert "maximum-scale=1, user-scalable=no" in html, name
        body_at = html.index("<body")
        assert html.index("<script", body_at + 1) == html.index(
            '<script src="/static/no-zoom.js?v=2"></script>'), name
        css = (_HOME / "css" / f"{name}-page.css").read_text(encoding="utf-8")
        assert "touch-action: pan-y;" in css, name
