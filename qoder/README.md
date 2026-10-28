# 今天吃什么

帮人决定下一餐：转盘推荐、按口味搜索、记录喜欢或不喜欢。

公开站点（重新发布前，线上函数仍可能是旧版本）：

https://jin-tian-chi-shen-me-2026-sju7xlq7hm5.qoder.zone

仓库：https://github.com/ssenran-star/odb （分支 `qoder`）

运行步骤见 [RUN.md](RUN.md)，验收样例见 [VERIFY.md](VERIFY.md)，提测表见 [SUBMISSION.md](SUBMISSION.md)。

## 现在实际接到了什么

- 菜品目录在仓库里，不依赖数据库。
- **PowerContext** 负责偏好、用餐历史和反馈。设置 `POWERCONTEXT_URL` 与 `POWERCONTEXT_SCOPE_ID` 后，写入走 `POST /v1/memory/remember`，读回走 `POST /v1/memory/search` 和 `POST /v1/memory/entries/list`。
- **seekdb** 只有在设置了 `SEEKDB_HOST`，并且 HTTP 检查成功时，搜索才会标成语义搜索。没配、或 HTTP 不通，搜索是关键词匹配，页面不会写「已连接 seekdb」。
- 两个地址都没配时是演示模式。页脚只有在 `GET /api/services/status` 里对应服务的 `status` 为 `connected` 时才显示已连接。
- 服务连不上时，推荐和搜索退回本机数据，状态仍是未连通或未配置。

`2026-10-28` 核对过的公开站点仍对 `/functions/v1/app` 返回 `{"ok":false,"error":"Not found"}`。这次提交修正了函数路由；Qoder Desktop 重新发布之后线上才会变。记录在 `evidence/sites-api-probe.txt`。

## 功能

- 转盘推荐，避开最近吃过和不喜欢的菜
- 搜索。未接 seekdb 时按名称、标签和简介做关键词匹配
- 喜欢 / 不喜欢
- 用餐历史
- 项目说明：简介、要解决的问题、核心功能、仓库链接

## 目录

```
src/                 React 页面
functions/           Deno 函数：路由、PowerContext、可选 seekdb
scripts/function-local.ts
scripts/verify-probes.ts
evidence/            运行记录、站点抓取、UID 占位
public/screenshots/  页面上的演示截图
```

## 本地启动

需要 Node.js 22.13+（22.x）或 24+，以及 Deno 2。本环境用 Node v22.23.4、Deno 2.9.8 跑过。

```bash
cd qoder
npm ci
npm run dev
```

另一个终端：

```bash
cd qoder
npm run dev:function
```

浏览器打开 http://127.0.0.1:5173 。前端请求 `/functions/v1/app/...`，由 Vite 转到 `127.0.0.1:8000`。

真实 PowerContext 的环境变量、Sites 发布和验收命令都写在 [RUN.md](RUN.md)。不要把 token 或密码写进仓库。

## 接口

函数会去掉 `/functions/v1/app`、`/app` 和多余的斜杠，所以下面几条指的是同一组路由：

- `GET /functions/v1/app`
- `GET /api/foods`
- `GET /api/foods/search?q=辣`
- `GET /api/foods/random?userId=...`
- `GET|POST /api/user/preferences?userId=...`
- `GET|POST /api/user/history?userId=...`
- `POST /api/feedback?userId=...`
- `GET /api/services/status`

## 证据

- `evidence/powercontext-remember-search.json`：应用经真实 PowerContext 写入并搜索到的偏好和历史
- `evidence/local-demo.png`：未配置时页脚为演示模式
- `evidence/local-connected.png`：状态检查成功后只显示已连接 PowerContext
- `evidence/sites-homepage.png` 与 `evidence/sites-homepage.html`：重新发布前的线上首页
- `evidence/QODER_UID.txt`：UID 留空，由参赛者填写

## 相关项目

- [PowerContext](https://github.com/oceanbase/powercontext)
- [seekdb](https://github.com/oceanbase/seekdb)
- [Qoder](https://qoder.com)
