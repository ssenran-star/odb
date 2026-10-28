# 验证样例

两组都要能按步骤做。样例 A 不需要外网服务。样例 B 证明 PowerContext 参与了偏好和历史，而不是只 ping 了一下端口。

公开站点在重新发布这次提交之前，函数仍可能 404。线上复测结果留在文末，不要把 2026-10-28 之前的 404 写成已经通过。

## 样例 A：演示模式搜索和偏好

### 初始数据

目录在 `functions/data.ts`，共 20 道菜。和本样例有关的是：

| id | 名称 | 分类 | 和查询的关系 |
| --- | --- | --- | --- |
| 1 | 红烧牛肉面 | noodle | 偏好里的喜欢 |
| 2 | 麻辣火锅 | hotpot | 名称含「辣」 |
| 4 | 宫保鸡丁 | chinese | 简介/标签含「辣」 |
| 9 | 酸菜鱼 | chinese | 标签含「麻辣」 |
| 12 | 麻辣烫 | hotpot | 名称含「辣」 |
| 17 | 螺蛳粉 | noodle | 标签含「酸辣」 |

不要先导出 `POWERCONTEXT_URL` 或 `SEEKDB_HOST`。

### 输入

- 搜索词：`辣`
- 用户：`verify-demo`
- 偏好 JSON：`{"favoriteCategories":["noodle"],"favoriteFoods":["1"],"dislikedFoods":["2"],"spicyLevel":1,"priceRange":"low"}`

### 操作步骤

1. 按 `RUN.md` 启动 `npm run dev:function`（不要带 PowerContext 环境变量）。
2. 请求健康检查、菜品列表、搜索和状态。
3. 写入上面的偏好，再读一次。
4. 用同一 `userId` 请求随机推荐，重复几次。
5. 打开 http://127.0.0.1:5173 ，看页脚和搜索框下方的字。

### 预期结果

- `GET /functions/v1/app`、`/functions/v1/app/`、`/app/api/foods` 都是 HTTP 200。
- 列表 `source` 为 `catalog`，20 道菜。
- 搜索 `q=辣` 的 `searchMethod` 为 `keyword`，`source` 为 `local`。结果里有麻辣火锅、麻辣烫、螺蛳粉、宫保鸡丁、酸菜鱼。
- 状态里 `mode` 为 `demo`，seekdb 和 PowerContext 的 `status` 都是 `unconfigured`，不是 `connected`。
- 偏好读回 `memorySource` 为 `local`，`favoriteCategories` 为 `["noodle"]`。
- 随机推荐的 `category` 为 `noodle`（红烧牛肉面或螺蛳粉）。红烧牛肉面在喜欢列表里，出现次数通常更多。
- 页面页脚是「演示模式：未配置 PowerContext / seekdb」。搜索说明是「关键词搜索（seekdb 未连接）」。不会出现「已连接 seekdb + PowerContext」。

### 实际运行记录

2026-10-28，本机 Node v22.23.4、Deno 2.9.8，函数 `http://127.0.0.1:8000`，未设置 PowerContext / seekdb。

健康检查：

```json
{"ok":true,"message":"今天吃什么 API 服务运行中","route":"/","receivedPath":"/functions/v1/app","mode":"demo","services":{"seekdb":"unconfigured","powerContext":"unconfigured"}}
```

`GET /app/api/foods`：`ok=true`，`source=catalog`，20 条，第一条是红烧牛肉面。

`GET /api/foods/search?q=辣`：

```json
{"searchMethod":"keyword","source":"local","names":["麻辣火锅","麻辣烫","螺蛳粉","宫保鸡丁","酸菜鱼"]}
```

状态：

```json
{"ok":true,"route":"/api/services/status","receivedPath":"/app/api/services/status","mode":"demo","services":{"seekdb":{"status":"unconfigured","configured":false},"powerContext":{"status":"unconfigured","configured":false}}}
```

偏好写入与读回的 `memorySource` 均为 `local`，分类为 `noodle`。连续三次随机推荐都是红烧牛肉面（id `1`，category `noodle`）。这是一次运行的结果，不是唯一合法结果。

浏览器 http://127.0.0.1:5173 在未配置时的 DOM 文本包含「演示模式：未配置 PowerContext / seekdb」和「偏好与历史：本机浏览器」，不包含「已连接 seekdb + PowerContext」。截图：`evidence/local-demo.png`。

## 样例 B：PowerContext 记住偏好和历史

### 初始数据

- 服务：`POWERCONTEXT_URL=https://cal-ent-altered-higher.trycloudflare.com`（隧道会变）
- Scope：`scp_15fskprdpsyc6887xq7v0mt3n5`（标题「今天吃什么-Qoder」）
- 该 scope 里已经有 kind 为 `user_preferences` 和 `eating_history` 的旧记忆，正文含「喜欢川菜与麻辣香锅」。见本文件「指定技术」一节的 prior capture，也在证据 JSON 的 `prior_capture`。
- 本次新增用户：`qoder-verify-20261028`
- 写入偏好：喜欢的菜系 `chinese`、`hotpot`，辣度 `3`，价位 `medium`，喜欢 `2`（麻辣火锅）和 `9`（酸菜鱼），不喜欢 `3`（寿司拼盘）
- 历史：foodId `2`，`liked: true`

### 输入

```bash
export POWERCONTEXT_URL="https://cal-ent-altered-higher.trycloudflare.com"
export POWERCONTEXT_SCOPE_ID="scp_15fskprdpsyc6887xq7v0mt3n5"
```

重启 `npm run dev:function` 后再发请求。

```bash
curl -sS -X POST "http://127.0.0.1:8000/functions/v1/app/api/user/preferences?userId=qoder-verify-20261028" \
  -H 'content-type: application/json' \
  -d '{"favoriteCategories":["chinese","hotpot"],"spicyLevel":3,"priceRange":"medium","dislikedFoods":["3"],"favoriteFoods":["2","9"]}'

curl -sS -X POST "http://127.0.0.1:8000/api/user/history?userId=qoder-verify-20261028" \
  -H 'content-type: application/json' \
  -d '{"foodId":"2","liked":true}'
```

### 操作步骤

1. 导出上面两个变量，确认 `USE_REAL_SERVICES` 不是 `false`。
2. 重启函数进程。
3. `GET /functions/v1/app/api/services/status`。
4. 按上面的输入写入偏好和历史，再 GET 读回。
5. 直接调用 PowerContext，不要经过应用内存：

```bash
curl -sS -X POST "$POWERCONTEXT_URL/v1/memory/search" \
  -H 'content-type: application/json' \
  -d '{"scope_id":"scp_15fskprdpsyc6887xq7v0mt3n5","query":"用户 qoder-verify-20261028 偏好 辣度","limit":5}'
```

6. 打开 http://127.0.0.1:5173 。页脚只有在步骤 3 的 `powerContext.status` 为 `connected` 时才显示「已连接 PowerContext」。seekdb 未配置时，这句话里没有 seekdb。

### 预期结果

- 状态：`powerContext.status` 为 `connected`，`configured` 为 true，`scopeId` 为上面的 id，`searchMode` 为 `text`。`seekdb.status` 仍是 `unconfigured`。
- 应用读回偏好的 `memorySource` 为 `powercontext`，辣度为 3，喜欢的菜包含 `2` 和 `9`。
- 应用读回历史的 `memorySource` 为 `powercontext`，第一条是麻辣火锅且 `liked` 为 true。
- PowerContext 搜索命中的 `kind` 含 `user_preferences`。正文含「用户 qoder-verify-20261028 偏好」和「辣度偏好 3」，并带 `PCJSON:` 行。这是 `/v1/memory/remember` 写入后再被 `/v1/memory/search` 检索到的结果。
- 旧的 anonymous 记忆可以仍然出现在更后面的命中里。它们没有 `PCJSON:`，应用不会把它们当成结构化偏好。

### 实际运行记录

2026-10-28，同一台机器，函数带上上述两个环境变量后重启。完整 JSON 在 `evidence/powercontext-remember-search.json` 的 `app_roundtrip`。下面是该次响应的原文，不是事后编的距离或条数。

状态（`hitCount` 在写入前为 2，之后搜索「喜欢吃什么辣的」为 4，因为新旧记忆都在）：

```json
{"ok":true,"route":"/api/services/status","receivedPath":"/functions/v1/app/api/services/status","mode":"configured","services":{"seekdb":{"status":"unconfigured","configured":false,"host":null,"port":null,"detail":null},"powerContext":{"status":"connected","configured":true,"scopeId":"scp_15fskprdpsyc6887xq7v0mt3n5","searchMode":"text","hitCount":2,"detail":null}}}
```

应用写入偏好：`memorySource` = `powercontext`。读回：

```json
{"ok":true,"data":{"favoriteCategories":["chinese","hotpot"],"spicyLevel":3,"priceRange":"medium","dislikedFoods":["3"],"favoriteFoods":["2","9"]},"memorySource":"powercontext"}
```

历史读回：foodId `2`，名称麻辣火锅，`liked` true，`memorySource` `powercontext`，时间戳 `1793162314166`。

直接搜索的第一条命中：

- mode: `text`
- kind: `user_preferences`
- artifact_id: `art_d94e56647e614a5e97a075dd684f91e4`
- score: `0.01639344262295082`
- matched_by: `text`
- 正文开头：`用户 qoder-verify-20261028 偏好：喜欢的菜系 chinese、hotpot；辣度偏好 3；价位 medium；喜欢的菜 麻辣火锅、酸菜鱼；不喜欢 寿司拼盘。`

第二条是同一用户的 `eating_history`，artifact_id `art_dc14ca6706564d1d8e572b280dcdbc55`，score `0.016129032258064516`，正文含「麻辣火锅 2（喜欢）」。

浏览器在这次连通配置下的 DOM 含「已连接 PowerContext」和「偏好与历史：PowerContext」，含「关键词搜索（seekdb 未连接）」，不含「已连接 seekdb」。截图：`evidence/local-connected.png`。

隧道失效时，把 `POWERCONTEXT_URL` 换成新的地址再跑。不要沿用打不开的主机名，也不要手填命中分数。

## 指定技术发挥作用的记录

发挥作用的是 PowerContext，不是 seekdb。

| 动作 | 接口 | 这次看到的结果 |
| --- | --- | --- |
| 状态检查 | `POST /v1/memory/search`，查询「喜欢吃什么辣的」 | `searchMode=text`，写入前 `hitCount=2` |
| 保存偏好 | 应用 `POST /api/user/preferences` → `POST /v1/memory/remember` | kind `user_preferences`，artifact `art_d94e56647e614a5e97a075dd684f91e4` |
| 保存历史 | 应用 `POST /api/user/history` → `POST /v1/memory/remember` | kind `eating_history`，artifact `art_dc14ca6706564d1d8e572b280dcdbc55` |
| 核对检索 | 直接 `POST /v1/memory/search` | 命中正文含用户 id、辣度偏好 3、麻辣火锅 |

更早一次只读抓取（同一 scope，查询「喜欢吃什么辣的」）在证据文件的 `prior_capture`：两条 active 记忆，kind 为 `eating_history` 与 `user_preferences`，artifact 分别为 `art_19524f611fba456da0d3a0fa84d5dfde`、`art_4966f10befe6448482a2a008ac06c6a3`。那次没有经过本仓库的新客户端，这次样例 B 的读写经过了 `functions/powercontext-client.ts`。

seekdb 这次没有配置，状态是 `unconfigured`。不要把关键词搜索写成 seekdb 距离。

## 线上站点（重新发布后由参赛者粘贴）

推送前，2026-10-28T04:39:26Z，公开 URL 的首页 HTTP 200，函数仍是：

```text
GET /functions/v1/app                         404  {"ok":false,"error":"Not found"}
GET /functions/v1/app/api/foods               404  {"ok":false,"error":"Not found"}
GET /functions/v1/app/api/services/status     404  {"ok":false,"error":"Not found"}
```

原文：`evidence/sites-api-probe.txt`。首页抓取：`evidence/sites-homepage.html`、`evidence/sites-homepage.png`。当时页面页脚仍写着「已连接 seekdb + PowerContext」，和 404 不符。这次提交改掉了这个默认文案；线上要等重新发布。

重新发布并写好 Secrets 之后，把下面空位换成无痕窗口里的真实输出。没做的就留空，不要抄上面的本地 JSON。

- 运行时间：
- 公开 URL：
- `GET /functions/v1/app` 状态码和正文：
- `GET /functions/v1/app/api/services/status` 里 `powerContext.status`：
- 页脚原文：
- 若 status 不是 `connected`：不要写成已通过技术结合
