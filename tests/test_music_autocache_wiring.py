"""My Music 自动缓存接线测试 (1.8.77 播放时自动缓存下一曲): 纯逻辑模块
+ 浏览器接线 + 换源优先级 + 预取顺手落盘 + 已下载页统计行分栏。"""
from pathlib import Path

from tests.music_static_files import MUSIC_STATIC

ROOT = Path(__file__).resolve().parent.parent


def test_music_autocache_wiring():
    """自动缓存全链: 纯逻辑 LRU (node 直测另有 autocache.test.mjs) + 与
    手动下载同一道门/分仓 + 换源优先本地 (手动下载 > 自动缓存 > 流媒体,
    用户亲手下的不许被 LRU 清) + 预取字节顺手落盘 (同一份字节不走第二
    次网络) + 已下载页统计行分栏 (没有手动下载也带出这行)。"""
    pure_js = (MUSIC_STATIC / "js" / "autocache.js").read_text(encoding="utf-8")
    integration_js = (MUSIC_STATIC / "js"
                      / "music-autocache-integration.js").read_text(
                          encoding="utf-8")
    sources_js = (MUSIC_STATIC / "js" / "music-player-sources.js").read_text(
        encoding="utf-8")
    prefetch_js = (MUSIC_STATIC / "js" / "music-player-prefetch.js").read_text(
        encoding="utf-8")
    pane_js = (MUSIC_STATIC / "js" / "music-downloads-pane.js").read_text(
        encoding="utf-8")
    # 纯逻辑: LRU (cached_at 排队清最旧) + 预算 (maxBytes) + 自愈/幂等
    assert "function createAutoCache" in pure_js
    assert "cached_at" in pure_js and "maxBytes" in pure_js
    assert "2 * 1024 * 1024 * 1024" in pure_js          # 默认预算 2GB
    assert "module.exports" in pure_js                  # node --test 直测路径
    # 接线: 与手动下载同一道门, 缓存/索引分仓 (LRU 清不到用户亲手下的)
    assert "const autoCacheEnabled = downloadsEnabled;" in integration_js
    assert '"music-autocache-v1"' in integration_js
    assert '"music-autocache"' in integration_js
    assert "autoCache.put(trackId, blob).catch(() => {});" in integration_js
    # 换源优先级: 手动下载优先, 自动缓存次之, 流媒体兜底
    assert "async function localBlobFor" in sources_js
    assert "const blob = await downloads.cachedBlob(trackId);" in sources_js
    assert "return autoCache.blob(trackId);" in sources_js
    assert "function trackLocalCached" in sources_js    # 同步答 (只看索引)
    # 预取字节顺手落盘: fire-and-forget, 失败/没实例都不挡预取主路
    assert "autoCacheStash(trackId, blob);" in prefetch_js
    # 已下载页统计行分栏: 空列表分支也带出这行 (不然私仓用着却看不见)
    assert 'id="dl-autocache"' in pane_js
    assert "autoCache.usage()" in pane_js
    # 门禁收编: tsc 类型检查 + c8 覆盖率都认这个纯模块
    assert "app/music/static/js/autocache.js" in (ROOT / "tsconfig.json"
                                                  ).read_text(encoding="utf-8")
    assert "autocache.js" in (ROOT / "run_tests.sh").read_text(encoding="utf-8")
