"""独立部署的鉴权接线测试: 根路径进应用 / 登录拦截 / 登录登出 /
账号接口 —— 独立仓与组合仓共用同一套账号配方, 这里验独立装配那一层。"""
from app import config
from tests.conftest import TEST_PASS, TEST_USER


def test_root_redirects_to_music(client):
    """根路径无条件进听歌应用 (独立仓没有门厅), 未登录与否都一样。"""
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 302 and r.headers["location"] == "/music"


def test_music_redirects_to_scope_login(client):
    """未登录进 /music: 302 到应用 scope 内的登录页, 带原地址回跳。"""
    r = client.get("/music", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/music/login?next=%2Fmusic"
    # 登录页本身与静态资源放行 (表单要先看得见)
    assert client.get("/music/login").status_code == 200
    assert client.get("/login").status_code == 200


def test_api_unauthorized_401(client):
    """未登录的账号接口回 401 JSON (页面才 302, 接口不跳转)。"""
    r = client.get("/api/me")
    assert r.status_code == 401 and r.json() == {"detail": "未登录"}
    # 接口响应禁缓存 (改完账号浏览器不能用旧值)
    assert r.headers["cache-control"] == "no-store"


def test_login_flow(auth):
    """登录 → 会话 cookie 进 /music; /api/me 报账号; 登录页再进直接跳应用。"""
    r = auth.get("/music")            # 307 补斜杠后落到应用主页
    assert r.status_code == 200
    me = auth.get("/api/me").json()
    assert me == {"name": TEST_USER, "is_admin": True}
    r = auth.get("/login", follow_redirects=False)
    assert r.status_code == 302 and r.headers["location"] == "/music"
    r = auth.get("/music/login", follow_redirects=False)
    assert r.status_code == 302 and r.headers["location"] == "/music"


def test_login_wrong_password(client):
    """错密码 401, 不发 cookie; 限速计数涨 (第 6 次锁 60 秒)。"""
    for _ in range(config.LOGIN_MAX_FAILS):
        r = client.post("/api/login",
                        json={"user": TEST_USER, "password": "wrong"})
        assert r.status_code == 401 and "auth" not in r.cookies
    r = client.post("/api/login",
                    json={"user": TEST_USER, "password": TEST_PASS})
    assert r.status_code == 429 and "尝试次数过多" in r.json()["detail"]


def test_logout_clears_session(client, auth):  # pylint: disable=unused-argument
    """登出清 cookie: 再进 /music 又被拦回登录页。"""
    assert client.post("/api/logout").status_code == 200
    r = client.get("/music", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/music/login?next=%2Fmusic"


def test_accounts_page_and_share_surface(client, auth):  # pylint: disable=unused-argument
    """账号管理页 (管理员) 与分享面免登录 (uuid 即凭证) 都在。"""
    assert auth.get("/accounts").status_code == 200
    # 分享链接面前缀放行: 页面免登录直接渲染 (坏链接由页面自己提示),
    # 数据接口对不存在的 token 410 Gone —— 都不是 302 登录页
    assert client.get("/music/share/no-such-uuid").status_code == 200
    r = client.get("/music/share/no-such-uuid/api")
    assert r.status_code == 410
    # 平台验证文件: verify/ 里没有的一律 404 (有则原样吐回, 见 pages.py)
    assert client.get("/whatever.txt").status_code == 404
