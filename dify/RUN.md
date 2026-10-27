# 运行说明

## 创意和体验

玩家在 Dify 的对话窗口里和锈锚酒馆老板老疤说话。Dify 编排每一轮：先向 PowerContext 读取仇账，再让模型生成回复；只有这一句是恶作剧或带补偿的赔罪时，才写回一条记忆。下一次打开新会话，只要还是同一个 `scope_id`，老疤就会按旧账改变态度。

应用入口是导入并发布后的 Dify Web 对话页。发布后的应用 API 也可以发同一句话，验证样例按 Web 对话来做。

## 版本

| 项目 | 版本与说明 |
| --- | --- |
| Dify DSL | `0.3.0`，`advanced-chat`。2026-10-27 查到的 Dify `main` 当前 DSL 是 `0.7.0`（`api/constants/dsl_version.py`）。旧 DSL 可以导入，界面若提示版本较旧，确认继续 |
| Dify 运行 | 能导入 DSL 0.3.0 的 Dify 1.x。本环境没有启动 Dify，工作室里的点击留给评审，见 [VERIFY.md](VERIFY.md) |
| 对话模型 | 任意已安装的对话模型。DSL 里的占位是 `langgenius/openai/openai` / `gpt-4o-mini`。不需要 Embedding，也不需要 Rerank |
| PowerContext | 2026-10-27 从 `github.com/oceanbase/powercontext` 的 `master` 安装。跑通记录里的 `package_version` 是 `1.4.2.dev4+gcdb8da296`。该进程的 `/openapi.json` 的 `info.version` 是 `1.4.1`，`/v1/server-info` 的 `api_contract_version` 是 1.4 |
| Python | 官方要求 3.11+。本环境用 3.12.3 跑 Server 和脚本 |
| 脚本依赖 | 标准库，外加 PyYAML（`check_dsl.py` 和契约脚本读取 DSL） |
| 插件 | 无。DSL 的 `dependencies` 为空 |

存储是 Server 默认的 SQLite。鉴权默认关闭，只监听本机回环。推理模型可以不配：本作品只调用显式 Memory 和 `prepare`，不调用 Server 侧生成。

## 环境变量

占位值也写在 `.env.example`。仓库里不放真实 token。

| 变量 | 占位 | 填到哪里 |
| --- | --- | --- |
| `POWERCONTEXT_URL` | `http://127.0.0.1:8000` | Dify 环境变量，以及跑脚本时的环境。不要以斜杠结尾 |
| `POWERCONTEXT_SCOPE_ID` | `REPLACE_WITH_SCOPE_ID` | 换成 `--init-scope` 打印的 `scope_id` |
| `POWERCONTEXT_TOKEN` | 空 | 默认 Server 不填。开启鉴权后再填，并按下面「鉴权」改 HTTP 节点 |

Dify 若支持把变量标成 Secret，把 token 标成 Secret。提交材料里保持空字符串。

## 启动 PowerContext

官方快速开始使用 `uv`：

```bash
uv tool install --force "powercontext[cli,server] @ git+https://github.com/oceanbase/powercontext.git@master"
powercontext server run
```

另开一个终端：

```bash
curl --fail --silent --show-error http://127.0.0.1:8000/health/live
curl --fail --silent --show-error http://127.0.0.1:8000/health/ready
```

`/health/live` 返回 `{"status":"ok"}`。`/health/ready` 为 `ready` 或 `degraded` 时，记忆接口都可以用。本次演练的 ready 状态是 `ready`，推理模型未配置。

本次实际安装命令（与官方同一个 Git 源，装进虚拟环境）：

```bash
uv venv /tmp/pcvenv
uv pip install --python /tmp/pcvenv/bin/python \
  "powercontext[cli,server] @ git+https://github.com/oceanbase/powercontext.git@master"
POWERCONTEXT_HOME=/tmp/powercontext-data \
  /tmp/pcvenv/bin/powercontext server run --host 127.0.0.1 --port 8000
```

### 容器

`powercontext/docker-compose.yml` 使用官方文档里的本地标签 `powercontext-server:local`。它不会从仓库上拉取一个未核实的镜像名。构建步骤以 PowerContext 仓库的 `docker/README.md` 为准：

https://github.com/oceanbase/powercontext/blob/master/docker/README.md

端口发布在 `127.0.0.1:8000`。和脚本、浏览器在同一台机器上的 Dify 可以直接用这个地址。

Dify 若跑在另一个容器里，它访问不到宿主机的 `127.0.0.1`。把两个容器接到同一个 Docker 网络，把 `POWERCONTEXT_URL` 设为 `http://powercontext-server:8000`。需要把端口暴露到宿主机之外时，先按官方部署文档开启 Bearer，再放宽发布地址。

## 初始化 scope

在仓库根目录：

```bash
python3 dify/scripts/powercontext_contract.py --init-scope
```

脚本对 `POST /v1/scopes` 使用固定的 `idempotency_key`：`rust-anchor-traveler-demo`。同一个 key 再调用一次会返回同一个 `scope_id`（本次对本地 Server 观察到 HTTP 201 且 id 不变）。这条命令不写仇账。

把打印出的 id 填进 Dify 的 `POWERCONTEXT_SCOPE_ID`。

契约演练默认使用另一把 key：`rust-anchor-contract-sample`，避免把样例仇账写进准备给玩家的演示 scope。

## 导入 DSL

1. 打开 Dify 工作室，选择导入 DSL 文件。
2. 选择 `dify/dsl/rust-anchor-tavern-keeper.chatflow.yml`。这是唯一的应用文件，没有第二个导入步骤。
3. 版本提示若出现，确认导入。
4. 打开「老疤」节点，把模型从占位的 `gpt-4o-mini` 换成当前工作区已经安装的对话模型。提供商字符串对不上时，节点会标红，换模型后即可发布。
5. 在工作流的环境变量面板填写上一节的三个值。`POWERCONTEXT_URL` 不要带结尾斜杠，也不要带 `/v1`。
6. 确认三个 HTTP 节点仍是「无鉴权」。地址应分别为：
   - `{{#env.POWERCONTEXT_URL#}}/v1/memory/search`
   - `{{#env.POWERCONTEXT_URL#}}/v1/context/prepare`
   - `{{#env.POWERCONTEXT_URL#}}/v1/memory/remember`
7. 发布，打开 Web 对话。

条件分支「要不要记仇」判断 `解析记仇决定.should_remember` 等于 `yes`。导入后如果条件是空的，在界面里重新选这个字符串比较。

### 鉴权

默认回环安装不校验 Bearer，DSL 因此使用 `no-auth`。空的 API Key 配成 Bearer 时，Dify 的 HTTP 节点会直接失败（见 langgenius/dify 问题 21830）。

Server 开启鉴权之后，在三个 HTTP 节点里把鉴权改成 API Key / Bearer，把 token 填进 API Key。token 留在 Dify 的环境变量或本机 secret 里。

## 图里每个节点做什么

1. 开始：使用系统变量 `sys.query`。
2. 组装检索请求：生成 search 和 prepare 的 JSON。查询固定为 `仇账`，search 的 `mode` 为 `fts`，`limit` 为 10；prepare 的 `max_bytes` 为 4000。
3. 仇账检索：`POST /v1/memory/search`。
4. 整理仇账：只保留 `state` 为 `active` 的 `hits[].memory.text`。
5. 准备上下文：`POST /v1/context/prepare`。
6. 整理准备上下文：`status=ready` 时把 `content` 原样送进提示词；`empty` 且 `content=null` 按空历史处理。
7. 老疤：对话模型。会话窗口保留最近 6 轮，用来记住这一场对话；跨会话的仇账只来自 PowerContext。
8. 解析记仇决定：从模型输出里取 JSON，拼出 remember 请求。字段只有 `scope_id`、`kind`、`text`、`reason`。
9. 要不要记仇：`yes` 才继续。
10. 记入仇账：`POST /v1/memory/remember`。`kind` 为应用自定义的 `grudge` 或 `atonement`（OpenAPI 里 `kind` 是长度 1 到 128 的字符串）。
11. 回话：把对白交还玩家。

`kind`、正文长度 8192 字节、`reason` 最长 512、search `mode` 取值 `auto|fts|vector|hybrid`、prepare 的 `max_bytes` 范围 512 到 32768，都按该 Server 的 OpenAPI 填写。代码节点把正文限制在 8000 字节以内。请求不带旧的修订预检字段。

## 已知限制

- 全文检索按词匹配。本地 Server 上，单独的「盐」命中 0 条，而「盐罐」「炖菜」「仇账」可以命中。图不拿玩家原话当查询。
- 同一句「麦酒」既搜不到盐罐那笔账，`prepare` 也返回 `status: empty`。所以第二轮点酒仍能翻旧账，靠的是固定查询 `仇账`。
- 请求 `mode: fts` 时，这次 Server 的响应 `mode` 是 `text`。
- 页脚条数不含本轮刚写入的记录。
- 模型若没有输出 JSON，代码节点会让老疤说「没听清」，并且不写仇账。
- 同一个已发布应用共用环境变量里的那一个 scope。演示按一位旅人来验收。
- 本作品不部署 seekdb，也不把 PowerContext 当作 Dify 的系统库。

## 来源和改动

接口以运行中的 `/openapi.json` 为准，并对照过这些公开说明：

- PowerContext 接入选择：https://powercontext.oceanbase.io/zh/docs/develop/interfaces/
- API 快速开始：https://powercontext.oceanbase.io/zh/docs/develop/api-quickstart/
- HTTP API：https://powercontext.oceanbase.io/en/docs/develop/http-api/
- Dify HTTP 请求节点：https://docs.dify.ai/en/cloud/use-dify/nodes/http-request

DSL 的字段形状参照已经能导入的公开文件，没有把那些应用原样抄进来：

- HTTP 节点、DSL `0.3.0`、`advanced-chat` 的节点骨架：https://github.com/langgenius/dify/issues/21830
- `if-else` 分支和 HTTP `body.data` 列表：https://github.com/wwwzhouhui/dify-for-dsl/blob/main/dsl/69-dify案例分享-数学公式识别工作流.yml
- 娱乐向角色对话的玩法参考（恋爱模拟器等 Chatflow）：https://github.com/dzh-gitcode/dify-workflows/tree/main/14_娱乐游戏

相对这些示例，本作品换成了酒馆老板人设，并加入 PowerContext 的 search、prepare、remember 三个 HTTP 节点。容器片段只引用官方 `docker/README.md` 里的 `powercontext-server:local` 标签。
