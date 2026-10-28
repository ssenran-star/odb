# 验证样例

评审按下面的顺序可以玩通主要功能，并核对 PowerContext 确实被写入、再被读回。

技术通过看这三件事。模型的具体措辞可以不同：

1. Dify 的 HTTP 节点打到 PowerContext：`POST /v1/memory/search`、`POST /v1/context/prepare`、`POST /v1/memory/remember` 返回 200。
2. 页脚的「写入前仇账 N 条」和「本轮新记」跟这一轮有没有写入一致。
3. 换一场新的 Dify 对话，仍用同一个 `scope_id`，上一笔仇账仍能被检索和准备上下文读回。

态度会不会跟着仇账变，写在下面的样例对话里，方便对照着玩。措辞不必逐字相同。

2026-10-28 已在 Dify Cloud 走完真实对话，截图在 `evidence/dify-run/`。本地 Server 的读写契约仍在下一节，原始记录在 `evidence/powercontext-contract.json`。导入之后评审要做的点击写在最后一节。

## Dify 云端真实对话（2026-10-28）

已在 Dify Cloud 导入并发布 Chatflow「记仇的酒馆老板」，对话页 `https://udify.app/chat/sOX4UjWbZj3ekiUW`。
模型：OpenAI gpt-4o-mini（AI Credits）。PowerContext 跑在选手本机，经 cloudflared http2 隧道供 Dify HTTP 节点调用。隧道主机名只出现在日志截图里，是当次临时地址，本文不抄录。仓库里没有 Bearer token。

| 轮次 | 输入 | 页脚 | PowerContext 证据 |
| --- | --- | --- | --- |
| 1 | 老板，来一杯麦酒。 | 写入前仇账 0 条｜本轮新记：否 | 执行仇账检索与准备上下文；未记入 |
| 2 | 我把盐罐换成了糖… | 写入前仇账 0 条｜本轮新记：是 | `POST /v1/memory/remember` HTTP 200，`kind=grudge`，`changed=true`（见 `evidence/dify-run/02-log-remember.png`） |
| 3 | （新对话）老板，来一杯麦酒。 | 写入前仇账 1 条｜本轮新记：否 | search 命中盐罐仇账；prepare ready；未记入（见 `evidence/dify-run/03-log-search-prepare.png`） |

随后加强提示词后，新会话点酒的 reply 已能点名「盐罐换成糖」（`evidence/dify-run/03b-new-session-remembers.png`）。当前 DSL 里「老疤」的温度为 0，并写了只输出一个 JSON、有旧账必须点名具体恶作剧、点单不记账这几条。截图均在 `evidence/dify-run/`。

| 文件 | 画面里能看到的内容 |
| --- | --- |
| `evidence/dify-run/chat-ready.png` | 已发布的 Web 对话页。开场白、三条建议问题、「Start New chat」。还没有玩家输入 |
| `evidence/dify-run/01-empty-order-beer.png` | 第一轮输入「老板，来一杯麦酒。」页脚「写入前仇账 0 条｜本轮新记：否」 |
| `evidence/dify-run/02-prank-remember.png` | 同一会话继续输入盐罐换成糖。回复提到加价。页脚「写入前仇账 0 条｜本轮新记：是」 |
| `evidence/dify-run/02-log-remember.png` | 该轮追踪：「记入仇账」为 `POST /v1/memory/remember`，HTTP 200，响应里 `changed` 为 true，`kind` 为 `grudge`，`family` 为 `atomic-memory`。右侧对话页脚仍是 0 条、本轮新记是 |
| `evidence/dify-run/03-new-session-remembers.png` | 侧栏另起一条「老板，来一杯麦酒。」页脚「写入前仇账 1 条｜本轮新记：否」 |
| `evidence/dify-run/03-log-search-prepare.png` | 该轮追踪：`POST /v1/memory/search` HTTP 200，`hits` 里有盐罐那笔 `grudge`；「准备上下文」已执行。右侧页脚仍是 1 条、本轮新记否 |
| `evidence/dify-run/03b-new-session-remembers.png` | 加强提示词之后的新会话点酒。回复点名「盐罐换成糖」，并说到加价。这一张的页脚是「写入前仇账 1 条｜本轮新记：是」 |

第 3 轮和第 2 轮不是同一条 Dify 会话：侧栏各有一条标题为「老板，来一杯麦酒。」的对话，scope 没有换，页脚从 0 条变成 1 条。`03b` 用来看加强提示词之后的回复措辞；跨会话「本轮新记：否」以 `03-new-session-remembers.png` 和 `03-log-search-prepare.png` 为准。

技术结论：必须使用的 Dify + PowerContext 已在真实对话中跑通；跨会话同一 `scope_id` 可读回仇账。技术通过按本节开头的三条（HTTP 200、页脚、跨会话同一 scope）判断，模型措辞可以不同。

## 这次已经跑通的契约

2026-10-27，Server `package_version` 为 `1.4.2.dev4+gcdb8da296`，OpenAPI `1.4.1`。命令：

```bash
python3 dify/scripts/check_dsl.py
python3 dify/scripts/powercontext_contract.py \
  --expect-empty-before \
  --idempotency-key rust-anchor-contract-sample
```

`check_dsl.py` 不连网。它检查三个 HTTP 节点的路径、占位符，并执行 DSL 里的代码节点。

契约脚本使用 DSL 代码节点生成的请求体。记录文件里的关键结果：

| 步骤 | 结果 |
| --- | --- |
| 写入前 `POST /v1/memory/search`，查询 `仇账` | `hits` 为空 |
| `POST /v1/memory/remember` | HTTP 200，`records[0].state=active`，`kind=grudge`，`artifact.family=atomic-memory`，`revision=1`。正文以「仇账：」开头，并包含盐罐和炖菜 |
| 再次 search，查询 `仇账`、`炖菜`、`盐罐` | 响应 `mode=text`，都能命中这条正文 |
| search，查询 `盐` | 0 条。单字没有被当成「盐罐」 |
| search，查询 `麦酒` | 0 条。点酒这句话本身不在仇账里 |
| `POST /v1/context/prepare`，查询 `仇账` | `schema=powercontext.prepared-context.v1`，`status=ready`，`content_bytes=739`，`content` 含炖菜，并带有不可信历史的包裹文本 |
| prepare，查询 `麦酒` | `status=empty`，`content=null`，`content_bytes=0` |
| 点单的模型 JSON | 代码节点给出 `should_remember=no`，不产生 remember 请求体 |
| 再写入 `kind=atonement` 后 search `仇账` | 2 条，分别含「恶作剧」和「赔罪」 |

remember 请求只有 `scope_id`、`kind`、`text`、`reason`。记录文件不含 Bearer token。里面的 `scope_id` 只存在于产出它的那台 Server；评审在自己的 Server 上会得到新的 id。

同一把 `idempotency_key` 再跑时，写入前的检索不再为空。要看「空账 → 写入 → 读回」，换一个新的 `--idempotency-key`，并保留 `--expect-empty-before`。

## 给 Dify 对话用的初始状态

1. PowerContext 已启动，`/health/live` 为 `ok`。
2. 执行 `python3 dify/scripts/powercontext_contract.py --init-scope`。
3. 把打印的 `scope_id` 填进 Dify 环境变量 `POWERCONTEXT_SCOPE_ID`。`POWERCONTEXT_URL` 指向这台 Server。
4. 这个 scope 在全新 Server 上没有仇账。`idempotency_key` 是 `rust-anchor-traveler-demo`。

恢复初始状态：用新的 idempotency key 再执行一次初始化（把脚本里的 key 通过你自己的 scope 创建请求换掉，或直接 `POST /v1/scopes`），把新的 `scope_id` 填回 Dify。旧对话仍然读环境变量里的 scope，所以换 id 之后从新对话开始验收。

## 样例对话

发布应用后，从一轮新对话开始。三句玩家输入：

### 1. 空账时点酒

输入：

```text
老板，来一杯麦酒。
```

预期：

- 老疤把你当新客人，麦酒一杯一个铜子。回复里不出现盐罐、糖、炖菜。
- 页脚：`写入前仇账 0 条｜本轮新记：否`。
- 运行日志执行了「仇账检索」和「准备上下文」，没有执行「记入仇账」。
- 检索响应的 `hits` 为 `[]`。准备上下文的 `status` 为 `empty`。

### 2. 写下一笔恶作剧

输入：

```text
我把盐罐换成了糖，你的炖菜全毁了，哈哈！
```

预期：

- 回复当场变脸，提到这件事，并出现加价、拒赊或赶人一类的态度。
- 页脚：`本轮新记：是`。条数仍是写入前的数字；上一轮没记过时是 0。
- 「记入仇账」HTTP 200。`records[0].kind` 为 `grudge`，`state` 为 `active`，`text` 含「仇账」以及盐罐或炖菜。
- 「仇账检索」在这一轮仍可能是空的，因为它发生在写入之前。

### 3. 新会话里再点酒

点 Dify 的「新对话」。不要改 `POWERCONTEXT_SCOPE_ID`。

输入：

```text
老板，来一杯麦酒。
```

预期：

- 回复点名盐罐、糖或炖菜，价钱或态度和第一轮不同。
- 页脚条数大于等于 1，`本轮新记：否`。
- 「仇账检索」的 `hits` 里能看到上一轮写入的 `text`，响应 `mode` 为 `text`。
- 「准备上下文」的 `status` 为 `ready`，`content` 含那笔恶作剧。
- 「记入仇账」这一轮不执行。

这就是跨会话记忆的证明：Dify 的 conversation id 换了，PowerContext 的 scope 没换，回复跟着旧账变。

### 4. 可选：赔罪

输入：

```text
上次把盐换成糖是我不对。这袋铜子赔炖菜，我当面给你道歉。
```

预期：「记入仇账」再写一条，`kind` 为 `atonement`，正文含「赔罪」。再开一场新对话去点酒时，他可以倒酒，但仍然提得起炖菜，而不是把你当成第一次进门的人。

## 评审导入后要做的事

本仓库已经包含可导入的 DSL、占位配置、`evidence/dify-run/` 里的 Dify Cloud 截图，以及一次本地 PowerContext 读写记录。评审若要在自己的环境再走一遍：

1. 按 [RUN.md](RUN.md) 启动 PowerContext，导入 DSL，把「老疤」换成自己的对话模型，填入 `--init-scope` 给出的 `scope_id`。
2. 按上一节走完第 1 到第 3 轮。第 3 轮必须是新对话。
3. 打开第 2 轮的「记入仇账」节点，确认响应里有 `records`。打开第 3 轮的「仇账检索」和「准备上下文」，确认读回了同一句仇账。
4. 若要留下和 `evidence/powercontext-contract.json` 同形的日志，在自己的 Server 上重跑契约脚本。换一把新的 `--idempotency-key`，这样写入前的检索仍是空的。

节点日志里的 URL、请求 JSON 和响应 JSON 就是 PowerContext 参与玩法的运行证据。只打开健康检查、不走这三轮对话，不算完成样例。
