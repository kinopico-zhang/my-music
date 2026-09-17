# My Music

家庭自用的听歌应用: 扫描 NAS 上的音乐库 (FLAC/DSF/MP3…), 手机浏览器里
浏览 / 播放 / 看歌词 / 建歌单 / 分享歌曲链接 / 离线缓存。FastAPI +
SQLAlchemy + Pydantic, 前端零依赖 (原生 JS + Service Worker)。

从 [My Home](https://github.com/kinopico-zhang/my-home) 组合仓拆出来的
独立仓: 账号体系 (登录/注册/账号管理) 内嵌在 `app/home/`, 单独 clone
本仓即可部署, 不需要组合仓。

## 部署

需要 Python 3.13+ (venv):

```sh
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env      # 编辑: 至少设 AUTH_PASS (首启种子管理员)
mkdir -p /path/to/music   # 曲库目录 (也可进应用后在 设置 页改)
./run.sh                  # 默认 8500 端口; data/certs/ 有证书自动 HTTPS
```

打开 `http://<host>:8500/` → 自动进 `/music` (未登录先到登录页, 账密是
`.env` 里 `AUTH_USER`/`AUTH_PASS` 种下的管理员, 之后可在界面里改)。

数据都落在 `data/` (git 忽略): `music.db` 曲库索引 / `users.db` 账号 /
`music-art/` 封面缓存。音乐目录默认 `/share/Media/Music`, 用
`MYTESLA_MUSIC_DIR` 或设置页改。

## 测试

```sh
npm install               # 前端工具链 (eslint/tsc/stylelint/html-validate/c8)
./run_tests.sh            # pylint + mypy + pytest + 前端全套 + 覆盖率门禁
```

从 My Home 组合仓的 `apps/my-music` 下跑时不用 npm install —— 脚本会
软链组合仓根的 node_modules。

## 结构

```
app/
  music/      听歌应用本体 (扫描 / 查询 / 媒体流 / 分享 / 接口与页面)
  home/       账号层副本 (登录/注册/账号管理页面 + /api 会话接口 + 中间件)
  account_store/  账号库存取 (scrypt 密码 + 注册邀请)
  authentication.py  会话 cookie 签发与校验 (HMAC)
  main.py     独立装配: 账号层挂根, 应用挂 /music
tests/        pytest (真实 ORM + SQLite 临时库) + node --test (纯逻辑模块)
```

账号层的接口与 cookie 配方和 My Home 组合仓完全一致 (`/api/login`、
`/api/me`…): 组合部署时外层把 `MYHOME_USERS_DB` / `MYHOME_SECRET_FILE`
指到共享的账号库与密钥文件, 三个应用就共用同一批账号单点登录。
