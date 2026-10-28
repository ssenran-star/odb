# 运行说明

作品是「今天吃什么」。命令都在仓库的 `qoder/` 目录执行。配置示例只有占位值，不要把真实 token、密码写进文件或提交记录。

本说明在 Node v22.23.4、Deno 2.9.8 上跑通。Node 需要 22.13 及以上的 22.x，或 24 及以上。Deno 使用 2.x。

## 1. 安装

```bash
cd qoder
node -v
deno --version
npm ci
```

没有 Deno 时，可用 https://docs.deno.com/runtime/getting_started/installation/ 安装，再把 `deno` 放到 `PATH`。

## 2. 只跑演示

演示模式不连接 PowerContext 或 seekdb。偏好只留在这次函数进程里，刷新页面后的历史以浏览器 `localStorage` 为准。页脚应显示「演示模式：未配置 PowerContext / seekdb」，不能显示已连接。

终端 A：

```bash
npm run dev
```

终端 B：

```bash
npm run dev:function
```

打开 http://127.0.0.1:5173 。

函数直接监听 http://127.0.0.1:8000 ，这些地址都应返回 JSON，而不是 404：

```bash
curl -sS http://127.0.0.1:8000/functions/v1/app
curl -sS http://127.0.0.1:8000/functions/v1/app/api/foods
curl -sS http://127.0.0.1:8000/app/api/services/status
curl -sS --get --data-urlencode "q=辣" http://127.0.0.1:8000/api/foods/search
```

自检路由和打印上述命令：

```bash
npm run verify:probes
npm run test:function
```

`USE_REAL_SERVICES=false` 会强制演示，即使下面的地址已经填写。

## 3. 接入 PowerContext

这是验收用的指定技术：用户偏好、用餐历史和喜欢/不喜欢都经过 PowerContext 记忆，不是只做连通性探测。

`trycloudflare.com` 地址会轮换。下面的主机名在 2026-10-28 可用；打不开时换成自己的隧道或本机 `http://127.0.0.1:8000`，不要把过期地址当成故障以外的结论。

```bash
export POWERCONTEXT_URL="https://cal-ent-altered-higher.trycloudflare.com"
export POWERCONTEXT_SCOPE_ID="scp_15fskprdpsyc6887xq7v0mt3n5"
export POWERCONTEXT_API_TOKEN=""
```

`POWERCONTEXT_API_TOKEN` 留空表示服务端没开鉴权。服务端要求 Bearer 时再填，只放在环境里。

已有 scope 可以直接用。新建 scope 时必须带 `idempotency_key`（占位，不要用真实密钥当 key 的替代品）：

```bash
curl -sS -X POST "$POWERCONTEXT_URL/v1/scopes" \
  -H 'content-type: application/json' \
  -d '{"title":"今天吃什么","summary":"食物偏好与用餐历史","idempotency_key":"what-to-eat-scope"}'
```

从返回 JSON 里取出 `scope_id`，设到 `POWERCONTEXT_SCOPE_ID`。

停掉原来的 `npm run dev:function`，在同一个已导出变量的终端重新启动。然后：

```bash
curl -sS http://127.0.0.1:8000/functions/v1/app/api/services/status
```

`services.powerContext.status` 为 `connected` 才表示 `POST /v1/memory/search` 成功。只打开页面、或只访问 `/health/live`，不算接上。

可选：把同一次读写打出来。

```bash
npm run verify:probes -- --write --out evidence/powercontext-remember-search.json
```

没有这两个环境变量时，脚本只做路由自检，不会假装连上了服务。

## 4. seekdb（可选，当前不是验收主路径）

Deno 函数不会走 pyseekdb 的 MySQL 协议。只有 `SEEKDB_HOST` 指向一个能响应 HTTP JSON 的 seekdb 网关时，状态才会变成 `connected`，搜索的 `searchMethod` 才会是 `semantic`。连不上就保持关键词搜索，并在状态里标 `disconnected`。

```bash
export SEEKDB_HOST=""
export SEEKDB_PORT="2881"
export SEEKDB_USER="root"
export SEEKDB_PASSWORD=""
export SEEKDB_DATABASE="food_app"
```

`SEEKDB_HOST` 留空表示不启用。密码只放在环境变量 `SEEKDB_PASSWORD`。

## 5. 发布到 Qoder Sites

用个人账号。企业版账号不能把站点设成公开。

1. 拉取分支 `qoder` 的最新提交。
2. 用 Qoder Desktop 打开该项目，进入 Sites。
3. 可见范围选「任何人都可访问」。
4. 在 Sites 的环境变量 / Secrets 里写入与本地相同的名字。值只写在 Qoder 里，不写进 git：
   - `POWERCONTEXT_URL`
   - `POWERCONTEXT_SCOPE_ID`
   - `POWERCONTEXT_API_TOKEN`（没有鉴权就不要建这个变量）
   - 可选：`SEEKDB_HOST`、`SEEKDB_PORT`、`SEEKDB_USER`、`SEEKDB_PASSWORD`、`SEEKDB_DATABASE`
   - 不要把 `USE_REAL_SERVICES` 设成 `false`，否则会强制演示。
5. 再次点击「发布」。只改代码或只改变量而不发布，线上仍是旧包。
6. 用无痕窗口打开公开 URL，确认未登录能打开首页。

发布后核对函数（把主机换成自己的 Sites 域名）：

```bash
curl -sS https://jin-tian-chi-shen-me-2026-sju7xlq7hm5.qoder.zone/functions/v1/app
curl -sS https://jin-tian-chi-shen-me-2026-sju7xlq7hm5.qoder.zone/functions/v1/app/api/foods
curl -sS https://jin-tian-chi-shen-me-2026-sju7xlq7hm5.qoder.zone/functions/v1/app/api/services/status
```

健康检查应返回 `"ok": true`。状态接口在 Secrets 生效后，`powerContext.status` 应为 `connected`。若仍是 `{"ok":false,"error":"Not found"}`，说明这次提交还没发布上去。2026-10-28 推送前的线上结果记在 `evidence/sites-api-probe.txt`，当时就是这个 404。

## 6. 和验证样例的关系

本地演示走 [VERIFY.md](VERIFY.md) 样例 A。接上 PowerContext 后走样例 B。样例 B 的原始响应在 `evidence/powercontext-remember-search.json`。
