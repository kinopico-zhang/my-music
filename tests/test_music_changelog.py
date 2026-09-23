"""My Music 更新日志测试: 独立版本线 (2026-09-14 从 My Tesla 的日志拆出) +
条目接口 + 页面骨架 + 主页入口。渲染器与 My Tesla 共用 /static/changelog-page.js。
"""
from app.music import changelog


# ---------------------------------------------------------------- 数据
def test_versions_wellformed():
    """独立版本线从 1.0.0 起; 每版字段齐全, 文案是用户视角的一句话。"""
    vs = changelog.entries()
    assert [v.version for v in vs] == ["1.8.81", "1.8.80",
                                       "1.8.79", "1.8.78",
                                       "1.8.77", "1.8.76", "1.8.75", "1.8.74",
                                       "1.8.73", "1.8.72",
                                       "1.8.71", "1.8.70", "1.8.69",
                                       "1.8.68", "1.8.67", "1.8.66",
                                       "1.8.65", "1.8.64", "1.8.63",
                                       "1.8.62",
                                       "1.8.61",
                                       "1.8.60", "1.8.59", "1.8.58",
                                       "1.8.57",
                                       "1.8.56",
                                       "1.8.55",
                                       "1.8.54",
                                       "1.8.53", "1.8.52", "1.8.51", "1.8.50",
                                       "1.8.49",
                                       "1.8.48", "1.8.47", "1.8.46", "1.8.45", "1.8.44",
                                       "1.8.43", "1.8.42", "1.8.41", "1.8.40", "1.8.39",
                                       "1.8.38", "1.8.37", "1.8.36", "1.8.35",
                                       "1.8.34",
                                       "1.8.33", "1.8.32", "1.8.31", "1.8.30",
                                       "1.8.29",
                                       "1.8.28", "1.8.27", "1.8.26", "1.8.25",
                                       "1.8.24",
                                       "1.8.23", "1.8.22", "1.8.21", "1.8.20",
                                       "1.8.19",
                                       "1.8.18",
                                       "1.8.17", "1.8.16", "1.8.15", "1.8.14",
                                       "1.8.13", "1.8.12", "1.8.11", "1.8.10",
                                       "1.8.9", "1.8.8",
                                       "1.8.7", "1.8.6", "1.8.5", "1.8.4",
                                       "1.8.3", "1.8.2", "1.8.1", "1.8.0",
                                       "1.7.2", "1.7.1", "1.7.0", "1.6.0",
                                       "1.5.1", "1.5.0", "1.4.1", "1.4.0",
                                       "1.3.0", "1.2.1", "1.2.0", "1.1.0",
                                       "1.0.0"]
    assert vs[0].date == "2026-09-23"
    kinds = {it.kind for it in vs[0].items}
    assert kinds <= {"新增", "改进", "修复"}   # 合并批次 (单功能批次不硬凑别的类)
    for v in vs:
        assert v.items
        assert len(v.date) == 10 and v.date[4] == "-"
        for it in v.items:
            assert it.kind in ("新增", "改进", "修复")
            assert len(it.text) >= 4
            # 2026-09-21 用户定的规矩: 一条一句话 —— 全文至多一个句号且必须收尾
            assert it.text.count("。") <= 1
            assert it.text.endswith("。") or "。" not in it.text
            assert "api/" not in it.text and "http" not in it.text
    # 头条是主打 (新功能或修的主 bug); 纯改口/调措辞的版本条条都是改进, 不硬凑
    assert vs[0].items[0].kind in ("新增", "修复") \
        or {it.kind for it in vs[0].items} == {"改进"}
    assert "My Tesla" not in " ".join(it.text for v in vs for it in v.items)


# ---------------------------------------------------------------- 接口
def test_music_changelog_entries_endpoint(auth):
    """条目接口原样吐数据 (新→老), 字段形状与共用渲染器对齐。"""
    es = auth.get("/music/changelog/api/entries").json()
    assert [e["version"] for e in es] == [v.version for v in changelog.entries()]
    for e, v in zip(es, changelog.entries()):
        assert e["date"] == v.date
        assert e["items"] == [{"kind": it.kind, "text": it.text}
                              for it in v.items]
    # 头条是主打 (同上: 纯改口的版本整版都是改进)
    assert es[0]["items"][0]["kind"] in ("新增", "修复") \
        or {i["kind"] for i in es[0]["items"]} == {"改进"}


# ---------------------------------------------------------------- 页面
def test_music_changelog_page_skeleton(auth):
    """更新日志页: 与 My Tesla 同一套骨架, 数据源/资源换成听歌应用自己的。"""
    html = auth.get("/music/changelog").text
    html += auth.get("/static/changelog-page.js?v=1").text
    for frag in [
        "<title>更新日志 · My Music</title>",
        '<a href="/music/">听歌</a>',                            # 回主页
        '<a class="on" href="/music/changelog">更新日志</a>',   # 菜单 (自身亮)
        'id="brand-menu"', 'id="logout"',
        'id="entries"', 'id="list"', 'id="loading"', 'id="error"', 'id="retry"',
        'data-changelog-api="/music/changelog/api/entries"',   # 数据源 (body)
        'href="/music/static/manifest.json"',                  # 独立 PWA 身份
        'const KIND_CLS = { "新增": "add", "改进": "imp", "修复": "fix" };',
        "更新日志 · My Music",
    ]:
        assert frag in html, f"更新日志页缺少 {frag}"
    assert "lastpage.js" not in html    # 上次停留页是 Tesla 应用的概念


def test_changelog_link_in_music_menu(auth):
    """听歌应用的更新日志入口: 顶栏菜单撤了 (导航挪去底部页签栏), 入口进
    设置页「更新」子页 (1.8.17 起设置拆四个左右滑的子页; 应用内视图,
    不再整页跳走)。"""
    js = auth.get("/music/static/js/music-settings-view.js").text
    assert 'data-set-tab="changelog">更新</button>' in js   # 「更新」子页的页签
