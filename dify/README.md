# 记仇的酒馆老板

锈锚酒馆的老板老疤会把玩家的恶作剧写进 PowerContext。换一场新的 Dify 会话之后，他仍然翻得到那笔仇账，价钱和口气都会变。

这是 OceanBase 大赛 Dify 赛道「Just for Fun」的作品：Dify Chatflow 负责编排，PowerContext 负责跨会话记忆。没有使用 seekdb。

## 怎么玩

打开导入后的 Chatflow，对老疤说话。

- 第一次点麦酒，他当新客人招呼你，一杯一个铜子。
- 把盐罐换成糖、赖账、砸店、当众羞辱他，他会当场变脸，并把这件事记成仇账。
- 点「新对话」再去要酒。scope 不变。他会点名上一笔坏事，加价或者拒绝赊账。
- 当面道歉，并且拿出具体补偿（赔铜子、赔酒、干活），他会再记一笔赔罪，之后态度松一档，但旧账还能被拿来开玩笑。

页脚的「写入前仇账 N 条」是这一轮开口之前的旧账。恶作剧当轮会显示「本轮新记：是」，条数要到下一轮才增加。

## 技术分工

| 组件 | 作用 |
| --- | --- |
| Dify Chatflow | 接收玩家输入，检索旧账，调用对话模型，决定记不记新账，把回复返回给玩家 |
| PowerContext `POST /v1/memory/search` | 用全文检索读取当前 scope 里的仇账 |
| PowerContext `POST /v1/context/prepare` | 把同一笔仇账收成有界、标记为不可信历史的上下文，交给模型 |
| PowerContext `POST /v1/memory/remember` | 只在本轮确认为恶作剧或赔罪时写入一条 Atomic Memory |

一个 scope 对应一位旅人。演示用环境变量里的同一个 `scope_id`。换玩家就换 scope。scope 由运行脚本创建，不让模型填写。

最小 Server 走全文检索。玩家下一句如果只是「来一杯麦酒」，这句话里没有旧账里的词，直接拿它当查询会什么都召不回。所以图里的检索和准备上下文都固定查询 `仇账`，写入的正文也一律带上这个标记。这个行为在本仓库的契约演练里对过本地 Server，见 [VERIFY.md](VERIFY.md)。

## 目录

| 路径 | 用途 |
| --- | --- |
| `dsl/rust-anchor-tavern-keeper.chatflow.yml` | 唯一要导入的 Chatflow DSL |
| `RUN.md` | 版本、环境变量、启动和导入 |
| `VERIFY.md` | 完整验证样例，以及 PowerContext 读写的证明路径 |
| `scripts/check_dsl.py` | 不启动服务，检查 DSL 结构和代码节点 |
| `scripts/powercontext_contract.py` | 对真实 Server 做写入、检索、准备上下文 |
| `scripts/dsl_nodes.py` | 从 DSL 里取出代码节点，保证演练请求和导入后的图一致 |
| `evidence/powercontext-contract.json` | 2026-10-27 在本地 Server 上跑通契约的记录，不含 token |
| `powercontext/docker-compose.yml` | 指向官方镜像构建方式的本机编排片段 |
| `.env.example` | 占位变量，没有密钥 |

## 导入顺序

只有这一个 DSL，没有前置应用、知识库或插件包。导入步骤、模型占位符和环境变量写在 [RUN.md](RUN.md)。

## 提测

- 分支：`dify`
- commit：该分支的 tip。以 `git rev-parse HEAD` 为准，不要用 `main`
- 作品目录：`dify/`
